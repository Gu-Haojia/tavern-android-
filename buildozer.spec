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
# 选 3.11.11 的原因：
#   - 3.12.x 在 NDK 25b 上 grpmodule.c 编译失败（setgrent/getgrent/endgrent 隐式声明被 -Werror 升级为致命错误），
#     p4a master 的 python3 recipe 对 3.12 无对应补丁；3.11 的 grpmodule.c 有 HAVE_SETGRENT 守卫，是 p4a 最稳组合。
#   - 3.14.2（p4a 默认）会触发 hostpython3 3.14 ensurepip 的 BuildDependencyInstallError，不可用。
requirements = python3==3.11.11,hostpython3==3.11.11,kivy,distro,charset_normalizer

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
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# 可选资源：文件存在后再取消注释。
# icon.filename = %(source.dir)s/icons/icon.png
# presplash.filename = %(source.dir)s/icons/splash.png

[buildozer]

log_level = 2
warn_on_root = 1
