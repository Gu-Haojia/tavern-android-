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

# 依赖：ai_core 只用 Python 标准库，Kivy 提供 UI
# ⚠️ buildozer requirements 格式严格：
#   - 不要写 python3.12（不是 pip 包名，p4a 拉不到）
#   - 不要写 >=3.0,<3.5 这类版本约束（buildozer 按逗号分割会错把 <3.5 当成独立包）
#   - distro / charset_normalizer 是普通 pip 包（不是 p4a recipe），放 [app] requirements；
#     p4a 会通过 pip 装上
#   - Python 版本不是靠 bootstrap 名控制的（网上“sd12=Python 3.12”是误读）；
#     避免 3.14 问题的关键是 p4a.branch = master（见下）
requirements = python3,kivy,distro,charset_normalizer

# 强制 p4a 用 master 分支；buildozer 1.5.0 默认会拉 develop,
# develop 要求 hostpython3 3.14,其内置 pip 内部模块不匹配,会报 BuildDependencyInstallError
p4a.branch = master

# p4a bootstrap：合法取值仅 sdl2 / service_only / webview / qt 等，没有 sd12。
# sdl2 是安卓图形应用标准 bootstrap（Kivy 走 SDL2）。
p4a.bootstrap = sdl2

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
