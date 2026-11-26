"""Replay every Client.exe patch from this repo's unpatched backup.

Source is 程序\\Client.exe (relative to the repo root). That file stays
unchanged. By default, writes the patched binary to Client.exe in the repo
root (no longer requires placing the folder inside the game directory).

Requires Python 3. Uses only the standard library.
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "程序" / "Client.exe"
TARGET = ROOT / "Client.exe"

IMAGE_BASE = 0x400000
DECRYPT_CAVE = 0x683F00
INFOR_CAVE = 0x684030
INFOR_FORMAT = 0x684018
HUD_CAVE = 0x684100
HUD_RETURN = 0x454E93
FALSE_STR = 0x565BE8
TRUE_STR = 0x565BF0
NEXIO_OBJECT = 0x5A33D8
IKEY_VA = 0x683000
IKEY_RAW = 0x192000

FLAG = 0x681AD0
INDEX = 0x681AD1
CANDIDATE = 0x681AD2
FALLBACK = 0x681AD3
RETRIED = 0x681AD4


def emit(buf, *raw):
    buf.extend(raw)


def build_decrypt_cave():
    """Directory decrypt: flag decreases per entry, key byte is recovered."""
    code = bytearray()
    labels = {}
    fixups = []

    def lab(name):
        labels[name] = len(code)

    def j8(op, name):
        emit(code, op, 0)
        fixups.append((len(code) - 1, "j8", name))

    def j32(op, name):
        emit(code, 0x0F, op, 0, 0, 0, 0)
        fixups.append((len(code) - 4, "j32", name))

    def call_abs(addr):
        emit(code, 0xE8, 0, 0, 0, 0)
        fixups.append((len(code) - 4, "call", addr))

    lab("store")
    emit(code, 0x88, 0x4C, 0x24, 0x1B)
    emit(code, 0x88, 0x0D, *FLAG.to_bytes(4, "little"))
    emit(code, 0xC6, 0x05, *INDEX.to_bytes(4, "little"), 0x00)
    emit(code, 0x89, 0x54, 0x24, 0x1C)
    emit(code, 0xC3)

    lab("load")
    emit(code, 0xA0, *FLAG.to_bytes(4, "little"))
    emit(code, 0x2A, 0x05, *INDEX.to_bytes(4, "little"))
    emit(code, 0x88, 0xC1)
    emit(code, 0xFE, 0x05, *INDEX.to_bytes(4, "little"))
    emit(code, 0x89, 0xF0)
    emit(code, 0xBE, 0x26, 0x00, 0x00, 0x00)
    emit(code, 0xC3)

    lab("pick")
    emit(code, 0x8B, 0x44, 0x18, 0x0C)
    emit(code, 0xA2, *FALLBACK.to_bytes(4, "little"))
    emit(code, 0x53, 0x57, 0x55)
    emit(code, 0x89, 0xE5)
    emit(code, 0x81, 0xEC, 0x40, 0x01, 0x00, 0x00)
    emit(code, 0xFC)
    # Address of the raw entry. lea, not mov: mov would read the ciphertext as a pointer.
    emit(code, 0x8D, 0x75, 0x38)
    emit(code, 0x89, 0xE7)
    emit(code, 0xB9, 0x98, 0x00, 0x00, 0x00)
    emit(code, 0xF3, 0xA4)
    emit(code, 0xC6, 0x05, *CANDIDATE.to_bytes(4, "little"), 0x00)

    lab("next")
    emit(code, 0x89, 0xE6)
    emit(code, 0x8D, 0xBC, 0x24, 0xA0, 0x00, 0x00, 0x00)
    emit(code, 0xB9, 0x98, 0x00, 0x00, 0x00)
    emit(code, 0xF3, 0xA4)
    emit(code, 0x8D, 0xB4, 0x24, 0xA0, 0x00, 0x00, 0x00)
    emit(code, 0x0F, 0xB6, 0x05, *CANDIDATE.to_bytes(4, "little"))
    call_abs(0x458040)
    emit(code, 0xA0, *FLAG.to_bytes(4, "little"))
    emit(code, 0x2A, 0x05, *INDEX.to_bytes(4, "little"))
    emit(code, 0x88, 0xC1)
    emit(code, 0xBF, 0x26, 0x00, 0x00, 0x00)
    emit(code, 0x89, 0xF0)
    lab("tloop")
    emit(code, 0x0F, 0xB6, 0xD1)
    emit(code, 0x8A, 0x92, 0x30, 0x63, 0x56, 0x00)
    emit(code, 0x30, 0x10)
    emit(code, 0x83, 0xC0, 0x04)
    emit(code, 0x80, 0xC1, 0x04)
    emit(code, 0x4F)
    j8(0x75, "tloop")
    emit(code, 0x31, 0xFF)
    lab("ks")
    emit(code, 0x8B, 0x0E)
    emit(code, 0x89, 0xFA)
    call_abs(0x457FC0)
    emit(code, 0x29, 0x44, 0xBE, 0x0C)
    emit(code, 0x47)
    emit(code, 0x83, 0xFF, 0x20)
    j8(0x72, "ks")
    emit(code, 0x8D, 0x46, 0x0C)
    emit(code, 0x31, 0xC9)
    emit(code, 0x31, 0xD2)
    lab("chk")
    emit(code, 0x8A, 0x18)
    emit(code, 0x84, 0xDB)
    j8(0x74, "endn")
    emit(code, 0x80, 0xFB, 0x20)
    j8(0x72, "bad")
    emit(code, 0x80, 0xFB, 0x7E)
    j8(0x77, "bad")
    emit(code, 0x80, 0xFB, 0x5C)
    j8(0x75, "nosl")
    emit(code, 0xB2, 0x01)
    lab("nosl")
    emit(code, 0x80, 0xFB, 0x2E)
    j8(0x75, "nodot")
    emit(code, 0xB6, 0x01)
    lab("nodot")
    emit(code, 0x41, 0x40)
    emit(code, 0x83, 0xF9, 0x70)
    j8(0x72, "chk")
    lab("endn")
    emit(code, 0x83, 0xF9, 0x05)
    j8(0x72, "bad")
    emit(code, 0x84, 0xD2)
    j8(0x74, "bad")
    emit(code, 0x84, 0xF6)
    j8(0x74, "bad")
    emit(code, 0x0F, 0xB6, 0x05, *CANDIDATE.to_bytes(4, "little"))
    j8(0xEB, "finish")
    lab("bad")
    emit(code, 0xFE, 0x05, *CANDIDATE.to_bytes(4, "little"))
    j32(0x85, "next")
    emit(code, 0xA0, *FALLBACK.to_bytes(4, "little"))
    lab("finish")
    emit(code, 0x0F, 0xB6, 0xC0)
    emit(code, 0x8D, 0x75, 0x38)
    emit(code, 0x89, 0xEC)
    emit(code, 0x5D, 0x5F, 0x5B, 0xC3)

    for at, kind, target in fixups:
        if kind == "j8":
            rel = labels[target] - (at + 1)
            if not -128 <= rel <= 127:
                raise SystemExit(f"short jump to {target} does not fit: {rel}")
            code[at] = rel & 0xFF
        elif kind == "j32":
            rel = labels[target] - (at + 4)
            code[at:at + 4] = rel.to_bytes(4, "little", signed=True)
        else:
            rel = target - (DECRYPT_CAVE + at + 4)
            code[at:at + 4] = rel.to_bytes(4, "little", signed=True)
    if DECRYPT_CAVE + len(code) > INFOR_FORMAT:
        raise SystemExit("decrypt cave overlaps the infor.csv format string")
    return code, labels


def build_infor_cave():
    """On an info.csv miss, look up stem/infor.csv once."""
    code = bytearray()
    labels = {}
    fixups = []

    def at(name):
        labels[name] = len(code)

    def jcc(op, name):
        emit(code, 0x0F, op)
        fixups.append((len(code), name))
        emit(code, 0, 0, 0, 0)

    def jmp(name):
        emit(code, 0xE9)
        fixups.append((len(code), name))
        emit(code, 0, 0, 0, 0)

    def absjmp(va):
        emit(code, 0xE9)
        fixups.append((len(code), va))
        emit(code, 0, 0, 0, 0)

    def call(va):
        emit(code, 0xE8)
        fixups.append((len(code), va))
        emit(code, 0, 0, 0, 0)

    emit(code, 0x83, 0xC4, 0x08)
    emit(code, 0x84, 0xC0)
    jcc(0x84, "miss")
    emit(code, 0xC6, 0x05, *RETRIED.to_bytes(4, "little"), 0)
    absjmp(0x447DD7)

    at("miss")
    emit(code, 0x80, 0x3D, *RETRIED.to_bytes(4, "little"), 0)
    jcc(0x85, "giveup")
    emit(code, 0xC6, 0x05, *RETRIED.to_bytes(4, "little"), 1)
    emit(code, 0x57)
    emit(code, 0xFF, 0x74, 0x24, 0x28)
    emit(code, 0x68, *INFOR_FORMAT.to_bytes(4, "little"))
    call(0x476770)
    emit(code, 0x83, 0xC4, 0x08)
    emit(code, 0x5F)
    emit(code, 0x8B, 0xC8)
    emit(code, 0x33, 0xD2)
    at("lenloop")
    emit(code, 0x80, 0x39, 0x00)
    jcc(0x84, "lendone")
    emit(code, 0x41)
    emit(code, 0x42)
    jmp("lenloop")
    at("lendone")
    emit(code, 0x52)
    emit(code, 0x50)
    emit(code, 0x8D, 0x8C, 0x24, 0xA4, 0x00, 0x00, 0x00)
    call(0x4038C0)
    absjmp(0x447D59)

    at("giveup")
    emit(code, 0xC6, 0x05, *RETRIED.to_bytes(4, "little"), 0)
    absjmp(0x447D87)

    for pos, target in fixups:
        dest = INFOR_CAVE + labels[target] if isinstance(target, str) else target
        rel = dest - (INFOR_CAVE + pos + 4)
        code[pos:pos + 4] = rel.to_bytes(4, "little", signed=True)
    return code


def build_hud_cave():
    """NexioOpen(%s) always pushed "false". Push "true" when the device flag is set."""
    code = bytearray()

    def emit(*raw):
        code.extend(raw)

    emit(0x50)
    emit(0x51)
    emit(0xB8, *FALSE_STR.to_bytes(4, "little"))
    emit(0x8B, 0x0D, *NEXIO_OBJECT.to_bytes(4, "little"))
    emit(0x85, 0xC9)
    jz_null = len(code)
    emit(0x74, 0)
    emit(0x80, 0x79, 0x0C, 0x00)
    jz_closed = len(code)
    emit(0x74, 0)
    emit(0xB8, *TRUE_STR.to_bytes(4, "little"))
    opened = len(code)
    code[jz_null + 1] = opened - (jz_null + 2)
    code[jz_closed + 1] = opened - (jz_closed + 2)
    emit(0x89, 0xC1)
    emit(0x58)
    emit(0x91)
    emit(0x87, 0x04, 0x24)
    jmp_at = len(code)
    emit(0xE9, 0, 0, 0, 0)
    rel = HUD_RETURN - (HUD_CAVE + jmp_at + 5)
    code[jmp_at + 1:jmp_at + 5] = rel.to_bytes(4, "little", signed=True)
    return code


def put_call(data, file_off, size, dest):
    rel = (dest - (IMAGE_BASE + file_off + 5)).to_bytes(4, "little", signed=True)
    data[file_off:file_off + size] = b"\xE8" + rel + b"\x90" * (size - 5)


def extend_ikey(data, end_va):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    file_align = struct.unpack_from("<I", data, pe + 24 + 36)[0]
    sect_align = struct.unpack_from("<I", data, pe + 24 + 32)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    sec = pe + 24 + opt
    ikey = None
    for i in range(nsec):
        off = sec + i * 40
        if data[off:off + 6] == b".ikey\x00":
            ikey = off
    if ikey is None:
        raise SystemExit(".ikey section not found")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, ikey + 8)
    if (va, rawptr, rawsize) != (0x283000, IKEY_RAW, 0x1000):
        raise SystemExit("unexpected .ikey section; source is not the unpatched backup")
    need = end_va - IKEY_VA
    need_raw = (need + file_align - 1) & ~(file_align - 1)
    data.extend(b"\x00" * (need_raw - rawsize))
    struct.pack_into("<I", data, ikey + 8, need)
    struct.pack_into("<I", data, ikey + 16, need_raw)
    image_end = (IMAGE_BASE + va + need + sect_align - 1) & ~(sect_align - 1)
    struct.pack_into("<I", data, pe + 24 + 56, image_end - IMAGE_BASE)


def patched_image():
    if not SOURCE.is_file():
        raise SystemExit(f"missing unpatched backup: {SOURCE}")
    data = bytearray(SOURCE.read_bytes())

    def replace(off, old, new):
        found = bytes(data[off:off + len(old)])
        if found != old:
            raise SystemExit(f"offset {off:#x} is {found.hex()}, expected {old.hex()}")
        data[off:off + len(new)] = new

    # Packed config says ADDSONG_FROM_USB. Always take the local addsong folder.
    replace(0x476BD, bytes.fromhex("0f84fe000000"), bytes.fromhex("e9ff00000090"))
    # Packed config asks for COM1. CSerial::Create returns success without opening it.
    # The later WriteFile path treats error 0 as pending and blocks in GetOverlappedResult.
    # Skip that wait too, or the window stays black.
    replace(0x4FDC0, bytes.fromhex("538b5c2408"), bytes.fromhex("b001c20400"))
    replace(0x504F8, bytes.fromhex("8b0d2c365a00"), bytes.fromhex("ebf390909090"))
    # One bad pak must not abort the rest of Addsong.
    replace(0x47C3E, bytes.fromhex("7412"), bytes.fromhex("9090"))
    # First touch often arrives while GetForegroundWindow is not the saved hwnd.
    # That path forces every key to state 5 and ignores the press until a second tap.
    replace(0x68B16, bytes.fromhex("740c"), bytes.fromhex("eb0c"))

    decrypt, labels = build_decrypt_cave()
    put_call(data, 0x5845F, 8, DECRYPT_CAVE + labels["store"])
    put_call(data, 0x5851C, 8, DECRYPT_CAVE + labels["pick"])
    put_call(data, 0x58529, 11, DECRYPT_CAVE + labels["load"])

    infor = build_infor_cave()
    hud = build_hud_cave()
    if INFOR_CAVE + len(infor) > HUD_CAVE:
        raise SystemExit("infor cave overlaps the NexioOpen cave")
    end_va = HUD_CAVE + len(hud)
    extend_ikey(data, end_va)
    fmt_off = IKEY_RAW + (INFOR_FORMAT - IKEY_VA)
    data[fmt_off:fmt_off + 13] = b"%s/infor.csv\x00"
    cave_off = IKEY_RAW + (DECRYPT_CAVE - IKEY_VA)
    data[cave_off:cave_off + len(decrypt)] = decrypt
    infor_off = IKEY_RAW + (INFOR_CAVE - IKEY_VA)
    data[infor_off:infor_off + len(infor)] = infor
    hook = 0x47D80
    rel = (INFOR_CAVE - (IMAGE_BASE + hook + 5)).to_bytes(4, "little", signed=True)
    replace(hook, bytes.fromhex("83c40884c07550"), b"\xE9" + rel + b"\x90\x90")
    hud_off = IKEY_RAW + (HUD_CAVE - IKEY_VA)
    data[hud_off:hud_off + len(hud)] = hud
    rel = (HUD_CAVE - (IMAGE_BASE + 0x54E8E + 5)).to_bytes(4, "little", signed=True)
    replace(0x54E8E, bytes.fromhex("68e85b5600"), b"\xE9" + rel)
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description="Replay the TopStar1 Client.exe patches.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the patched image (default behavior, kept for compatibility)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only check whether the target matches the patched image without writing",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=TARGET,
        help=f"output path for the patched Client.exe (default: {TARGET})",
    )
    args = parser.parse_args()
    target = args.output
    image = patched_image()
    if target.is_file() and target.read_bytes() == image:
        print(f"matches {target}")
    else:
        print(f"differs from {target} ({len(image)} bytes)")
    if not args.check or args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image)
        print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
