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
# Python 版本必须 python3 和 hostpython3 一起钉，两者必须完全一致（p4a 强制检查）。
# 用 3.12（p4a master 官方稳定支持到 3.12），配 NDK 29（官方验证组合）：
#   - 3.14.2 是 p4a 默认，但其 hostpython3 3.14 的 ensurepip 在旧 buildozer 下报 BuildDependencyInstallError，不可用；
#   - 3.12 在 NDK 29 下 grpmodule 可编译（NDK 25 的 bionic 不声明 setgrent 才会挂，升 NDK 到 29 解决）。
requirements = python3==3.12,hostpython3==3.12,kivy,distro,charset_normalizer

# Kivy 应用使用 SDL2。合法的 p4a bootstrap 只有 sdl2 / service_only / webview / qt 等；bootstrap 名不控制 Python 版本。
p4a.bootstrap = sdl2

# 使用 p4a master 分支。配合上面的 Python recipe 版本可避免跟随默认版本漂移。
p4a.branch = master

orientation = portrait

# 手机直连 OpenAI 兼容 API / DeepSeek API。
android.permissions = INTERNET

# GitHub Actions 当前使用的 Android 工具链版本。
android.api = 34
android.minapi = 24
android.ndk = 29
android.archs = arm64-v8a
android.accept_sdk_license = True

# 可选资源：文件存在后再取消注释。
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

[buildozer]

log_level = 2
warn_on_root = 1
