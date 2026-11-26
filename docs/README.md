**中文** | [English](README_EN.md)

# TopStar1 Crack Fix

用于对 `TopStar1` 的 `Client.exe` 一键打补丁的工具：支持免串口（无需 COM1）启动游戏，以及读取 `Addsong` 目录下的自制歌曲包（含目录解密、`infor.csv` 兼容与 `NexioOpen` 状态/焦点修复）。

- `一键生成Client.bat`：读取 `程序\Client.exe`（基于 bemaniso 发布的不完美破解版），在当前文件夹下生成打好补丁的 `Client.exe`（无需将本工具放入游戏目录，生成后复制到游戏目录覆盖原文件即可）。
- `脚本\apply_client_patches.py`：补丁主脚本（仅依赖 Python 3 标准库），直接运行即可生成 `Client.exe`。
- `程序\Client.exe`：仓库自带的基础程序（为 bemaniso 发布的破解版，但存在串口与自制曲读取等问题，需配合本工具进一步修补）。

详细原理与操作步骤见 [修改方法.md](修改方法.md)。
