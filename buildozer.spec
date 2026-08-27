[app]

# 应用名（手机桌面显示的名字）
title = 酒馆

# buildozer 必需字段（否则启动校验直接拒绝）
version = 0.1.0

# 包名（唯一标识，装过就不能随便改）
package.name = tavernpet
package.domain = org.example

# 源文件入口
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
source.exclude_dirs = tests, bin, .git, .github, .buildozer

# ai_core 只使用 Python 标准库，UI 只依赖 Kivy。
# 不要添加未使用的普通 pip 包，否则 p4a 会进入额外的
# pure-Python 包安装阶段，容易受目标 Python 内置 pip 版本影响。
requirements = python3,kivy

# 固定到包含 Android wheel 安装修复的 p4a develop 提交，避免分支后续漂移。
p4a.branch = develop
p4a.commit = 9d5918bf752379f4520902524c15f794e45972b4

# Kivy Android 图形应用使用 SDL2 bootstrap。
p4a.bootstrap = sdl2

# 竖屏（手机聊天应用）
orientation = portrait

# 图标/横幅可放 icons/ 目录，缺省用 Kivy 默认
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

# 需要联网调 DeepSeek API
android.permissions = INTERNET
# 目标 API 34、最低 24（Android 7+）
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
# 打包为 debug 版（无需签名配置，适合自用）
android.debug_artifact_name = tavernpet-debug

[buildozer]
# 日志级别
log_level = 2
warn_on_root = 1
