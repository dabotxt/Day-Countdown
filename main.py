import inspect
import base64
import datetime
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import webview


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>倒计时 · 下午6点</title>
    <style>
        * { box-sizing: border-box; }

        html,
        body {
            width: 100%;
            min-height: 100vh;
            margin: 0;
            overflow: hidden;
            font-family: "Segoe UI", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
            color: #f7fbff;
            background: transparent;
            user-select: none;
        }

        body {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
        }

        .shell {
            position: relative;
            width: 100vw;
            min-height: 100vh;
            padding: 20px;
            border-radius: 26px;
            overflow: hidden;
            background:
                radial-gradient(circle at 22% 0%, rgba(84, 168, 255, 0.22), transparent 32%),
                radial-gradient(circle at 88% 14%, rgba(255, 178, 104, 0.18), transparent 34%),
                linear-gradient(145deg, #171e2b 0%, #10151f 58%, #0b1018 100%);
            box-shadow: none;
        }

        .shell > :not(.bg-media-layer) {
            position: relative;
            z-index: 1;
        }

        .bg-media-layer {
            position: absolute;
            inset: 0;
            z-index: 0;
            display: none;
            overflow: hidden;
            border-radius: inherit;
            background: transparent;
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
            background: rgba(255, 255, 255, 0.18);
            pointer-events: none;
        }

        .topbar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 16px;
        }

        .top-actions {
            display: flex;
            justify-content: flex-end;
            gap: 6px;
            margin-bottom: 8px;
        }

        .tool-button {
            min-width: 48px;
            height: 28px;
            border: 0;
            border-radius: 999px;
            padding: 0 10px;
            color: #f7fbff;
            background: rgba(255, 255, 255, 0.12);
            font: inherit;
            font-size: 12px;
            cursor: pointer;
        }

        .tool-button:hover {
            background: rgba(255, 255, 255, 0.18);
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
            border-radius: 18px;
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
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.045);
        }

        .salary-input-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            border-radius: 14px;
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
            border-radius: 14px;
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

        .settings-panel {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 12px;
            padding: 10px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.045);
        }

        .setting-field {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
            padding: 8px 10px;
            border-radius: 14px;
            background: rgba(0, 0, 0, 0.2);
        }

        .setting-field label {
            flex: 0 0 auto;
            color: rgba(247, 251, 255, 0.58);
            font-size: 13px;
        }

        .setting-field input,
        .setting-field select {
            width: 100%;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: #f7fbff;
            font: inherit;
            font-size: 15px;
            font-weight: 650;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        .setting-field select {
            cursor: pointer;
        }

        .setting-field select option {
            color: #20242c;
        }

        .setting-field input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: currentColor;
        }

        .setting-field input[type="color"] {
            width: 34px;
            height: 24px;
            flex: 0 0 auto;
            border: 0;
            padding: 0;
            background: transparent;
            cursor: pointer;
        }

        .background-settings {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 10px;
        }

        .background-file-name {
            grid-column: 1 / -1;
            margin: -2px 2px 0;
            overflow: hidden;
            color: currentColor;
            opacity: 0.48;
            font-size: 12px;
            line-height: 1.4;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .mini-button {
            height: 34px;
            border: 0;
            border-radius: 999px;
            padding: 0 12px;
            color: currentColor;
            background: rgba(255, 255, 255, 0.52);
            font: inherit;
            font-size: 13px;
            cursor: pointer;
        }

        .shutdown-settings {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .shutdown-description {
            grid-column: 1 / -1;
            align-items: flex-start;
        }

        .setting-field textarea {
            width: 100%;
            min-height: 42px;
            max-height: 72px;
            min-width: 0;
            border: 0;
            outline: 0;
            resize: none;
            background: transparent;
            color: #f7fbff;
            font: inherit;
            font-size: 14px;
            line-height: 1.45;
            text-align: right;
            user-select: text;
        }

        .setting-field textarea::placeholder {
            color: rgba(247, 251, 255, 0.28);
        }

        .shutdown-status {
            grid-column: 1 / -1;
            margin: -2px 2px 0;
            color: currentColor;
            opacity: 0.54;
            font-size: 12px;
            line-height: 1.4;
        }

        .shutdown-modal {
            position: fixed;
            inset: 0;
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 20;
            padding: 18px;
            background: rgba(15, 20, 30, 0.36);
            backdrop-filter: blur(10px);
        }

        .shutdown-modal.is-open {
            display: flex;
        }

        .shutdown-dialog {
            width: min(420px, 100%);
            padding: 22px;
            border-radius: 26px;
            color: #263244;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(239, 246, 255, 0.94));
            box-shadow: 0 26px 70px rgba(0, 0, 0, 0.28);
        }

        .shutdown-dialog h2 {
            margin: 0 0 8px;
            font-size: 22px;
            line-height: 1.25;
            letter-spacing: 0;
        }

        .shutdown-desc {
            min-height: 44px;
            margin: 0 0 14px;
            color: rgba(38, 50, 68, 0.68);
            font-size: 14px;
            line-height: 1.55;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .shutdown-count {
            display: flex;
            align-items: baseline;
            justify-content: center;
            gap: 6px;
            margin: 14px 0 18px;
            font-variant-numeric: tabular-nums;
        }

        .shutdown-count strong {
            font-size: 54px;
            line-height: 1;
        }

        .shutdown-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .shutdown-action {
            height: 40px;
            border: 0;
            border-radius: 999px;
            color: #263244;
            background: rgba(38, 50, 68, 0.09);
            font: inherit;
            font-size: 14px;
            font-weight: 650;
            cursor: pointer;
        }

        .shutdown-action.primary {
            color: #fff;
            background: #e05252;
        }

        .theme-hint {
            grid-column: 1 / -1;
            margin: -2px 2px 0;
            color: currentColor;
            opacity: 0.44;
            font-size: 12px;
            line-height: 1.4;
        }

        body[data-theme="day"] {
            color: #253044;
            background: #f2efe8;
        }

        body[data-theme="day"] .shell {
            background:
                radial-gradient(circle at 20% 0%, rgba(255, 214, 112, 0.38), transparent 34%),
                radial-gradient(circle at 88% 8%, rgba(85, 166, 255, 0.22), transparent 36%),
                linear-gradient(145deg, #fffaf0 0%, #edf5ff 100%);
            box-shadow: 0 22px 52px rgba(89, 102, 120, 0.18);
        }

        body[data-theme="mint"] {
            color: #17352f;
            background: #e8f4ef;
        }

        body[data-theme="mint"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(75, 199, 157, 0.24), transparent 34%),
                radial-gradient(circle at 86% 12%, rgba(255, 221, 124, 0.26), transparent 34%),
                linear-gradient(145deg, #f7fff9 0%, #dff3ea 100%);
            box-shadow: 0 22px 52px rgba(40, 99, 82, 0.16);
        }

        body[data-theme="peach"] {
            color: #49312f;
            background: #f7ece7;
        }

        body[data-theme="peach"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(255, 167, 131, 0.28), transparent 34%),
                radial-gradient(circle at 88% 10%, rgba(255, 218, 107, 0.28), transparent 34%),
                linear-gradient(145deg, #fff7f0 0%, #f6e3dc 100%);
            box-shadow: 0 22px 52px rgba(121, 70, 58, 0.16);
        }

        body[data-theme="paper"] {
            color: #30333a;
            background: #eeeeea;
        }

        body[data-theme="paper"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(120, 158, 255, 0.18), transparent 34%),
                radial-gradient(circle at 86% 10%, rgba(255, 212, 119, 0.20), transparent 34%),
                linear-gradient(145deg, #fbfaf5 0%, #e6e8e5 100%);
            box-shadow: 0 22px 52px rgba(69, 76, 86, 0.15);
        }

        body[data-theme="sky"] {
            color: #1b344b;
            background: #e8f4ff;
        }

        body[data-theme="sky"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(72, 164, 255, 0.26), transparent 34%),
                radial-gradient(circle at 88% 10%, rgba(127, 222, 239, 0.22), transparent 34%),
                linear-gradient(145deg, #f6fbff 0%, #dcefff 100%);
            box-shadow: 0 22px 52px rgba(44, 97, 142, 0.16);
        }

        body[data-theme="rose"] {
            color: #4a2736;
            background: #f7e9ef;
        }

        body[data-theme="rose"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(240, 110, 146, 0.24), transparent 34%),
                radial-gradient(circle at 88% 10%, rgba(119, 186, 255, 0.18), transparent 34%),
                linear-gradient(145deg, #fff6f8 0%, #f2dfe8 100%);
            box-shadow: 0 22px 52px rgba(121, 54, 78, 0.15);
        }

        body[data-theme="leaf"] {
            color: #24391f;
            background: #edf5e6;
        }

        body[data-theme="leaf"] .shell {
            background:
                radial-gradient(circle at 18% 0%, rgba(138, 199, 82, 0.24), transparent 34%),
                radial-gradient(circle at 88% 10%, rgba(255, 211, 103, 0.20), transparent 34%),
                linear-gradient(145deg, #fbfff5 0%, #dfeeda 100%);
            box-shadow: 0 22px 52px rgba(74, 105, 53, 0.15);
        }

        body[data-theme] .subtitle,
        body[data-theme] .status,
        body[data-theme] .label,
        body[data-theme] .salary-stat .salary-label,
        body[data-theme] .salary-note,
        body[data-theme] .salary-input-wrap label,
        body[data-theme] .salary-input-wrap span,
        body[data-theme] .setting-field label {
            color: currentColor;
            opacity: 0.62;
        }

        body[data-theme] .status strong,
        body[data-theme] .salary-stat .amount,
        body[data-theme] .salary-input-wrap input,
        body[data-theme] .setting-field input,
        body[data-theme] .setting-field select,
        body[data-theme] .setting-field textarea {
            color: currentColor;
        }

        body[data-theme] .salary-panel,
        body[data-theme] .settings-panel {
            background: rgba(255, 255, 255, 0.42);
        }

        body[data-theme] .salary-input-wrap,
        body[data-theme] .salary-stat,
        body[data-theme] .setting-field {
            background: rgba(255, 255, 255, 0.52);
        }

        body[data-theme] .flip-card {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.78) 0%, rgba(255, 255, 255, 0.50) 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.8),
                0 14px 26px rgba(92, 101, 116, 0.16);
        }

        body[data-theme] .flip-card::before {
            background: rgba(80, 88, 100, 0.14);
            box-shadow: 0 1px 0 rgba(255, 255, 255, 0.44);
        }

        body[data-theme] .flip-card::after {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), transparent 45%);
        }

        body[data-theme] .flip-value {
            color: currentColor;
            text-shadow: none;
        }

        body[data-theme] .tool-button {
            color: currentColor;
            background: rgba(255, 255, 255, 0.58);
        }

        body[data-theme] .setting-field textarea::placeholder {
            color: currentColor;
            opacity: 0.34;
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
            .settings-panel {
                grid-template-columns: 1fr;
            }
            .shutdown-settings {
                grid-template-columns: 1fr;
            }
        }

        html.compact,
        html.compact body,
        body.compact {
            min-height: 100vh;
            padding: 0;
            background: #010203;
        }

        body.compact .shell {
            width: 220px;
            padding: 0;
            border-radius: 0;
            background: #010203;
            box-shadow: none;
        }

        body.compact .topbar,
        body.compact .settings-panel,
        body.compact .salary-panel,
        body.compact .label {
            display: none;
        }

        body.compact .countdown-grid {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            width: 220px;
            height: 56px;
            margin: 0;
            background: #010203;
        }

        body.compact .flip-unit {
            display: flex;
            align-items: center;
            min-width: 0;
            background: #010203;
        }

        body.compact .flip-unit:not(:last-child)::after {
            content: ":";
            display: block;
            width: 18px;
            margin: 0 4px;
            color: #fff;
            font-size: 24px;
            font-weight: 780;
            line-height: 1;
            text-align: center;
            font-variant-numeric: tabular-nums;
        }

        body.compact .flip-card {
            width: 48px;
            height: 32px;
            overflow: visible;
            border-radius: 0;
            background: #010203;
            box-shadow: none;
            perspective: none;
        }

        body.compact .flip-card::before,
        body.compact .flip-card::after {
            display: none;
        }

        body.compact .flip-value {
            position: static;
            width: 48px;
            height: 32px;
            font-size: 24px;
            color: #fff;
            text-shadow: none;
            animation: none;
        }
    </style>
</head>
<body data-theme="day">
    <main class="shell" id="shell">
        <div class="bg-media-layer" id="bgMediaLayer"></div>
        <section class="topbar">
            <div>
                <h1>今日倒计时</h1>
                <p class="subtitle" id="subtitle">距离 18:00 还有</p>
            </div>
            <div class="status">
                <div class="top-actions">
                    <button class="tool-button" id="backgroundButton" type="button">后台</button>
                </div>
                <span id="targetDisplay">今天 18:00</span>
                <strong id="currentTimeDisplay">--:--:--</strong>
            </div>
        </section>

        <section class="settings-panel">
            <div class="setting-field">
                <label for="workStartTime">上班</label>
                <input id="workStartTime" type="time" value="09:00" />
            </div>
            <div class="setting-field">
                <label for="offWorkTime">下班</label>
                <input id="offWorkTime" type="time" value="18:00" />
            </div>
            <div class="setting-field">
                <label for="themeSelect">皮肤</label>
                <select id="themeSelect">
                    <option value="day">清晨</option>
                    <option value="mint">薄荷</option>
                    <option value="peach">蜜桃</option>
                    <option value="paper">纸张</option>
                    <option value="sky">晴空</option>
                    <option value="rose">玫瑰</option>
                    <option value="leaf">叶绿</option>
                </select>
            </div>
            <div class="shutdown-settings">
                <div class="setting-field">
                    <label for="shutdownEnabled">关机</label>
                    <input id="shutdownEnabled" type="checkbox" />
                </div>
                <div class="setting-field">
                    <label for="shutdownTime">时间</label>
                    <input id="shutdownTime" type="time" value="18:30" />
                </div>
                <div class="setting-field shutdown-description">
                    <label for="shutdownDescription">描述</label>
                    <textarea id="shutdownDescription" maxlength="80" placeholder="例如：下班啦，电脑准备关机"></textarea>
                </div>
                <div class="shutdown-status" id="shutdownStatus">自动关机未开启。</div>
            </div>
            <div class="background-settings">
                <div class="setting-field">
                    <label for="bgColorInput">背景</label>
                    <input id="bgColorInput" type="color" value="#f2efe8" />
                </div>
                <button class="mini-button" id="chooseBgMedia" type="button">图片/视频</button>
                <button class="mini-button" id="clearBgMedia" type="button">清除</button>
                <div class="background-file-name" id="bgMediaName">当前使用颜色背景。</div>
            </div>
            <div class="theme-hint">Ctrl + 1~7 切换皮肤，Ctrl + + 轮换下一款。</div>
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
            <div class="salary-note" id="salaryNote">按每月 15 日薪资周期、工作日起止时间估算。</div>
        </section>
    </main>

    <div class="shutdown-modal" id="shutdownModal" role="dialog" aria-modal="true" aria-labelledby="shutdownTitle">
        <div class="shutdown-dialog">
            <h2 id="shutdownTitle">即将自动关机</h2>
            <p class="shutdown-desc" id="shutdownModalDescription">定时关机时间到了。</p>
            <div class="shutdown-count"><strong id="shutdownCountdown">30</strong><span>秒后关机</span></div>
            <div class="shutdown-actions">
                <button class="shutdown-action" id="cancelShutdownButton" type="button">取消本次</button>
                <button class="shutdown-action primary" id="shutdownNowButton" type="button">立即关机</button>
            </div>
        </div>
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
            var subtitle = document.getElementById('subtitle');
            var workStartTimeInput = document.getElementById('workStartTime');
            var offWorkTimeInput = document.getElementById('offWorkTime');
            var themeSelect = document.getElementById('themeSelect');
            var backgroundButton = document.getElementById('backgroundButton');
            var monthlySalaryInput = document.getElementById('monthlySalary');
            var monthEarnedEl = document.getElementById('monthEarned');
            var todayEarnedEl = document.getElementById('todayEarned');
            var salaryNote = document.getElementById('salaryNote');
            var shutdownEnabledInput = document.getElementById('shutdownEnabled');
            var shutdownTimeInput = document.getElementById('shutdownTime');
            var shutdownDescriptionInput = document.getElementById('shutdownDescription');
            var shutdownStatus = document.getElementById('shutdownStatus');
            var shutdownModal = document.getElementById('shutdownModal');
            var shutdownModalDescription = document.getElementById('shutdownModalDescription');
            var shutdownCountdownEl = document.getElementById('shutdownCountdown');
            var cancelShutdownButton = document.getElementById('cancelShutdownButton');
            var shutdownNowButton = document.getElementById('shutdownNowButton');
            var shell = document.getElementById('shell');
            var bgMediaLayer = document.getElementById('bgMediaLayer');
            var bgColorInput = document.getElementById('bgColorInput');
            var chooseBgMedia = document.getElementById('chooseBgMedia');
            var clearBgMedia = document.getElementById('clearBgMedia');
            var bgMediaName = document.getElementById('bgMediaName');

            var TARGET_HOUR = 18;
            var TARGET_MINUTE = 0;
            var TARGET_SECOND = 0;
            var WORK_START_HOUR = 9;
            var WORK_START_MINUTE = 0;
            var WORK_END_HOUR = 18;
            var WORK_END_MINUTE = 0;
            var SALARY_STORAGE_KEY = 'countdown_monthly_salary';
            var WORK_START_STORAGE_KEY = 'countdown_work_start_time';
            var OFF_WORK_STORAGE_KEY = 'countdown_off_work_time';
            var THEME_STORAGE_KEY = 'countdown_theme';
            var SHUTDOWN_ENABLED_STORAGE_KEY = 'countdown_shutdown_enabled';
            var SHUTDOWN_TIME_STORAGE_KEY = 'countdown_shutdown_time';
            var SHUTDOWN_DESCRIPTION_STORAGE_KEY = 'countdown_shutdown_description';
            var BG_STORAGE_KEY = 'countdown_background_settings';
            var THEME_NAMES = ['day', 'mint', 'peach', 'paper', 'sky', 'rose', 'leaf'];
            var previousValues = {};
            var lastSalarySecond = -1;
            var isCompact = false;
            var pendingCompactSync = false;
            var shutdownEnabled = false;
            var shutdownHour = 18;
            var shutdownMinute = 30;
            var lastShutdownSecond = -1;
            var shutdownPromptKey = '';
            var shutdownPromptOpen = false;
            var shutdownPromptEndsAt = 0;
            var shutdownExecuting = false;
            var raf = window.requestAnimationFrame ||
                window.webkitRequestAnimationFrame ||
                function(callback) { return window.setTimeout(callback, 50); };

            function addEvent(target, name, handler) {
                if (target.addEventListener) target.addEventListener(name, handler, false);
                else if (target.attachEvent) target.attachEvent('on' + name, handler);
            }

            function addClass(target, name) {
                if ((' ' + target.className + ' ').indexOf(' ' + name + ' ') < 0) {
                    target.className = (target.className + ' ' + name).replace(/^\\s+|\\s+$/g, '');
                }
            }

            function removeClass(target, name) {
                target.className = (' ' + target.className + ' ')
                    .replace(new RegExp(' ' + name + ' ', 'g'), ' ')
                    .replace(/^\\s+|\\s+$/g, '');
            }

            function addBodyClass(name) {
                addClass(document.documentElement, name);
                addClass(document.body, name);
            }

            function removeBodyClass(name) {
                removeClass(document.documentElement, name);
                removeClass(document.body, name);
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
                if (window.pywebview && window.pywebview.api && window.pywebview.api.set_compact) {
                    removeBodyClass('compact');
                    pendingCompactSync = false;
                    window.pywebview.api.set_compact(isCompact);
                } else {
                    if (isCompact) addBodyClass('compact');
                    else removeBodyClass('compact');
                    syncCompactWindow();
                }
            }

            function toggleCompactMode() {
                setCompactMode(!isCompact);
            }

            window.__setCountdownCompactMode = function(nextCompact) {
                setCompactMode(!!nextCompact);
            };

            function padZero(num, length) {
                length = length || 2;
                var text = String(num);
                while (text.length < length) text = '0' + text;
                return text;
            }

            function formatTime(h, m, s) {
                return padZero(h) + ':' + padZero(m) + ':' + padZero(s);
            }

            function formatTargetTime() {
                return padZero(TARGET_HOUR) + ':' + padZero(TARGET_MINUTE);
            }

            function formatWorkStartTime() {
                return padZero(WORK_START_HOUR) + ':' + padZero(WORK_START_MINUTE);
            }

            function parseClockTime(value) {
                var match = /^([01]?\\d|2[0-3]):([0-5]\\d)$/.exec(value || '');
                if (!match) return null;
                return {
                    hour: Number(match[1]),
                    minute: Number(match[2])
                };
            }

            function applyOffWorkTime(value, shouldSave) {
                var parsed = parseClockTime(value) || { hour: 18, minute: 0 };
                TARGET_HOUR = parsed.hour;
                TARGET_MINUTE = parsed.minute;
                WORK_END_HOUR = parsed.hour;
                WORK_END_MINUTE = parsed.minute;
                offWorkTimeInput.value = formatTargetTime();
                subtitle.innerText = '距离 ' + formatTargetTime() + ' 还有';
                if (shouldSave) {
                    try {
                        localStorage.setItem(OFF_WORK_STORAGE_KEY, formatTargetTime());
                    } catch (err) {}
                }
            }

            function formatShutdownTime() {
                return padZero(shutdownHour) + ':' + padZero(shutdownMinute);
            }

            function makeShutdownKey(date) {
                return date.getFullYear() + '-' + padZero(date.getMonth() + 1) + '-' + padZero(date.getDate()) + ' ' + formatShutdownTime();
            }

            function getTodayShutdownDate(now) {
                var target = new Date(now.getTime());
                target.setHours(shutdownHour, shutdownMinute, 0, 0);
                return target;
            }

            function getNextShutdownDate(now) {
                var target = getTodayShutdownDate(now);
                if (now.getTime() >= target.getTime()) {
                    target.setDate(target.getDate() + 1);
                }
                return target;
            }

            function getShutdownDescription() {
                var text = (shutdownDescriptionInput.value || '').replace(/^\\s+|\\s+$/g, '');
                return text || '定时关机时间到了。';
            }

            function saveShutdownSettings() {
                try {
                    localStorage.setItem(SHUTDOWN_ENABLED_STORAGE_KEY, shutdownEnabled ? '1' : '0');
                    localStorage.setItem(SHUTDOWN_TIME_STORAGE_KEY, formatShutdownTime());
                    localStorage.setItem(SHUTDOWN_DESCRIPTION_STORAGE_KEY, shutdownDescriptionInput.value || '');
                } catch (err) {}
            }

            function updateShutdownStatus(now) {
                var target;
                var label;
                now = now || new Date();
                if (!shutdownEnabled) {
                    shutdownStatus.innerText = '自动关机未开启。';
                    return;
                }
                target = getNextShutdownDate(now);
                label = target.toDateString() === now.toDateString() ? '今天' : '明天';
                shutdownStatus.innerText = '已开启，' + label + ' ' + formatShutdownTime() + ' 将弹出 30 秒关机确认。';
            }

            function applyShutdownSettings(enabled, timeValue, description, shouldSave, preventImmediate) {
                var parsed = parseClockTime(timeValue) || { hour: 18, minute: 30 };
                var now = new Date();
                var todayTarget;
                shutdownEnabled = !!enabled;
                shutdownHour = parsed.hour;
                shutdownMinute = parsed.minute;
                shutdownEnabledInput.checked = shutdownEnabled;
                shutdownTimeInput.value = formatShutdownTime();
                if (typeof description === 'string') shutdownDescriptionInput.value = description;
                if (!shutdownEnabled) closeShutdownPrompt();
                if (preventImmediate && shutdownEnabled) {
                    todayTarget = getTodayShutdownDate(now);
                    if (now.getTime() >= todayTarget.getTime()) {
                        shutdownPromptKey = makeShutdownKey(todayTarget);
                    }
                }
                updateShutdownStatus(now);
                if (shouldSave) saveShutdownSettings();
            }

            function restoreWindowForShutdown() {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.restore_from_background) {
                    window.pywebview.api.restore_from_background();
                }
            }

            function openShutdownPrompt(targetDate) {
                if (shutdownPromptOpen || shutdownExecuting) return;
                shutdownPromptKey = makeShutdownKey(targetDate);
                shutdownPromptOpen = true;
                shutdownPromptEndsAt = Date.now() + 30000;
                shutdownModalDescription.innerText = getShutdownDescription();
                shutdownCountdownEl.innerText = '30';
                addClass(shutdownModal, 'is-open');
                restoreWindowForShutdown();
            }

            function closeShutdownPrompt() {
                shutdownPromptOpen = false;
                removeClass(shutdownModal, 'is-open');
            }

            function runShutdownNow() {
                var result;
                if (shutdownExecuting) return;
                shutdownExecuting = true;
                shutdownCountdownEl.innerText = '0';
                shutdownStatus.innerText = '正在执行系统关机...';
                if (window.pywebview && window.pywebview.api && window.pywebview.api.execute_shutdown) {
                    result = window.pywebview.api.execute_shutdown(getShutdownDescription());
                    if (result && result.catch) {
                        result.catch(function() {
                            shutdownExecuting = false;
                            shutdownStatus.innerText = '关机命令执行失败，请检查系统权限。';
                        });
                    }
                } else {
                    shutdownExecuting = false;
                    shutdownStatus.innerText = '当前环境无法调用系统关机。';
                }
            }

            function updateShutdownPrompt(now) {
                var secondsLeft;
                if (!shutdownPromptOpen || shutdownExecuting) return;
                secondsLeft = Math.ceil((shutdownPromptEndsAt - now.getTime()) / 1000);
                if (secondsLeft <= 0) {
                    runShutdownNow();
                    return;
                }
                shutdownCountdownEl.innerText = String(secondsLeft);
            }

            function checkShutdownSchedule(now) {
                var target;
                var key;
                if (!shutdownEnabled || shutdownExecuting) return;
                if (now.getSeconds() === lastShutdownSecond) {
                    updateShutdownPrompt(now);
                    return;
                }
                lastShutdownSecond = now.getSeconds();
                updateShutdownPrompt(now);
                if (shutdownPromptOpen) return;
                target = getTodayShutdownDate(now);
                key = makeShutdownKey(target);
                if (now.getTime() >= target.getTime() && shutdownPromptKey !== key) {
                    openShutdownPrompt(target);
                }
                updateShutdownStatus(now);
            }

            function applyTheme(theme, shouldSave) {
                var nextTheme = THEME_NAMES.indexOf(theme) >= 0 ? theme : 'day';
                document.body.setAttribute('data-theme', nextTheme);
                themeSelect.value = nextTheme;
                if (shouldSave) {
                    try {
                        localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
                    } catch (err) {}
                }
            }

            function applyWorkStartTime(value, shouldSave) {
                var parsed = parseClockTime(value) || { hour: 9, minute: 0 };
                WORK_START_HOUR = parsed.hour;
                WORK_START_MINUTE = parsed.minute;
                workStartTimeInput.value = formatWorkStartTime();
                if (shouldSave) {
                    try {
                        localStorage.setItem(WORK_START_STORAGE_KEY, formatWorkStartTime());
                    } catch (err) {}
                }
            }

            function saveBackgroundSettings(settings) {
                try {
                    localStorage.setItem(BG_STORAGE_KEY, JSON.stringify(settings));
                } catch (err) {}
            }

            function applyBackgroundSettings(settings, shouldSave) {
                var hasSettings = !!settings;
                var customColor = !!(settings && settings.customColor);
                var color = settings && /^#[0-9a-fA-F]{6}$/.test(settings.color || '') ? settings.color : '#f2efe8';
                var mediaUrl = settings && settings.mediaUrl ? settings.mediaUrl : '';
                var mediaType = settings && settings.mediaType ? settings.mediaType : '';
                var mediaName = settings && settings.mediaName ? settings.mediaName : '';
                var mediaEl;

                bgColorInput.value = color;
                shell.style.background = customColor || mediaUrl ? color : '';
                bgMediaLayer.innerHTML = '';
                removeClass(bgMediaLayer, 'is-active');

                if (mediaUrl && (mediaType === 'image' || mediaType === 'video')) {
                    mediaEl = document.createElement(mediaType === 'video' ? 'video' : 'img');
                    mediaEl.src = mediaUrl;
                    if (mediaType === 'video') {
                        mediaEl.autoplay = true;
                        mediaEl.loop = true;
                        mediaEl.muted = true;
                        mediaEl.playsInline = true;
                    }
                    bgMediaLayer.appendChild(mediaEl);
                    addClass(bgMediaLayer, 'is-active');
                    bgMediaName.innerText = mediaName || '已选择自定义背景。';
                } else {
                    bgMediaName.innerText = '当前使用颜色背景。';
                }

                if (shouldSave) {
                    saveBackgroundSettings({
                        color: color,
                        customColor: customColor,
                        mediaUrl: mediaUrl,
                        mediaType: mediaType,
                        mediaName: mediaName
                    });
                }
            }

            function restoreBackgroundSettings() {
                var saved;
                try {
                    saved = JSON.parse(localStorage.getItem(BG_STORAGE_KEY) || 'null');
                } catch (err) {
                    saved = null;
                }
                applyBackgroundSettings(saved, false);
            }

            function cycleTheme() {
                var current = themeSelect.value || 'day';
                var index = THEME_NAMES.indexOf(current);
                var next = THEME_NAMES[(index + 1) % THEME_NAMES.length];
                applyTheme(next, true);
            }

            function formatMoney(amount) {
                return '¥' + Number(amount).toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
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
                start.setHours(WORK_START_HOUR, WORK_START_MINUTE, 0, 0);
                end = new Date(now.getTime());
                end.setHours(WORK_END_HOUR, WORK_END_MINUTE, 0, 0);
                if (end.getTime() <= start.getTime()) return 0;
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
                    salaryNote.innerText = '输入月薪后，按每月 15 日薪资周期和工作日 ' + formatWorkStartTime() + '-' + formatTargetTime() + ' 估算。';
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

                targetDisplay.innerText = (isToday ? '今天' : '明天') + ' ' + formatTargetTime();
                currentTimeDisplay.innerText = formatTime(now.getHours(), now.getMinutes(), now.getSeconds());

                if (now.getSeconds() !== lastSalarySecond) {
                    lastSalarySecond = now.getSeconds();
                    updateSalary(now);
                }
                checkShutdownSchedule(now);
            }

            function tick() {
                updateCountdown(new Date());
                raf(tick);
            }

            try {
                applyWorkStartTime(localStorage.getItem(WORK_START_STORAGE_KEY), false);
                applyOffWorkTime(localStorage.getItem(OFF_WORK_STORAGE_KEY), false);
                applyTheme(localStorage.getItem(THEME_STORAGE_KEY), false);
                var saved = localStorage.getItem(SALARY_STORAGE_KEY);
                var savedShutdownEnabled = localStorage.getItem(SHUTDOWN_ENABLED_STORAGE_KEY) === '1';
                var savedShutdownTime = localStorage.getItem(SHUTDOWN_TIME_STORAGE_KEY) || '18:30';
                var savedShutdownDescription = localStorage.getItem(SHUTDOWN_DESCRIPTION_STORAGE_KEY) || '';
                if (saved) monthlySalaryInput.value = saved;
                applyShutdownSettings(savedShutdownEnabled, savedShutdownTime, savedShutdownDescription, false, true);
                restoreBackgroundSettings();
            } catch (err) {
                applyWorkStartTime('09:00', false);
                applyOffWorkTime('18:00', false);
                applyTheme('day', false);
                applyShutdownSettings(false, '18:30', '', false, true);
                applyBackgroundSettings(null, false);
            }

            workStartTimeInput.onchange = function() {
                applyWorkStartTime(this.value, true);
                updateSalary(new Date());
            };

            offWorkTimeInput.onchange = function() {
                applyOffWorkTime(this.value, true);
                updateCountdown(new Date());
                updateSalary(new Date());
            };

            themeSelect.onchange = function() {
                applyTheme(this.value, true);
            };

            shutdownEnabledInput.onchange = function() {
                applyShutdownSettings(this.checked, shutdownTimeInput.value, shutdownDescriptionInput.value, true, true);
            };

            shutdownTimeInput.onchange = function() {
                applyShutdownSettings(shutdownEnabledInput.checked, this.value, shutdownDescriptionInput.value, true, true);
            };

            shutdownDescriptionInput.oninput = function() {
                saveShutdownSettings();
                if (shutdownPromptOpen) {
                    shutdownModalDescription.innerText = getShutdownDescription();
                }
            };

            bgColorInput.oninput = function() {
                applyBackgroundSettings({ color: this.value, customColor: true }, true);
            };

            chooseBgMedia.onclick = function() {
                if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.select_background_media) {
                    bgMediaName.innerText = '当前环境不支持选择本地文件。';
                    return;
                }
                window.pywebview.api.select_background_media(bgColorInput.value).then(function(result) {
                    if (!result) return;
                    if (result.error) {
                        bgMediaName.innerText = result.error;
                        return;
                    }
                    applyBackgroundSettings(result, true);
                }).catch(function() {
                    bgMediaName.innerText = '选择背景失败，请重试。';
                });
            };

            clearBgMedia.onclick = function() {
                applyBackgroundSettings({ color: bgColorInput.value, customColor: true }, true);
            };

            backgroundButton.onclick = function() {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.send_to_background) {
                    window.pywebview.api.send_to_background();
                } else if (window.blur) {
                    window.blur();
                }
            };

            cancelShutdownButton.onclick = function() {
                closeShutdownPrompt();
                updateShutdownStatus(new Date());
            };

            shutdownNowButton.onclick = function() {
                runShutdownNow();
            };

            monthlySalaryInput.oninput = function() {
                try {
                    localStorage.setItem(SALARY_STORAGE_KEY, this.value);
                } catch (err) {}
                updateSalary(new Date());
            };

            addEvent(document, 'keydown', function(event) {
                event = event || window.event;
                if (event.ctrlKey && event.keyCode === 87) {
                    if (event.preventDefault) event.preventDefault();
                    event.returnValue = false;
                    toggleCompactMode();
                    return false;
                }
                if (event.ctrlKey && event.keyCode >= 49 && event.keyCode <= 55) {
                    if (event.preventDefault) event.preventDefault();
                    event.returnValue = false;
                    applyTheme(THEME_NAMES[event.keyCode - 49], true);
                    return false;
                }
                if (event.ctrlKey && (event.keyCode === 187 || event.keyCode === 107)) {
                    if (event.preventDefault) event.preventDefault();
                    event.returnValue = false;
                    cycleTheme();
                    return false;
                }
            });

            addEvent(document, 'dblclick', function() {
                if (isCompact) setCompactMode(false);
            });

            addEvent(window, 'pywebviewready', function() {
                if (pendingCompactSync) syncCompactWindow();
            });

            addEvent(window, 'focus', function() {
                if (isCompact) {
                    isCompact = false;
                    removeBodyClass('compact');
                }
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
        self.tray_icon = None
        self.tray_menu = None
        self._tray_handlers = []
        self.float_root = None
        self.float_label = None
        self.float_thread = None
        self.float_stop_event = threading.Event()
        self.float_dragging = False
        self.float_offset = (0, 0)

    def bind(self, window):
        self.window = window

    def _defer_window_action(self, action):
        def runner():
            time.sleep(0.05)
            try:
                action()
            except Exception:
                pass

        threading.Thread(target=runner, daemon=True).start()

    def _invoke_native(self, action):
        def runner():
            native = None
            for _ in range(80):
                native = getattr(self.window, 'native', None) if self.window else None
                if native is not None:
                    break
                time.sleep(0.05)

            if native is None:
                return

            try:
                from System import Action
                native.BeginInvoke(Action(action))
            except Exception:
                try:
                    action()
                except Exception:
                    pass

        threading.Thread(target=runner, daemon=True).start()

    def _format_float_time(self):
        now = datetime.datetime.now()
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        total_seconds = max(0, int((target - now).total_seconds()))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f'{hours:02d}  :  {minutes:02d}  :  {seconds:02d}'

    def _sync_page_compact(self, compact):
        return

    def _apply_window_round_region(self, radius=26):
        native = getattr(self.window, 'native', None) if self.window else None
        if native is None:
            return
        try:
            from System.Drawing import Region
            from System.Drawing.Drawing2D import GraphicsPath

            width = native.ClientSize.Width
            height = native.ClientSize.Height
            diameter = radius * 2
            path = GraphicsPath()
            path.AddArc(0, 0, diameter, diameter, 180, 90)
            path.AddArc(width - diameter, 0, diameter, diameter, 270, 90)
            path.AddArc(width - diameter, height - diameter, diameter, diameter, 0, 90)
            path.AddArc(0, height - diameter, diameter, diameter, 90, 90)
            path.CloseFigure()
            native.Region = Region(path)
        except Exception:
            pass

    def _show_float_window(self):
        if self.float_thread and self.float_thread.is_alive():
            return

        self.float_stop_event.clear()

        def runner():
            try:
                import tkinter as tk
                key_color = '#010203'
                root = tk.Tk()
                root.title('倒计时 · 迷你')
                root.overrideredirect(True)
                root.attributes('-topmost', True)
                root.configure(bg=key_color)
                root.wm_attributes('-transparentcolor', key_color)
                root.geometry('230x54+260+180')

                label = tk.Label(
                    root,
                    text=self._format_float_time(),
                    font=('Segoe UI', 18, 'bold'),
                    fg='white',
                    bg=key_color,
                    padx=0,
                    pady=0,
                )
                label.pack(fill='both', expand=True)

                def restore_main(event=None):
                    root.after(0, root.destroy)
                    self.restore_main_window()

                def exit_app():
                    root.after(0, root.destroy)
                    if self.window:
                        self._defer_window_action(self.window.destroy)

                menu = tk.Menu(root, tearoff=0)
                menu.add_command(label='恢复主窗口', command=restore_main)
                menu.add_command(label='退出', command=exit_app)

                def show_menu(event):
                    menu.tk_popup(event.x_root, event.y_root)

                def start_drag(event):
                    self.float_offset = (event.x, event.y)

                def drag(event):
                    x = root.winfo_pointerx() - self.float_offset[0]
                    y = root.winfo_pointery() - self.float_offset[1]
                    root.geometry(f'+{x}+{y}')

                def refresh():
                    if self.float_stop_event.is_set():
                        root.destroy()
                        return
                    label.configure(text=self._format_float_time())
                    root.after(250, refresh)

                root.bind('<Double-Button-1>', restore_main)
                label.bind('<Double-Button-1>', restore_main)
                root.bind('<Control-w>', restore_main)
                root.bind('<Control-W>', restore_main)
                label.bind('<Control-w>', restore_main)
                label.bind('<Control-W>', restore_main)
                root.bind('<Button-3>', show_menu)
                label.bind('<Button-3>', show_menu)
                root.bind('<ButtonPress-1>', start_drag)
                label.bind('<ButtonPress-1>', start_drag)
                root.bind('<B1-Motion>', drag)
                label.bind('<B1-Motion>', drag)

                self.float_root = root
                self.float_label = label
                refresh()
                root.after(100, root.focus_force)
                root.mainloop()
            except Exception:
                pass
            finally:
                self.float_root = None
                self.float_label = None

        self.float_thread = threading.Thread(target=runner, daemon=True)
        self.float_thread.start()

    def _hide_float_window(self):
        self.float_stop_event.set()
        root = self.float_root
        if root is not None:
            try:
                root.after(0, root.destroy)
            except Exception:
                pass
        self.float_root = None
        self.float_label = None

    def setup_tray(self):
        if self.tray_icon is not None:
            return True

        def create_tray():
            try:
                import clr
                clr.AddReference('System.Windows.Forms')
                clr.AddReference('System.Drawing')
                import System.Windows.Forms as WinForms
                from System.Drawing import Icon

                tray = WinForms.NotifyIcon()
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.ico')
                if os.path.exists(icon_path):
                    tray.Icon = Icon(icon_path)
                else:
                    tray.Icon = Icon.ExtractAssociatedIcon(sys.executable)
                tray.Text = '倒计时'
                tray.Visible = True

                menu = WinForms.ContextMenu()
                show_item = WinForms.MenuItem('显示')
                exit_item = WinForms.MenuItem('退出')
                menu.MenuItems.Add(show_item)
                menu.MenuItems.Add(exit_item)
                tray.ContextMenu = menu

                def show_window(sender=None, event=None):
                    self.restore_main_window()

                def exit_app(sender=None, event=None):
                    try:
                        tray.Visible = False
                        tray.Dispose()
                    except Exception:
                        pass
                    if self.window:
                        self._defer_window_action(self.window.destroy)

                tray.DoubleClick += show_window
                show_item.Click += show_window
                exit_item.Click += exit_app

                self.tray_icon = tray
                self.tray_menu = menu
                self._tray_handlers.extend([show_item, exit_item, show_window, exit_app])
            except Exception:
                pass

        self._invoke_native(create_tray)
        return True

    def set_compact(self, compact):
        self.compact = bool(compact)
        if self.window:
            if self.compact:
                self.setup_tray()
                if hasattr(self.window, 'hide'):
                    self._defer_window_action(self.window.hide)
                self._show_float_window()
            else:
                self._hide_float_window()

                def restore_main_window():
                    self.window.show()
                    self.window.restore()
                    self.window.resize(604, 900)
                    self.window.set_title('倒计时')
                    self._apply_window_round_region()

                self._defer_window_action(restore_main_window)
        return self.compact

    def restore_main_window(self):
        self.compact = False
        self._hide_float_window()

        def restore_main_window():
            if not self.window:
                return
            self.window.show()
            self.window.restore()
            self.window.resize(604, 900)
            self.window.set_title('倒计时')
            self._apply_window_round_region()

        self._defer_window_action(restore_main_window)
        return True

    def send_to_background(self):
        if not self.window:
            return False
        self.setup_tray()
        if hasattr(self.window, 'hide'):
            self._defer_window_action(self.window.hide)
            return True
        if hasattr(self.window, 'minimize'):
            self._defer_window_action(self.window.minimize)
            return True
        return False

    def restore_from_background(self):
        if not self.window:
            return False
        def restore_window():
            self.compact = False
            self._hide_float_window()
            for method_name in ('show', 'restore', 'bring_to_front'):
                method = getattr(self.window, method_name, None)
                if callable(method):
                    try:
                        method()
                    except Exception:
                        pass

        self._defer_window_action(restore_window)
        return True

    def execute_shutdown(self, description=''):
        subprocess.Popen(['shutdown', '/s', '/t', '0'])
        return True

    def select_background_media(self, color='#f2efe8'):
        if not self.window:
            return {'error': '窗口尚未准备好。'}

        try:
            paths = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False,
                file_types=(
                    '图片和视频 (*.jpg;*.jpeg;*.png;*.gif;*.webp;*.bmp;*.mp4;*.mov;*.m4v;*.webm)',
                    '图片 (*.jpg;*.jpeg;*.png;*.gif;*.webp;*.bmp)',
                    '视频 (*.mp4;*.mov;*.m4v;*.webm)',
                ),
            )
        except Exception:
            return {'error': '打开文件选择器失败。'}

        if not paths:
            return None

        path = Path(paths[0]).expanduser().resolve()
        suffix = path.suffix.lower()
        image_suffixes = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        video_suffixes = {'.mp4', '.mov', '.m4v', '.webm'}

        if not path.exists():
            return {'error': '文件不存在，请重新选择。'}
        if suffix in image_suffixes:
            media_type = 'image'
            try:
                mime_type = mimetypes.guess_type(path.name)[0] or 'image/jpeg'
                media_url = 'data:' + mime_type + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
            except OSError:
                return {'error': '图片读取失败，请重新选择。'}
        elif suffix in video_suffixes:
            media_type = 'video'
            media_url = path.as_uri()
        else:
            return {'error': '请选择支持的图片或视频文件。'}

        return {
            'color': color if isinstance(color, str) and color.startswith('#') else '#f2efe8',
            'customColor': True,
            'mediaUrl': media_url,
            'mediaType': media_type,
            'mediaName': path.name,
        }

    def apply_window_chrome(self):
        def apply_region():
            self._apply_window_round_region()

        self._invoke_native(apply_region)
        return True


def main():
    api = TimerApi()
    window_options = {
        'title': '倒计时',
        'html': HTML,
        'js_api': api,
        'width': 604,
        'height': 800,
        'resizable': False,
        'fullscreen': False,
        'min_size': (120, 32),
        'confirm_close': False,
        'text_select': False,
        'easy_drag': True,
        'frameless': True,
        'shadow': False,
        'on_top': True,
        'background_color': '#f2efe8'
    }
    window = webview.create_window(**window_options)
    api.bind(window)
    webview.start(
        api.apply_window_chrome,
        debug=False,
        private_mode=False,
        gui='winforms'
    )


if __name__ == '__main__':
    main()
