[app]

# 应用名（手机桌面显示的名字）
title = 酒馆
version = 0.1.0

# 包名（唯一标识，装过就不能随便改）
package.name = tavernpet
package.domain = org.example

# 源文件入口
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
source.exclude_dirs = tests, bin, .git, .github

# 依赖：ai_core 只用 Python 标准库，Kivy 提供 UI
requirements = python3.12,kivy,distro,charset_normalizer>=3.0,<3.5

# 竖屏（手机聊天应用）
orientation = portrait

# 图标/横幅可放 icons/ 目录，缺省用 Kivy 默认
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

[buildozer]
# 日志级别
log_level = 2
warn_on_root = 1

[android]
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
[p4a]
# 固定 Python 版本到 3.12（3.14 太新，很多 wheel 还没出）
bootstrap = sd12
requirements = python3.12,kivy
