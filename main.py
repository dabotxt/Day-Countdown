import base64
import mimetypes
from pathlib import Path

import webview


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>倒计时 · 下午6点</title>
    <style>
        * { box-sizing: border-box; }

        :root {
            --app-bg: #10151f;
            --shell-bg:
                radial-gradient(circle at 22% 0%, rgba(84, 168, 255, 0.22), transparent 32%),
                radial-gradient(circle at 88% 14%, rgba(255, 178, 104, 0.18), transparent 34%),
                linear-gradient(145deg, #171e2b 0%, #10151f 58%, #0b1018 100%);
        }

        html,
        body {
            width: 100%;
            min-height: 100vh;
            margin: 0;
            overflow: hidden;
            font-family: "Segoe UI", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
            color: #f7fbff;
            background: var(--app-bg);
            user-select: none;
        }

        body {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px;
        }

        .bg-media-layer {
            position: fixed;
            inset: 0;
            z-index: 0;
            display: none;
            overflow: hidden;
            background: var(--app-bg);
        }

        .bg-media-layer.is-active {
            display: block;
        }

        .bg-media-layer img,
        .bg-media-layer video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .bg-media-layer::after {
            content: "";
            position: absolute;
            inset: 0;
            background: rgba(5, 8, 13, 0.38);
        }

        .shell {
            position: relative;
            z-index: 1;
            width: min(604px, calc(100vw - 16px));
            padding: 20px;
            border-radius: 18px;
            background: var(--shell-bg);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.46);
        }

        body.has-media-bg .shell {
            background:
                linear-gradient(145deg, rgba(23, 30, 43, 0.76), rgba(11, 16, 24, 0.62));
            backdrop-filter: blur(4px);
        }

        body.has-media-bg .salary-panel,
        body.has-media-bg .salary-stat,
        body.has-media-bg .salary-input-wrap {
            background: rgba(0, 0, 0, 0.34);
        }

        .topbar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 16px;
        }

        h1 {
            margin: 0 0 8px;
            font-size: 27px;
            font-weight: 650;
            line-height: 1.2;
            letter-spacing: 0;
        }

        .subtitle {
            margin: 0;
            color: rgba(247, 251, 255, 0.58);
            font-size: 14px;
            line-height: 1.5;
        }

        .status {
            min-width: 132px;
            padding-top: 4px;
            text-align: right;
            color: rgba(247, 251, 255, 0.54);
            font-size: 13px;
            line-height: 1.55;
            font-variant-numeric: tabular-nums;
        }

        .status strong {
            display: block;
            color: #f7fbff;
            font-size: 15px;
            font-weight: 650;
        }

        .top-actions {
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }

        .drag-handle {
            cursor: move;
        }

        .settings-button,
        .dialog-button {
            border: 0;
            border-radius: 8px;
            color: #f7fbff;
            font-family: inherit;
            font-weight: 650;
            cursor: pointer;
            -webkit-app-region: no-drag;
        }

        .settings-button {
            flex: 0 0 auto;
            min-width: 58px;
            height: 34px;
            padding: 0 12px;
            background: rgba(255, 255, 255, 0.09);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .settings-button:hover,
        .dialog-button:hover {
            background: rgba(255, 255, 255, 0.14);
        }

        .countdown-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 16px;
        }

        .flip-unit {
            min-width: 0;
        }

        .flip-card {
            position: relative;
            height: 98px;
            overflow: hidden;
            border-radius: 8px;
            background: linear-gradient(180deg, #273246 0%, #141b27 50%, #0e131c 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.12),
                inset 0 -1px 0 rgba(0, 0, 0, 0.45),
                0 16px 28px rgba(0, 0, 0, 0.32);
            perspective: 900px;
        }

        .flip-card::before {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            height: 1px;
            z-index: 3;
            background: rgba(0, 0, 0, 0.48);
            box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06);
        }

        .flip-card::after {
            content: "";
            position: absolute;
            inset: 0;
            z-index: 2;
            pointer-events: none;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 38%),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05), transparent 18%, transparent 82%, rgba(0, 0, 0, 0.26));
        }

        .flip-value {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
            color: #f9fbff;
            font-size: 50px;
            font-weight: 780;
            line-height: 1;
            letter-spacing: 0;
            font-variant-numeric: tabular-nums;
            text-shadow: 0 3px 18px rgba(83, 154, 255, 0.24);
            transform-origin: center bottom;
            backface-visibility: hidden;
        }

        .flip-card.is-flipping .flip-value {
            animation: flipDown 420ms cubic-bezier(.2, .78, .34, 1);
        }

        .label {
            margin-top: 6px;
            color: rgba(247, 251, 255, 0.46);
            font-size: 13px;
            text-align: center;
            letter-spacing: 0;
        }

        .salary-panel {
            padding: 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.045);
        }

        .salary-input-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.25);
        }

        .salary-input-wrap label,
        .salary-input-wrap span {
            flex: 0 0 auto;
            color: rgba(247, 251, 255, 0.62);
            font-size: 14px;
        }

        .salary-input-wrap input {
            width: 100%;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: #f7fbff;
            font: inherit;
            font-size: 18px;
            font-weight: 650;
            text-align: right;
            font-variant-numeric: tabular-nums;
            user-select: text;
        }

        .salary-input-wrap input::placeholder {
            color: rgba(247, 251, 255, 0.25);
        }

        .salary-stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 10px;
        }

        .salary-stat {
            min-width: 0;
            padding: 10px;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.22);
        }

        .salary-stat .salary-label {
            margin-bottom: 5px;
            color: rgba(247, 251, 255, 0.44);
            font-size: 13px;
        }

        .salary-stat .amount {
            color: #f7fbff;
            font-size: 22px;
            font-weight: 760;
            line-height: 1.15;
            word-break: break-all;
            font-variant-numeric: tabular-nums;
        }

        .salary-note {
            margin-top: 8px;
            color: rgba(247, 251, 255, 0.36);
            font-size: 12px;
            line-height: 1.5;
        }

        .modal-backdrop {
            position: fixed;
            inset: 0;
            z-index: 20;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 16px;
            background: rgba(5, 8, 13, 0.62);
        }

        .modal-backdrop.is-open {
            display: flex;
        }

        .settings-dialog {
            width: min(360px, calc(100vw - 32px));
            padding: 16px;
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 8px;
            background: rgba(18, 24, 34, 0.98);
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5);
            -webkit-app-region: no-drag;
        }

        .settings-dialog h2 {
            margin: 0 0 14px;
            font-size: 18px;
            line-height: 1.25;
            font-weight: 700;
        }

        .field-row {
            display: grid;
            grid-template-columns: 78px minmax(0, 1fr) 42px;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }

        .field-row label,
        .gradient-row label {
            color: rgba(247, 251, 255, 0.62);
            font-size: 14px;
        }

        .field-row input[type="text"] {
            width: 100%;
            min-width: 0;
            height: 34px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            outline: 0;
            padding: 0 10px;
            background: rgba(0, 0, 0, 0.24);
            color: #f7fbff;
            font: inherit;
            user-select: text;
        }

        .field-row input[type="color"] {
            width: 42px;
            height: 34px;
            border: 0;
            border-radius: 8px;
            padding: 0;
            background: transparent;
            cursor: pointer;
        }

        .field-row.is-disabled {
            opacity: 0.45;
        }

        .gradient-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 4px 0 12px;
        }

        .gradient-row input {
            width: 16px;
            height: 16px;
            margin: 0;
            cursor: pointer;
        }

        .media-row {
            display: grid;
            grid-template-columns: 78px minmax(0, 1fr) auto;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }

        .media-row label {
            color: rgba(247, 251, 255, 0.62);
            font-size: 14px;
        }

        .media-name {
            min-width: 0;
            overflow: hidden;
            color: rgba(247, 251, 255, 0.58);
            font-size: 13px;
            line-height: 34px;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .small-dialog-button {
            height: 34px;
            border: 0;
            border-radius: 8px;
            padding: 0 10px;
            background: rgba(255, 255, 255, 0.09);
            color: #f7fbff;
            font-family: inherit;
            font-weight: 650;
            cursor: pointer;
            -webkit-app-region: no-drag;
        }

        .small-dialog-button:hover {
            background: rgba(255, 255, 255, 0.14);
        }

        .dialog-error {
            min-height: 18px;
            margin-bottom: 10px;
            color: #ffb4a8;
            font-size: 12px;
            line-height: 1.4;
        }

        .dialog-actions {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }

        .dialog-button {
            height: 36px;
            padding: 0 10px;
            background: rgba(255, 255, 255, 0.09);
        }

        .dialog-button.primary {
            background: #4f8cff;
        }

        .dialog-button.primary:hover {
            background: #659aff;
        }

        @keyframes flipDown {
            0% {
                opacity: 1;
                transform: rotateX(0deg);
            }
            45% {
                opacity: 0.35;
                transform: rotateX(-86deg);
            }
            52% {
                opacity: 0.35;
                transform: rotateX(76deg);
            }
            100% {
                opacity: 1;
                transform: rotateX(0deg);
            }
        }

        @media (max-width: 540px) {
            body { padding: 12px; }
            .shell {
                width: calc(100vw - 24px);
                padding: 24px 18px 20px;
                border-radius: 22px;
            }
            .topbar {
                display: block;
                margin-bottom: 22px;
            }
            .status {
                min-width: 0;
                margin-top: 10px;
                text-align: left;
            }
            .countdown-grid {
                gap: 8px;
            }
            .flip-card {
                height: 82px;
            }
            .flip-value {
                font-size: 38px;
            }
            .label {
                font-size: 12px;
            }
            .salary-stats {
                grid-template-columns: 1fr;
            }
        }

        body.compact {
            padding: 4px;
        }

        body.compact .shell {
            width: 232px;
            padding: 6px;
            border-radius: 8px;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.38);
        }

        body.compact .topbar,
        body.compact .salary-panel {
            display: none;
        }

        body.compact .countdown-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 4px;
            margin: 0;
        }

        body.compact .flip-card {
            height: 45px;
            border-radius: 6px;
        }

        body.compact .flip-value {
            font-size: 24px;
        }

        body.compact .label {
            margin-top: 3px;
            font-size: 9px;
        }
    </style>
</head>
<body>
    <div class="bg-media-layer" id="bgMediaLayer" aria-hidden="true">
        <img id="bgMediaImage" alt="" />
        <video id="bgMediaVideo" muted loop playsinline></video>
    </div>

    <main class="shell">
        <section class="topbar">
            <div class="drag-handle pywebview-drag-region">
                <h1>今日倒计时</h1>
                <p class="subtitle">距离下午 6:00 还有</p>
            </div>
            <div class="top-actions">
                <button class="settings-button" id="openBgSettings" type="button">背景</button>
                <div class="status">
                    <span id="targetDisplay">今天 18:00</span>
                    <strong id="currentTimeDisplay">--:--:--</strong>
                </div>
            </div>
        </section>

        <section class="countdown-grid" aria-label="倒计时">
            <div class="flip-unit">
                <div class="flip-card" data-unit="hours"><span class="flip-value" id="hours">00</span></div>
                <div class="label">小时</div>
            </div>
            <div class="flip-unit">
                <div class="flip-card" data-unit="minutes"><span class="flip-value" id="minutes">00</span></div>
                <div class="label">分钟</div>
            </div>
            <div class="flip-unit">
                <div class="flip-card" data-unit="seconds"><span class="flip-value" id="seconds">00</span></div>
                <div class="label">秒</div>
            </div>
        </section>

        <section class="salary-panel">
            <div class="salary-input-wrap">
                <label for="monthlySalary">月薪</label>
                <span>¥</span>
                <input id="monthlySalary" type="number" min="0" step="100" inputmode="decimal" placeholder="输入月薪" autocomplete="off" />
            </div>
            <div class="salary-stats">
                <div class="salary-stat">
                    <div class="salary-label">本周期已经挣到</div>
                    <div class="amount" id="monthEarned">¥0.00</div>
                </div>
                <div class="salary-stat">
                    <div class="salary-label">今日已经挣到</div>
                    <div class="amount" id="todayEarned">¥0.00</div>
                </div>
            </div>
            <div class="salary-note" id="salaryNote">按每月 15 日薪资周期、工作日 9:00-18:00 估算。</div>
        </section>
    </main>

    <div class="modal-backdrop" id="bgSettingsModal" aria-hidden="true">
        <section class="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="bgSettingsTitle">
            <h2 id="bgSettingsTitle">背景颜色</h2>
            <div class="field-row">
                <label for="bgColorInput">颜色</label>
                <input id="bgColorInput" type="text" spellcheck="false" autocomplete="off" placeholder="#10151f" />
                <input id="bgColorPicker" type="color" value="#10151f" aria-label="选择背景颜色" />
            </div>
            <div class="field-row" id="gradientColorRow">
                <label for="bgGradientInput">渐变色</label>
                <input id="bgGradientInput" type="text" spellcheck="false" autocomplete="off" placeholder="#24364f" />
                <input id="bgGradientPicker" type="color" value="#24364f" aria-label="选择渐变颜色" />
            </div>
            <div class="gradient-row">
                <input id="gradientEnabled" type="checkbox" />
                <label for="gradientEnabled">使用渐变</label>
            </div>
            <div class="media-row">
                <label>照片/视频</label>
                <div class="media-name" id="bgMediaName">未选择</div>
                <button class="small-dialog-button" id="chooseBgMedia" type="button">选择</button>
            </div>
            <div class="media-row">
                <label></label>
                <div class="media-name">图片会内嵌保存，视频使用本地路径</div>
                <button class="small-dialog-button" id="clearBgMedia" type="button">清除</button>
            </div>
            <div class="dialog-error" id="bgSettingsError"></div>
            <div class="dialog-actions">
                <button class="dialog-button" id="randomBgButton" type="button">随机</button>
                <button class="dialog-button" id="closeBgSettings" type="button">取消</button>
                <button class="dialog-button primary" id="applyBgSettings" type="button">应用</button>
            </div>
        </section>
    </div>

    <script>
        (function() {
            var fields = {
                hours: document.getElementById('hours'),
                minutes: document.getElementById('minutes'),
                seconds: document.getElementById('seconds')
            };
            var currentTimeDisplay = document.getElementById('currentTimeDisplay');
            var targetDisplay = document.getElementById('targetDisplay');
            var monthlySalaryInput = document.getElementById('monthlySalary');
            var monthEarnedEl = document.getElementById('monthEarned');
            var todayEarnedEl = document.getElementById('todayEarned');
            var salaryNote = document.getElementById('salaryNote');
            var openBgSettings = document.getElementById('openBgSettings');
            var bgSettingsModal = document.getElementById('bgSettingsModal');
            var bgColorInput = document.getElementById('bgColorInput');
            var bgColorPicker = document.getElementById('bgColorPicker');
            var bgGradientInput = document.getElementById('bgGradientInput');
            var bgGradientPicker = document.getElementById('bgGradientPicker');
            var gradientColorRow = document.getElementById('gradientColorRow');
            var gradientEnabled = document.getElementById('gradientEnabled');
            var bgSettingsError = document.getElementById('bgSettingsError');
            var randomBgButton = document.getElementById('randomBgButton');
            var closeBgSettings = document.getElementById('closeBgSettings');
            var applyBgSettings = document.getElementById('applyBgSettings');
            var bgMediaLayer = document.getElementById('bgMediaLayer');
            var bgMediaImage = document.getElementById('bgMediaImage');
            var bgMediaVideo = document.getElementById('bgMediaVideo');
            var bgMediaName = document.getElementById('bgMediaName');
            var chooseBgMedia = document.getElementById('chooseBgMedia');
            var clearBgMedia = document.getElementById('clearBgMedia');

            var TARGET_HOUR = 18;
            var TARGET_MINUTE = 0;
            var TARGET_SECOND = 0;
            var WORK_START_HOUR = 9;
            var WORK_END_HOUR = 18;
            var SALARY_STORAGE_KEY = 'countdown_monthly_salary';
            var BG_STORAGE_KEY = 'countdown_background_settings';
            var DEFAULT_BG_SETTINGS = {
                color: '#10151f',
                gradientColor: '#24364f',
                gradient: false,
                mediaUrl: '',
                mediaType: '',
                mediaName: ''
            };
            var bgSettings = {
                color: DEFAULT_BG_SETTINGS.color,
                gradientColor: DEFAULT_BG_SETTINGS.gradientColor,
                gradient: DEFAULT_BG_SETTINGS.gradient,
                mediaUrl: DEFAULT_BG_SETTINGS.mediaUrl,
                mediaType: DEFAULT_BG_SETTINGS.mediaType,
                mediaName: DEFAULT_BG_SETTINGS.mediaName
            };
            var draftMedia = {
                url: '',
                type: '',
                name: ''
            };
            var previousValues = {};
            var lastSalarySecond = -1;
            var isCompact = false;
            var pendingCompactSync = false;
            var raf = window.requestAnimationFrame ||
                window.webkitRequestAnimationFrame ||
                function(callback) { return window.setTimeout(callback, 50); };

            function addEvent(target, name, handler) {
                if (target.addEventListener) target.addEventListener(name, handler, false);
                else if (target.attachEvent) target.attachEvent('on' + name, handler);
            }

            function stopEvent(event) {
                event = event || window.event;
                if (event.stopPropagation) event.stopPropagation();
                event.cancelBubble = true;
            }

            function addBodyClass(name) {
                if ((' ' + document.body.className + ' ').indexOf(' ' + name + ' ') < 0) {
                    document.body.className = (document.body.className + ' ' + name).replace(/^\\s+|\\s+$/g, '');
                }
            }

            function removeBodyClass(name) {
                document.body.className = (' ' + document.body.className + ' ')
                    .replace(new RegExp(' ' + name + ' ', 'g'), ' ')
                    .replace(/^\\s+|\\s+$/g, '');
            }

            function syncCompactWindow() {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.set_compact) {
                    pendingCompactSync = false;
                    window.pywebview.api.set_compact(isCompact);
                } else {
                    pendingCompactSync = true;
                }
            }

            function setCompactMode(nextCompact) {
                isCompact = !!nextCompact;
                if (isCompact) addBodyClass('compact');
                else removeBodyClass('compact');
                syncCompactWindow();
            }

            function toggleCompactMode() {
                setCompactMode(!isCompact);
            }

            function padZero(num, length) {
                length = length || 2;
                var text = String(num);
                while (text.length < length) text = '0' + text;
                return text;
            }

            function formatTime(h, m, s) {
                return padZero(h) + ':' + padZero(m) + ':' + padZero(s);
            }

            function formatMoney(amount) {
                return '¥' + Number(amount).toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
            }

            function normalizeHexColor(value) {
                var text = String(value || '').replace(/^\\s+|\\s+$/g, '');
                if (text.charAt(0) !== '#') text = '#' + text;
                if (/^#[0-9a-fA-F]{3}$/.test(text)) {
                    text = '#' + text.charAt(1) + text.charAt(1) + text.charAt(2) + text.charAt(2) + text.charAt(3) + text.charAt(3);
                }
                if (!/^#[0-9a-fA-F]{6}$/.test(text)) return '';
                return text.toLowerCase();
            }

            function hexToRgb(hex) {
                var normalized = normalizeHexColor(hex);
                if (!normalized) return { r: 16, g: 21, b: 31 };
                return {
                    r: parseInt(normalized.substr(1, 2), 16),
                    g: parseInt(normalized.substr(3, 2), 16),
                    b: parseInt(normalized.substr(5, 2), 16)
                };
            }

            function mixColor(hex, ratio) {
                var rgb = hexToRgb(hex);
                var clamp = function(value) {
                    return Math.max(0, Math.min(255, Math.round(value)));
                };
                var toHex = function(value) {
                    var text = clamp(value).toString(16);
                    return text.length === 1 ? '0' + text : text;
                };
                return '#' + toHex(rgb.r * ratio) + toHex(rgb.g * ratio) + toHex(rgb.b * ratio);
            }

            function randomHexColor() {
                var value = Math.floor(Math.random() * 0xffffff).toString(16);
                while (value.length < 6) value = '0' + value;
                return '#' + value;
            }

            function setGradientRowEnabled(enabled) {
                gradientColorRow.className = enabled ? 'field-row' : 'field-row is-disabled';
                bgGradientInput.disabled = !enabled;
                bgGradientPicker.disabled = !enabled;
            }

            function applyBackgroundSettings(settings) {
                var color = normalizeHexColor(settings.color) || DEFAULT_BG_SETTINGS.color;
                var gradientColor = normalizeHexColor(settings.gradientColor) || DEFAULT_BG_SETTINGS.gradientColor;
                var mediaType = settings.mediaType === 'video' || settings.mediaType === 'image' ? settings.mediaType : '';
                var mediaUrl = mediaType ? String(settings.mediaUrl || '') : '';
                var root = document.documentElement.style;
                var lowerColor = mixColor(color, 0.58);
                var lowerGradient = mixColor(gradientColor, 0.58);
                var shellBg = settings.gradient
                    ? 'radial-gradient(circle at 18% 0%, ' + gradientColor + '44, transparent 34%), radial-gradient(circle at 88% 14%, ' + color + '33, transparent 34%), linear-gradient(145deg, ' + gradientColor + ' 0%, ' + color + ' 56%, ' + lowerColor + ' 100%)'
                    : 'radial-gradient(circle at 22% 0%, rgba(255, 255, 255, 0.11), transparent 32%), linear-gradient(145deg, ' + color + ' 0%, ' + color + ' 54%, ' + lowerColor + ' 100%)';

                bgSettings = {
                    color: color,
                    gradientColor: gradientColor,
                    gradient: !!settings.gradient,
                    mediaUrl: mediaUrl,
                    mediaType: mediaType,
                    mediaName: mediaUrl ? String(settings.mediaName || '自定义背景') : ''
                };
                root.setProperty('--app-bg', bgSettings.gradient
                    ? 'linear-gradient(135deg, ' + lowerColor + ', ' + lowerGradient + ')'
                    : color);
                root.setProperty('--shell-bg', shellBg);
                renderBackgroundMedia();
            }

            function renderBackgroundMedia() {
                bgMediaImage.onload = null;
                bgMediaImage.onerror = null;
                bgMediaVideo.oncanplay = null;
                bgMediaVideo.onerror = null;
                bgMediaImage.style.display = 'none';
                bgMediaVideo.style.display = 'none';
                bgMediaImage.removeAttribute('src');
                bgMediaVideo.pause();
                bgMediaVideo.removeAttribute('src');
                bgMediaVideo.load();

                if (!bgSettings.mediaUrl) {
                    bgMediaLayer.className = 'bg-media-layer';
                    removeBodyClass('has-media-bg');
                    bgMediaName.innerText = '未选择';
                    return;
                }

                bgMediaLayer.className = 'bg-media-layer is-active';
                addBodyClass('has-media-bg');
                bgMediaName.innerText = bgSettings.mediaName || '自定义背景';
                if (bgSettings.mediaType === 'video') {
                    bgMediaVideo.onerror = function() {
                        bgSettingsError.innerText = '视频背景加载失败，请换一个文件。';
                    };
                    bgMediaVideo.style.display = 'block';
                    bgMediaVideo.src = bgSettings.mediaUrl;
                    bgMediaVideo.play().catch(function() {});
                } else {
                    bgMediaImage.onerror = function() {
                        bgSettingsError.innerText = '图片背景加载失败，请换一个文件。';
                    };
                    bgMediaImage.style.display = 'block';
                    bgMediaImage.src = bgSettings.mediaUrl;
                }
            }

            function saveBackgroundSettings() {
                try {
                    localStorage.setItem(BG_STORAGE_KEY, JSON.stringify(bgSettings));
                } catch (err) {}
            }

            function syncBackgroundForm() {
                bgColorInput.value = bgSettings.color;
                bgColorPicker.value = bgSettings.color;
                bgGradientInput.value = bgSettings.gradientColor;
                bgGradientPicker.value = bgSettings.gradientColor;
                gradientEnabled.checked = !!bgSettings.gradient;
                draftMedia.url = bgSettings.mediaUrl;
                draftMedia.type = bgSettings.mediaType;
                draftMedia.name = bgSettings.mediaName;
                bgMediaName.innerText = draftMedia.name || '未选择';
                bgSettingsError.innerText = '';
                setGradientRowEnabled(bgSettings.gradient);
            }

            function openBackgroundDialog() {
                syncBackgroundForm();
                bgSettingsModal.className = 'modal-backdrop is-open';
                bgSettingsModal.setAttribute('aria-hidden', 'false');
                bgColorInput.focus();
            }

            function closeBackgroundDialog() {
                bgSettingsModal.className = 'modal-backdrop';
                bgSettingsModal.setAttribute('aria-hidden', 'true');
                bgSettingsError.innerText = '';
            }

            function collectBackgroundForm() {
                var color = normalizeHexColor(bgColorInput.value);
                var gradientColor = normalizeHexColor(bgGradientInput.value);
                if (!color) {
                    bgSettingsError.innerText = '请输入有效颜色，例如 #10151f 或 10151f。';
                    bgColorInput.focus();
                    return null;
                }
                if (gradientEnabled.checked && !gradientColor) {
                    bgSettingsError.innerText = '请输入有效渐变色，例如 #24364f。';
                    bgGradientInput.focus();
                    return null;
                }
                return {
                    color: color,
                    gradientColor: gradientColor || bgSettings.gradientColor,
                    gradient: gradientEnabled.checked,
                    mediaUrl: draftMedia.url,
                    mediaType: draftMedia.type,
                    mediaName: draftMedia.name
                };
            }

            function isWorkday(date) {
                var day = date.getDay();
                return day !== 0 && day !== 6;
            }

            function getSalaryCycle(now) {
                var start;
                var end;
                if (now.getDate() >= 15) {
                    start = new Date(now.getFullYear(), now.getMonth(), 15);
                    end = new Date(now.getFullYear(), now.getMonth() + 1, 15);
                } else {
                    start = new Date(now.getFullYear(), now.getMonth() - 1, 15);
                    end = new Date(now.getFullYear(), now.getMonth(), 15);
                }
                return { start: start, end: end };
            }

            function getWorkdaysInRange(startDate, endDate) {
                var count = 0;
                var date = new Date(startDate.getTime());
                while (date.getTime() < endDate.getTime()) {
                    if (isWorkday(date)) count += 1;
                    date.setDate(date.getDate() + 1);
                }
                return count;
            }

            function getCompletedWorkdaysBefore(date, cycleStart) {
                var count = 0;
                var cursor = new Date(cycleStart.getTime());
                var today = new Date(date.getFullYear(), date.getMonth(), date.getDate());
                while (cursor.getTime() < today.getTime()) {
                    if (isWorkday(cursor)) count += 1;
                    cursor.setDate(cursor.getDate() + 1);
                }
                return count;
            }

            function formatDate(date) {
                return padZero(date.getMonth() + 1) + '/' + padZero(date.getDate());
            }

            function getTodayWorkProgress(now) {
                var start;
                var end;
                if (!isWorkday(now)) return 0;
                start = new Date(now.getTime());
                start.setHours(WORK_START_HOUR, 0, 0, 0);
                end = new Date(now.getTime());
                end.setHours(WORK_END_HOUR, 0, 0, 0);
                if (now.getTime() <= start.getTime()) return 0;
                if (now.getTime() >= end.getTime()) return 1;
                return (now.getTime() - start.getTime()) / (end.getTime() - start.getTime());
            }

            function getNextTargetDate(now) {
                var target = new Date(now.getTime());
                target.setHours(TARGET_HOUR, TARGET_MINUTE, TARGET_SECOND, 0);
                if (now.getTime() >= target.getTime()) {
                    target.setDate(target.getDate() + 1);
                }
                return target;
            }

            function setFlipValue(unit, value) {
                var el = fields[unit];
                var card;
                if (!el || previousValues[unit] === value) return;
                card = el.parentNode;
                el.innerText = value;
                previousValues[unit] = value;
                card.className = card.className.replace(/\\bis-flipping\\b/g, '').replace(/\\s+/g, ' ');
                card.offsetWidth;
                card.className += ' is-flipping';
            }

            function updateSalary(now) {
                var monthlySalary = Number(monthlySalaryInput.value);
                var cycle;
                var workdaysInCycle;
                var dailySalary;
                var todayProgress;
                var todayEarned;
                var completed;
                var cycleEarned;

                if (!isFinite(monthlySalary) || monthlySalary <= 0) {
                    monthEarnedEl.innerText = formatMoney(0);
                    todayEarnedEl.innerText = formatMoney(0);
                    salaryNote.innerText = '输入月薪后，按每月 15 日薪资周期和工作日 9:00-18:00 估算。';
                    return;
                }

                cycle = getSalaryCycle(now);
                workdaysInCycle = getWorkdaysInRange(cycle.start, cycle.end);
                dailySalary = monthlySalary / workdaysInCycle;
                todayProgress = getTodayWorkProgress(now);
                todayEarned = dailySalary * todayProgress;
                completed = getCompletedWorkdaysBefore(now, cycle.start);
                cycleEarned = dailySalary * (completed + todayProgress);

                monthEarnedEl.innerText = formatMoney(cycleEarned);
                todayEarnedEl.innerText = formatMoney(todayEarned);
                salaryNote.innerText = isWorkday(now)
                    ? formatDate(cycle.start) + '-' + formatDate(cycle.end) + ' 共 ' + workdaysInCycle + ' 个工作日，日均 ' + formatMoney(dailySalary) + '，今日进度 ' + (todayProgress * 100).toFixed(1) + '%。'
                    : formatDate(cycle.start) + '-' + formatDate(cycle.end) + ' 共 ' + workdaysInCycle + ' 个工作日，日均 ' + formatMoney(dailySalary) + '，今天是休息日。';
            }

            function updateCountdown(now) {
                var target = getNextTargetDate(now);
                var diffMs = Math.max(0, target.getTime() - now.getTime());
                var totalSeconds = Math.floor(diffMs / 1000);
                var values = {
                    hours: padZero(Math.floor(totalSeconds / 3600)),
                    minutes: padZero(Math.floor((totalSeconds % 3600) / 60)),
                    seconds: padZero(totalSeconds % 60)
                };
                var isToday = target.toDateString() === now.toDateString();

                setFlipValue('hours', values.hours);
                setFlipValue('minutes', values.minutes);
                setFlipValue('seconds', values.seconds);

                targetDisplay.innerText = (isToday ? '今天' : '明天') + ' 18:00';
                currentTimeDisplay.innerText = formatTime(now.getHours(), now.getMinutes(), now.getSeconds());

                if (now.getSeconds() !== lastSalarySecond) {
                    lastSalarySecond = now.getSeconds();
                    updateSalary(now);
                }
            }

            function tick() {
                updateCountdown(new Date());
                raf(tick);
            }

            try {
                var savedBg = localStorage.getItem(BG_STORAGE_KEY);
                var parsedBg = savedBg ? JSON.parse(savedBg) : null;
                if (parsedBg) {
                    bgSettings.color = normalizeHexColor(parsedBg.color) || DEFAULT_BG_SETTINGS.color;
                    bgSettings.gradientColor = normalizeHexColor(parsedBg.gradientColor) || DEFAULT_BG_SETTINGS.gradientColor;
                    bgSettings.gradient = !!parsedBg.gradient;
                    bgSettings.mediaUrl = String(parsedBg.mediaUrl || '');
                    bgSettings.mediaType = parsedBg.mediaType === 'video' || parsedBg.mediaType === 'image' ? parsedBg.mediaType : '';
                    bgSettings.mediaName = String(parsedBg.mediaName || '');
                }
            } catch (err) {}

            applyBackgroundSettings(bgSettings);

            try {
                var saved = localStorage.getItem(SALARY_STORAGE_KEY);
                if (saved) monthlySalaryInput.value = saved;
            } catch (err) {}

            monthlySalaryInput.oninput = function() {
                try {
                    localStorage.setItem(SALARY_STORAGE_KEY, this.value);
                } catch (err) {}
                updateSalary(new Date());
            };

            bgColorInput.oninput = function() {
                var color = normalizeHexColor(this.value);
                if (color) bgColorPicker.value = color;
                bgSettingsError.innerText = '';
            };

            bgColorPicker.oninput = function() {
                bgColorInput.value = this.value;
                bgSettingsError.innerText = '';
            };

            bgGradientInput.oninput = function() {
                var color = normalizeHexColor(this.value);
                if (color) bgGradientPicker.value = color;
                bgSettingsError.innerText = '';
            };

            bgGradientPicker.oninput = function() {
                bgGradientInput.value = this.value;
                bgSettingsError.innerText = '';
            };

            gradientEnabled.onchange = function() {
                setGradientRowEnabled(this.checked);
                bgSettingsError.innerText = '';
            };

            chooseBgMedia.onclick = function(event) {
                stopEvent(event);
                bgSettingsError.innerText = '';
                if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.select_background_media) {
                    bgSettingsError.innerText = '当前环境暂不支持选择本地文件。';
                    return;
                }
                window.pywebview.api.select_background_media().then(function(result) {
                    if (!result) return;
                    if (result.error) {
                        bgSettingsError.innerText = result.error;
                        return;
                    }
                    draftMedia.url = result.url || '';
                    draftMedia.type = result.type || '';
                    draftMedia.name = result.name || '自定义背景';
                    bgMediaName.innerText = draftMedia.name;
                }).catch(function() {
                    bgSettingsError.innerText = '选择文件失败，请重新选择。';
                });
            };

            clearBgMedia.onclick = function(event) {
                stopEvent(event);
                draftMedia.url = '';
                draftMedia.type = '';
                draftMedia.name = '';
                bgMediaName.innerText = '未选择';
                bgSettingsError.innerText = '';
            };

            openBgSettings.onclick = function(event) {
                stopEvent(event);
                openBackgroundDialog();
            };

            closeBgSettings.onclick = function(event) {
                stopEvent(event);
                closeBackgroundDialog();
            };

            randomBgButton.onclick = function(event) {
                var color = randomHexColor();
                var gradientColor = randomHexColor();
                stopEvent(event);
                bgColorInput.value = color;
                bgColorPicker.value = color;
                bgGradientInput.value = gradientColor;
                bgGradientPicker.value = gradientColor;
                if (!gradientEnabled.checked) {
                    gradientEnabled.checked = true;
                    setGradientRowEnabled(true);
                }
                bgSettingsError.innerText = '';
            };

            applyBgSettings.onclick = function(event) {
                var nextSettings;
                stopEvent(event);
                nextSettings = collectBackgroundForm();
                if (!nextSettings) return;
                applyBackgroundSettings(nextSettings);
                saveBackgroundSettings();
                closeBackgroundDialog();
            };

            addEvent(bgSettingsModal, 'click', function(event) {
                event = event || window.event;
                if (event.target === bgSettingsModal) closeBackgroundDialog();
            });

            addEvent(bgSettingsModal, 'dblclick', stopEvent);

            addEvent(document, 'keydown', function(event) {
                event = event || window.event;
                if (event.keyCode === 27 && bgSettingsModal.className.indexOf('is-open') >= 0) {
                    closeBackgroundDialog();
                    return;
                }
                if (event.ctrlKey && event.keyCode === 87) {
                    if (event.preventDefault) event.preventDefault();
                    event.returnValue = false;
                    toggleCompactMode();
                    return false;
                }
            });

            addEvent(document, 'dblclick', function() {
                if (isCompact) setCompactMode(false);
            });

            addEvent(window, 'pywebviewready', function() {
                if (pendingCompactSync) syncCompactWindow();
            });

            tick();
        })();
    </script>
</body>
</html>"""


class TimerApi:
    def __init__(self):
        self.window = None
        self.compact = False

    def bind(self, window):
        self.window = window

    def set_compact(self, compact):
        self.compact = bool(compact)
        if self.window:
            if self.compact:
                self.window.resize(240, 80)
                self.window.set_title('倒计时 · 迷你')
            else:
                self.window.resize(620, 420)
                self.window.set_title('倒计时')
        return self.compact

    def select_background_media(self):
        if not self.window:
            return {'error': '窗口尚未准备好。'}

        file_types = (
            '图片和视频 (*.jpg;*.jpeg;*.png;*.gif;*.webp;*.bmp;*.mp4;*.mov;*.m4v;*.webm)',
            '图片 (*.jpg;*.jpeg;*.png;*.gif;*.webp;*.bmp)',
            '视频 (*.mp4;*.mov;*.m4v;*.webm)',
        )
        paths = self.window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=file_types,
        )
        if not paths:
            return None

        path = Path(paths[0]).expanduser().resolve()
        suffix = path.suffix.lower()
        image_suffixes = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        video_suffixes = {'.mp4', '.mov', '.m4v', '.webm'}

        if not path.exists():
            return {'error': '文件不存在，请重新选择。'}

        if suffix in image_suffixes:
            mime_type = mimetypes.guess_type(path.name)[0] or 'image/jpeg'
            try:
                data = base64.b64encode(path.read_bytes()).decode('ascii')
            except OSError:
                return {'error': '图片读取失败，请重新选择。'}
            return {
                'url': f'data:{mime_type};base64,{data}',
                'type': 'image',
                'name': path.name,
            }

        if suffix in video_suffixes:
            return {
                'url': path.as_uri(),
                'type': 'video',
                'name': path.name,
            }

        return {'error': '请选择支持的图片或视频文件。'}



def main():
    api = TimerApi()
    window = webview.create_window(
        title='倒计时',
        html=HTML,
        js_api=api,
        width=620,
        height=420,
        resizable=False,
        fullscreen=False,
        min_size=(220, 70),
        confirm_close=False,
        text_select=False,
        easy_drag=False,
        frameless=True,
        shadow=False,
        on_top=True,
        background_color='#10151f'
    )
    api.bind(window)
    webview.start(
        debug=False,
        private_mode=False,
        gui=None
    )


if __name__ == '__main__':
    main()
