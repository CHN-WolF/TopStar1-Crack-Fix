[中文](README.md) | **English**

# TopStar1 Crack Fix

A one-click binary patcher for `TopStar1`'s `Client.exe`, enabling COM1-free startup (no virtual serial port required) and loading custom song packs from the `Addsong` directory (including directory decryption, `infor.csv` fallback, and `NexioOpen` HUD / window-focus fixes).

- `一键生成Client.bat`: Reads `程序\Client.exe` (the imperfect cracked release from bemaniso), applies the patches, and generates `Client.exe` in the current folder (no need to place this folder inside the game directory; copy the generated `Client.exe` to your game directory).
- `脚本\apply_client_patches.py`: Main patching script (uses only the Python 3 standard library). Running it directly generates `Client.exe`.
- `程序\Client.exe`: Base executable included in this repository (the bemaniso cracked release, which has COM1 and custom-song issues fixed by this patcher).

See [USER_GUIDE.md](USER_GUIDE.md) for usage instructions and technical details.
