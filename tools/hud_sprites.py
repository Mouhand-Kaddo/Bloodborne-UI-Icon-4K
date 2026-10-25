"""Maintainer tool. The HUD's Blood Vial and Quicksilver Bullet pictures (on MENU_Common_00091,
beside the button prompts) were only enlarged, not upscaled, in the 1.0.0 archive. This takes them
from the game's own 1x sheet, upscales 4x with Real-ESRGAN (realesrgan-x4plus), scales to 2x with
Lanczos (ffmpeg) and writes them into the 4K archive's 2x sheet.

    python tools/hud_sprites.py --archive payload/.../common.tpf.dcx --game <game folder> \
        --esrgan realesrgan-ncnn-vulkan.exe --ffmpeg ffmpeg.exe
"""
from pathlib import Path
import argparse, struct, subprocess, sys, tempfile, zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integration'))
import ui4k_assets as u  # noqa: E402

SHEET = 'MENU_Common_00091'
# On the 1x (1024x512) sheet: the area cropped for the upscaler, and inside it the area written
# back (both pictures with their frames; even coordinates, so whole blocks at 2x).
CROP = (752, 104, 872, 166)
WRITE = (754, 106, 870, 164)


def write_png(path, w, h, rgba):
    raw = b''.join(b'\0' + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def sheet_pixels(t, x0, y0, x1, y1):
    """RGBA of a pixel rectangle (block-aligned) of a BC7 texture."""
    wb, hb = t['w'] // 4, t['h'] // 4
    lin = u.deswizzle(t['data'], wb, hb, 16)
    w, h = x1 - x0, y1 - y0
    out = bytearray(w * h * 4)
    for by in range(y0 // 4, (y1 + 3) // 4):
        for bx in range(x0 // 4, (x1 + 3) // 4):
            o = (by * wb + bx) * 16
            for i, c in enumerate(u.bc7_decode_block(bytes(lin[o:o + 16]))):
                x, y = bx * 4 + i % 4 - x0, by * 4 + i // 4 - y0
                if 0 <= x < w and 0 <= y < h:
                    out[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes(c)
    return out


def apply(archive, game, esrgan, ffmpeg):
    _h, game_tpf = u.read_archive(Path(game) / 'dvdroot_ps4/menu/common.tpf.dcx')
    src = next(t for t in game_tpf['textures'] if t['name'] == SHEET)
    assert (src['w'], src['h'], src['dxgi']) == (1024, 512, 98), 'unexpected game sheet'
    header, tpf = u.read_archive(archive)
    dst = next(t for t in tpf['textures'] if t['name'] == SHEET)
    assert (dst['w'], dst['h'], dst['dxgi']) == (2048, 1024, 98), 'unexpected 4K sheet'
    cx0, cy0, cx1, cy1 = CROP
    # Block-aligned decode around the crop, then the crop itself.
    bx0, by0, bx1, by1 = cx0 // 4 * 4, cy0 // 4 * 4, (cx1 + 3) // 4 * 4, (cy1 + 3) // 4 * 4
    big = sheet_pixels(src, bx0, by0, bx1, by1); bw = bx1 - bx0
    cw, ch = cx1 - cx0, cy1 - cy0
    crop = bytearray()
    for y in range(ch):
        o = ((y + cy0 - by0) * bw + (cx0 - bx0)) * 4
        crop += big[o:o + cw * 4]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write_png(tmp / 'in.png', cw, ch, crop)
        subprocess.run([str(esrgan), '-i', str(tmp / 'in.png'), '-o', str(tmp / 'x4.png'), '-n', 'realesrgan-x4plus', '-s', '4'],
                       check=True, cwd=Path(esrgan).parent, capture_output=True)
        subprocess.run([str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(tmp / 'x4.png'),
                        '-vf', f'scale={cw * 2}:{ch * 2}:flags=lanczos', '-f', 'rawvideo', '-pix_fmt', 'rgba', str(tmp / 'x2.raw')],
                       check=True)
        up = (tmp / 'x2.raw').read_bytes()
    assert len(up) == cw * 2 * ch * 2 * 4
    uw = cw * 2
    wx0, wy0, wx1, wy1 = (v * 2 for v in WRITE)  # 2x pixel rectangle, multiples of 4
    assert all(v % 4 == 0 for v in (wx0, wy0, wx1, wy1))
    wb, hb = dst['w'] // 4, dst['h'] // 4
    lin = u.deswizzle(dst['data'], wb, hb, 16)
    for by in range(wy0 // 4, wy1 // 4):
        for bx in range(wx0 // 4, wx1 // 4):
            px = []
            for i in range(16):
                x = bx * 4 + i % 4 - cx0 * 2; y = by * 4 + i // 4 - cy0 * 2
                o = (y * uw + x) * 4
                px.append(tuple(up[o:o + 4]))
            o = (by * wb + bx) * 16
            lin[o:o + 16] = u.bc7_encode_block(px)
    dst['data'] = u.swizzle(lin, wb, hb, 16)
    Path(archive).write_bytes(u.dcx_pack(header, u.tpf_write(tpf), 9))
    return (wx1 - wx0) // 4 * (wy1 - wy0) // 4


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for name in ('--archive', '--game', '--esrgan', '--ffmpeg'):
        ap.add_argument(name, type=Path, required=True)
    a = ap.parse_args()
    print('blocks written:', apply(a.archive, a.game, a.esrgan, a.ffmpeg))
