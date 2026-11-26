[中文](修改方法.md) | **English**

# TopStar1 Patching Guide

This folder can be placed anywhere—it **does not** need to be inside the game installation directory.

Directory layout:

```text
TopStar1-Crack-Fix\
  一键生成Client.bat
  Client.exe          (generated here; copy to your game root to replace the original Client.exe)
  程序\
    Client.exe        (imperfect cracked release from bemaniso; base binary, do not overwrite)
  脚本\
    apply_client_patches.py
  docs\
    README.md
    USER_GUIDE.md
```

Do not overwrite `程序\Client.exe` with the patched executable—`程序\Client.exe` is not the original unpatched binary, but the imperfect cracked release from **bemaniso** used as the base for this patcher.

`程序\Client.exe` is already included in this repository.

Python 3 is required. Double-click `一键生成Client.bat` (or run `python 脚本\apply_client_patches.py` directly). It patches from `程序\Client.exe` and outputs `Client.exe` in the current folder. Close the game first, then copy the generated `Client.exe` into your game root directory to overwrite the original `Client.exe`.

This patcher handles two things in one pass: booting without a `COM1` serial port, and loading custom songs from `Addsong`.

## Booting Without COM1

`Pack\config.pak` sets `IOBOARD_PORT` to `COM1`. Without a physical or virtual COM1 port, the game normally fails to start. With this patch, you no longer need virtual serial ports or `IO\io_emulator.py`.

Two places must be patched (patching only the first causes a black screen):

1. `CSerial::Create` at VA `0x44FDC0` (file offset `0x4FDC0`): originally starts with `53 8B 5C 24 08`. Patched to `B0 01 C2 04 00` (`mov al, 1; ret 4`) so it immediately reports success without calling `CreateFile`.
2. `CSerial::Update` write wait at VA `0x4504F8` (file offset `0x504F8`): originally `8B 0D 2C 36 5A 00`, which led into `GetOverlappedResult(..., bWait=TRUE)` and hung the main thread. Patched to `EB F3 90 90 90 90` to short-jump to `0x4504ED` (`xor al, al; ret 4`).

## Why Custom Songs Were Not Loaded

The game scans `Addsong` for `.pak` files, but three issues blocked them:

1. `ADDSONG_FROM_USB` was enabled in config, skipping local `addsong`. File offset `0x476BD` (`0F 84 FE 00 00 00`) is patched to `E9 FF 00 00 00 90` to always use the local `addsong` directory.
2. When one song's `info.csv` failed to open, the list loader aborted instead of skipping it. File offset `0x47C3E` (`74 12`) is patched to `90 90`.
3. Custom packs use a different directory-table decryption scheme than official packs (matching `extract_topstar1_pak.py`): official `config.pak` only needed entry `0`, whereas custom packs' `info.csv` is not entry `0`.

## Directory Decryption

Each directory entry is `0x98` bytes:

- Entry flag = header flag minus entry index (0-based).
- Instead of the fixed `ikey` table byte, the cave tests key bytes `0..255` using the game's own `0x458040` and `0x457FC0` routines and picks the first result that looks like a valid path (length >= 5, contains `\` and `.`, printable ASCII `0x20..0x7E`). If none matches, it falls back to the original `ikey` low byte so official packs keep working.
- Entry name sits at offset `0x0C` and matches `%s/info.csv` (lowercased, `/` normalized to `\`).

The code cave is placed at the end of `.ikey` starting at VA `0x683F00` (expanding `.ikey` virtual/raw sizes to `0x2000` aligned and `SizeOfImage` to `0x285000`). Scratch state bytes live in writable data:

| Address | Purpose |
| --- | --- |
| `0x681AD0` | Header flag |
| `0x681AD1` | Current entry index (reset per pack) |
| `0x681AD2` | Candidate key byte being tested |
| `0x681AD3` | Original fallback byte |
| `0x681AD4` | `infor.csv` retry flag |

Three hook sites:

| File Offset | Original | Cave Action |
| --- | --- | --- |
| `0x5845F` | Save flag and file position | Record header flag, reset index |
| `0x5851C` | Load `ikey` byte, `esi` = raw entry | Recover key byte, restore `esi` (`lea esi, [ebp+0x38]`) |
| `0x58529` | `cl = flag`, 0x26-round XOR | `cl = flag - index`, then increment index |

## Packs Using `infor.csv`

35 custom packs use `info.csv`, while 21 packs use `infor.csv`. File offset `0x47D80` jumps to `0x684030`: if `info.csv` is not found, it retries once with `%s/infor.csv` (VA `0x684018`).

## Never Ever

This pack's internal directory is `Never  Ever` (two spaces). Rename `Never Ever.pak` in `Addsong` to `Never  Ever.pak` (two spaces between `Never` and `Ever`) so the path matches.

## Result

Restart the game: all 27 original songs plus all 57 custom packs in `Addsong` (84 songs total) appear in the song list.
