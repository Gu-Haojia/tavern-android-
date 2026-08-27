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
# 用 3.12.14（p4a master 官方稳定支持到 3.12；3.14 是默认但 hostpython3 3.14 的 ensurepip 在旧组合下报 BuildDependencyInstallError，不可用）。
# 必须写完整小版本号（3.12.14，不能只写 3.12）：p4a 拼下载地址 v{version}.tar.gz，只写 3.12 会 404 找不到 tag。
# 配 NDK 28c（p4a 官方推荐版本；NDK 25 的 bionic 不声明 setgrent 导致 grpmodule 编译失败，升到 28c 解决）。
requirements = python3==3.12.14,hostpython3==3.12.14,kivy,distro,charset_normalizer

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
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True

# 可选资源：文件存在后再取消注释。
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

[buildozer]

log_level = 2
warn_on_root = 1
