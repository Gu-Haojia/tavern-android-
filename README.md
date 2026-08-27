# 🍻 酒馆 · 手机版（Kivy / APK）

把桌面酒馆版（`desktop-pet-tavern`）移植到安卓手机：**独立 APK，点开即用，手机直连 DeepSeek，不依赖电脑、不需要网页版**。

全部功能打包：世界书（关键词/正则触发）、互动小说模式（叙述引擎 + 选项按钮）、BM25 记忆 + 分页摘要压缩、角色卡导入、人设/世界观/玩家身份、示例对话、开场白、透明计费、气泡长按操作（编辑重发/删除/重新生成）、思维链展示。

---

## 🚀 云打包：全自动，只需你点几下

打包必须在 Linux 环境跑，公司电脑装不了 WSL，所以我们用 **GitHub Actions 云端打包**（免费，约 20~30 分钟）。

### 第 1 步：注册 GitHub（如已有跳过）
打开 https://github.com ，邮箱注册，免费。

### 第 2 步：新建私有仓库
1. 右上角 `+` → `New repository`
2. Repository name 填 `tavern-android`（或任意英文名）
3. 选 **Private**（私有，代码不会公开）
4. 不要勾选任何初始化选项（README/.gitignore 都不勾）→ `Create repository`

### 第 3 步：上传代码
1. 进入仓库页，点 `Add file` → `Upload files`
2. 把本文件夹（`tavern-android/`）里的**全部文件拖进去**：
   - `ai_core.py`
   - `main.py`
   - `buildozer.spec`
   - `.github/`（整个文件夹，里面是云端打包配置）
3. 底部 Commit 框填个名字（如 `init`）→ `Commit changes`

> 注意：`.github` 是隐藏文件夹，Windows 资源管理器可能看不到开头带点的文件夹——用 Git Bash 或文件管理器显示隐藏项确认它在上传列表里。上传时它必须和其余文件**同级**。如果拖不上去，用「Create new file」手建路径（见下方踩坑实录 #2）。

### 第 4 步：运行云端打包
1. 仓库页切到 **Actions** 页签
2. 左侧列表点 **Build APK**
3. 右侧点 **Run workflow** → 绿色按钮确认
4. 等待约 20~30 分钟（首次要下载 Android SDK/NDK，几 GB）

### 第 5 步：下载 APK
1. 打包完成后，Actions 页该次运行记录会显示绿色 ✓
2. 点进这次运行 → 底部 **Artifacts** → 下载 `tavern-apk`
3. 解压得到 `tavernpet-1.0.0-arm64-v8a-debug.apk`

### 第 6 步：装手机
1. 把 APK 传到手机（微信/网盘/数据线都行）
2. 手机允许「安装未知来源应用」
3. 安装 → 打开 → 右下角「⚙️ 设置」填 API Key（DeepSeek 等）→ 返回聊天

---

## 📱 手机使用

| 底部标签 | 功能 |
|---|---|
| 💬 聊天 | 对话；顶部「📖 小说」开关互动小说模式（AI 长叙事 + 末尾给选项按钮，点击即续写）；顶部「🔄」重新生成最后一条回复；**长按任一气泡**弹菜单（用户气泡：编辑并重新生成/删除；AI 气泡：重新生成/删除）；AI 回复下方灰色小字显示思维链（可观察 AI 是否入戏） |
| 📚 世界书 | 新增/编辑/删除世界书条目（关键词触发注入） |
| ⚙️ 设置 | API/模型/人设/世界观/玩家身份/示例对话/开场白/温度/各开关 |

- 记忆：聊到旧话题，AI 自动翻出相关旧对话（BM25）；跨会话长期记忆靠分页摘要压缩。
- 数据都存在手机 app 私有目录（卸载会清空；换机不迁移）。

## ⚠️ 常见问题

- **打包失败**：先对照下方「云打包踩坑实录」自查；解决不了就把 Actions 页的报错截图发我，按「走不通就停」约定处理。
- **聊天 401/报错**：多半是 API Key 没填对，检查设置页。
- **想改模型/人设**：在 ⚙️ 设置里改，保存后生效。
- **二次打包会快很多**：SDK/NDK 已缓存（Actions 里配了 cache）。

---

## 🧱 云打包踩坑实录（2026-08-26 实操验证）

这些坑都真实踩过并已修好，**当前仓库里的 `build.yml` 和 `buildozer.spec` 已是最终可用版**。以后重新打包若报错，先对照此表：

| # | 坑 | 报错特征 | 修复 |
|---|---|---|---|
| 1 | 新版 GitHub 空仓库没有 `Add file` 上传入口 | 只有 Quick setup 引导 | 浏览器直接开 `https://github.com/{你的用户名}/{仓库名}/upload/{分支}`（如 `/upload/main`） |
| 2 | `.github` 隐藏文件夹拖不上去 | 拖拽被拒绝（禁止点开头文件） | 先传普通文件；`.github/workflows/build.yml` 用 `Add file → Create new file`，文件名框直接输完整路径，GitHub 自动建目录 |
| 3 | 网页编辑器粘贴 YAML 后缩进错乱 | `Invalid workflow file`、某行缩进对不上 | workflow 用**极简版**：单行 `on: [workflow_dispatch]`、每步单行 `run:`、不用 `${{ }}` 表达式、不用多行块；粘贴用 `Ctrl+Shift+V`（纯文本） |
| 4 | `ubuntu-latest` 缺 `libtinfo5` | `E: Unable to locate package libtinfo5` | `runs-on: ubuntu-22.04`（24.04 移除了该包） |
| 5 | GStreamer 依赖冲突 | `libgstreamer1.0-dev : Depends: liborc-0.4-dev ...` | **删掉所有 libgstreamer 包**（buildozer 默认不需要） |
| 6 | buildozer.spec 缺版本号 | `One of "version" or "version.regex" must be set` | `[app]` 段加 `version = 0.1.0` |
| 7 | p4a 默认 Python 版本随 recipe 变化 | Python recipe 版本不一致或依赖安装失败 | 在 `[app] requirements` 中同时固定 `python3==3.12.14,hostpython3==3.12.14`；`p4a.bootstrap` 使用合法值 `sdl2` |
| 8 | distro 装不上（p4a 默认不打包） | `No matching distribution found for distro>=1.7.0` | `[app] requirements` 里**显式加** `distro` |
| 9 | **buildozer requirements 格式严格** | `Invalid requirement: '<3.5': Expected package name` | requirements 字段里**不要写版本约束**（`>=3.0,<3.5` 这种），buildozer 会按逗号错分成独立项；也**不要写 `python3.12`**（不是 pip 包名），Python 版本只能由 `[p4a] bootstrap` 控制 |

**核心经验**：网页编辑器对 YAML 复杂结构和隐藏文件不友好——要么用 GitHub Desktop（最稳），要么把 workflow 写极简。buildozer requirements 的通用解法是**只写包名、不要写版本约束**；包装不上就**显式列名**让它走 pip 拉。

---

## 文件清单

| 文件 | 作用 |
|---|---|
| `ai_core.py` | 纯 Python 内核（零依赖）：世界书/BM25/摘要/小说/流式调用/历史截断 |
| `main.py` | Kivy 移动端界面（聊天 + 长按气泡菜单 + 重新生成 + 思维链展示 + 世界书管理 + 设置） |
| `buildozer.spec` | APK 打包配置（sdl2 bootstrap；Python 3.12 recipe；distro/charset_normalizer 显式打包） |
| `.github/workflows/build.yml` | GitHub Actions 云端打包脚本（Ubuntu 22.04、缓存、手动/推送触发） |

桌面酒馆版（`desktop-pet-tavern/main.py`）未做任何改动；本目录是独立移植。
