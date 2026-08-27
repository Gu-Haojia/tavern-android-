[app]

# 应用基本信息
title = 酒馆
version = 0.1.0
package.name = tavernpet
package.domain = org.example

# main.py 位于仓库根目录。只把应用运行时需要的文件放进 APK。
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,txt,json
source.exclude_dirs = tests,bin,.git,.github,.buildozer,venv,.venv

# ai_core.py 只使用标准库；Kivy 是唯一的 UI 框架依赖。
# distro 和 charset_normalizer 是运行时普通 Python 包，需显式列出。
# Python 版本通过 python3 recipe 版本钉死；hostpython3 由 python3 recipe 内部处理，
# 不需要也不应该显式写进 requirements。
requirements = python3==3.12.14,kivy,distro,charset_normalizer

# Kivy 应用使用 SDL2。sd12 不是合法的 bootstrap，也不是 Python 3.12 的简称。
p4a.bootstrap = sdl2

# 使用 p4a master 分支。配合上面的 Python recipe 版本可避免跟随默认版本漂移。
p4a.branch = master

orientation = portrait

# 手机直连 OpenAI 兼容 API / DeepSeek API。
android.permissions = INTERNET

# GitHub Actions 当前使用的 Android 工具链版本。
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# debug 命令输出 APK，而不是 AAB。文件名由 Buildozer/p4a 自动生成。
android.debug_artifact = apk

# 可选资源：文件存在后再取消注释。
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

[buildozer]

log_level = 2
warn_on_root = 1
