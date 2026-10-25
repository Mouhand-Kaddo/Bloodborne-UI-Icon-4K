# SPDX-License-Identifier: GPL-2.0-or-later
"""Bloodborne UI 4K: game files made at launch for the bbport version in use.

Two kinds of files are made into the mod's own dvdroot_ps4 folder each time the game starts
(and only remade when an input changes):

* Menu movies (menu/*.gfx). The package ships the UI 4K copies only as references. Each movie
  is rebuilt from the copy the game would otherwise use (the port's generated PC menu, HUD
  layout or language files, other mods below this one, or the game's own), with UI 4K's image
  and shape records put in: the doubled image sizes and the halved bitmap-fill scales. A record
  is replaced only where the base still has the game's original one, so the port's own edits
  (PC menu rows, Quit Game, ultrawide layout) are kept. Bitmap fills are then made smoothed:
  the game's movies mark almost all of them non-smoothed (nearest-pixel sampling), exact at
  1080p but stair-stepped at any other size.
* The interface archive (menu/common.tpf.dcx): the 4K archive with the button prompts of the
  prompt set in use (the topmost other mod with its own common.tpf.dcx, such as the Xbox
  prompts, or the game's PlayStation prompts). The keyboard prompts (PCBButtons) keep the
  package's upscaled images.
"""
from pathlib import Path
import hashlib, json, struct, sys, zlib

MOD_NAME = 'UI 4K'
DATA_FOLDER = 'ui4k'            # inside the mod folder; the loader ignores files outside dvdroot_ps4
ARCHIVE = 'dvdroot_ps4/menu/common.tpf.dcx'
STAMP = 'generated.json'
IDENTITY = 'ui4k-assets 4'


# ---------------------------------------------------------------------------------------------
# DCX (DFLT) and TPF (PS4)

def dcx_unpack(raw):
    if raw[:4] != b'DCX\0' or raw[0x18:0x1c] != b'DCS\0' or raw[0x28:0x2c] != b'DFLT':
        raise ValueError('not a DFLT DCX file')
    usize, csize = struct.unpack_from('>II', raw, 0x1c)
    dca = raw.index(b'DCA\0', 0x2c)
    start = dca + struct.unpack_from('>I', raw, dca + 4)[0]
    data = zlib.decompress(raw[start:start + csize])
    if len(data) != usize:
        raise ValueError('DCX size mismatch')
    return raw[:start], data


def dcx_pack(header, data, level=6):
    comp = zlib.compress(data, level)
    head = bytearray(header)
    struct.pack_into('>II', head, 0x1c, len(data), len(comp))
    return bytes(head) + comp


def tpf_read(data):
    if data[:4] != b'TPF\0':
        raise ValueError('not a TPF file')
    count = struct.unpack_from('<I', data, 8)[0]
    platform, flag2, encoding, unk = data[12:16]
    if platform != 4:
        raise ValueError(f'TPF platform {platform} is not PS4')
    textures = []
    for k in range(count):
        at = 16 + 36 * k
        off, size, fmt, kind, mips, flags1, w, h, tcount, unk2, name_at, flags2, dxgi = \
            struct.unpack_from('<IIBBBBHHiiIii', data, at)
        if flags2 != 0:
            raise ValueError('TPF float structs are unsupported')
        if encoding == 1:
            end = name_at
            while data[end:end + 2] != b'\0\0':
                end += 2
            name = data[name_at:end].decode('utf-16le')
        else:
            name = data[name_at:data.index(b'\0', name_at)].decode('shift_jis')
        textures.append(dict(name=name, fmt=fmt, kind=kind, mips=mips, flags1=flags1, w=w, h=h,
                             tcount=tcount, unk2=unk2, dxgi=dxgi, data=data[off:off + size]))
    return dict(platform=platform, flag2=flag2, encoding=encoding, unk=unk, textures=textures)


def tpf_write(tpf):
    textures = tpf['textures']
    body = bytearray(b'TPF\0' + struct.pack('<II', 0, len(textures)) +
                     bytes([tpf['platform'], tpf['flag2'], tpf['encoding'], tpf['unk']]))
    entries = len(body)
    body += bytes(36 * len(textures))
    name_at = []
    for t in textures:
        name_at.append(len(body))
        body += t['name'].encode('utf-16le') + b'\0\0' if tpf['encoding'] == 1 else \
            t['name'].encode('shift_jis') + b'\0'
    while len(body) % 16:
        body += b'\0'
    data_start = len(body)
    offsets = []
    for t in textures:
        while len(body) % 16:
            body += b'\0'
        offsets.append(len(body))
        body += t['data']
    for k, t in enumerate(textures):
        struct.pack_into('<IIBBBBHHiiIii', body, entries + 36 * k, offsets[k], len(t['data']), t['fmt'],
                         t['kind'], t['mips'], t['flags1'], t['w'], t['h'], t['tcount'], t['unk2'],
                         name_at[k], 0, t['dxgi'])
    struct.pack_into('<I', body, 4, len(body) - data_start)
    return bytes(body)


def read_archive(path):
    header, data = dcx_unpack(Path(path).read_bytes())
    return header, tpf_read(data)


# The button prompt images: the key guide (KG_*), replaced whole, and the HUD sheet
# MENU_Common_00091, which has the O / X / L3 buttons beside HUD art of its own (bars, the Blood
# Vial and Quicksilver Bullet pictures, status icons). Only the buttons' rectangle is taken from
# a prompt mod; the rest of that sheet stays UI 4K's. Rectangles are fractions of the sheet's size
# (x0, y0, x1, y1), from the original 1024x512 sheet: x 656-752, y 112-160.
PROMPT_TEXTURES = ('KG_Cancel', 'KG_L1', 'KG_L2', 'KG_L3', 'KG_LS', 'KG_L_D', 'KG_L_LR', 'KG_L_U',
                   'KG_L_UD', 'KG_L_UDLR', 'KG_OK', 'KG_R1', 'KG_R2', 'KG_R3', 'KG_RS', 'KG_R_L',
                   'KG_R_U', 'KG_Start', 'KG_TP_L', 'KG_TP_R')
PROMPT_REGIONS = {'MENU_Common_00091': [(656 / 1024, 112 / 512, 752 / 1024, 160 / 512)]}
# What identifies a prompt set (prompts.json keyboard_source was made over these).
DIGEST_TEXTURES = PROMPT_TEXTURES + ('MENU_Common_00091',)


def prompt_digest(tpf):
    by_name = {t['name']: t for t in tpf['textures']}
    digest = hashlib.sha256()
    for name in DIGEST_TEXTURES:
        t = by_name[name]
        digest.update(name.encode() + struct.pack('<HHi', t['w'], t['h'], t['dxgi']) + t['data'])
    return digest.hexdigest()


# PS4 tiling: blocks in 8x8-block tiles, Morton order inside a tile, tiles row-major.
MORTON = []
for _i in range(64):
    _x = _y = 0
    for _b in range(3):
        _x |= ((_i >> (2 * _b)) & 1) << _b
        _y |= ((_i >> (2 * _b + 1)) & 1) << _b
    MORTON.append((_x, _y))


def deswizzle(data, wb, hb, bpb):
    out = bytearray(wb * hb * bpb)
    src = 0
    for ty in range((hb + 7) // 8):
        for tx in range((wb + 7) // 8):
            for mx, my in MORTON:
                x, y = tx * 8 + mx, ty * 8 + my
                if x < wb and y < hb:
                    d = (y * wb + x) * bpb
                    out[d:d + bpb] = data[src:src + bpb]
                src += bpb
    return out


def swizzle(linear, wb, hb, bpb):
    out = bytearray(((wb + 7) // 8) * ((hb + 7) // 8) * 64 * bpb)
    dst = 0
    for ty in range((hb + 7) // 8):
        for tx in range((wb + 7) // 8):
            for mx, my in MORTON:
                x, y = tx * 8 + mx, ty * 8 + my
                if x < wb and y < hb:
                    s = (y * wb + x) * bpb
                    out[dst:dst + bpb] = linear[s:s + bpb]
                dst += bpb
    return bytes(out)


# BC7: a full decoder (any mode), and a mode-6 encoder for the few blocks made here.
_W = {2: [0, 21, 43, 64], 3: [0, 9, 18, 27, 37, 46, 55, 64], 4: [0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64]}
_P2 = [0xcccc, 0x8888, 0xeeee, 0xecc8, 0xc880, 0xfeec, 0xfec8, 0xec80, 0xc800, 0xffec, 0xfe80, 0xe800, 0xffe8, 0xff00, 0xfff0, 0xf000,
       0xf710, 0x008e, 0x7100, 0x08ce, 0x008c, 0x7310, 0x3100, 0x8cce, 0x088c, 0x3110, 0x6666, 0x366c, 0x17e8, 0x0ff0, 0x718e, 0x399c,
       0xaaaa, 0xf0f0, 0x5a5a, 0x33cc, 0x3c3c, 0x55aa, 0x9696, 0xa55a, 0x73ce, 0x13c8, 0x324c, 0x3bdc, 0x6996, 0xc33c, 0x9966, 0x0660,
       0x0272, 0x04e4, 0x4e40, 0x2720, 0xc936, 0x936c, 0x39c6, 0x639c, 0x9336, 0x9cc6, 0x817e, 0xe718, 0xccf0, 0x0fcc, 0x7744, 0xee22]
_P3 = ['0011001122112221', '0001001122112221', '0000200122112211', '0222002200110111', '0000000011221122', '0011001100220022',
       '0022002211111111', '0011001122112211', '0000000011112222', '0000111111112222', '0000111122222222', '0012001200120012',
       '0112011201120112', '0122012201220122', '0011011211221222', '0011200122002220', '0001001101121122', '0111001120012200',
       '0000112211221122', '0022002200221111', '0111011102220222', '0001000122212221', '0000001101220122', '0000110022102210',
       '0122012200110000', '0012001211221122', '0110122112210110', '0000011012211221', '0022110211020022', '0110011020022222',
       '0011012201220011', '0000200022112221', '0000000111211122', '0222002200120011', '0011001200220222', '0120012001200120',
       '0000111122220000', '0120120120120120', '0120201212010120', '0011220011220011', '0011112222000011', '0101010122222222',
       '0000000021212121', '0022112200221122', '0022001100220011', '0220122102201221', '0101222222220101', '0000212121212121',
       '0101010101012222', '0222011102220111', '0002111200021112', '0000211221122112', '0222011101110222', '0002111211120002',
       '0110011001102222', '0000000021122112', '0110011022222222', '0022001100110022', '0022112211220022', '0000000000002112',
       '0002000100020001', '0222122202221222', '0101222222222222', '0111201122012220']
_A2 = [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 2, 8, 2, 2, 8, 8, 15, 2, 8, 2, 2, 8, 8, 2, 2,
       15, 15, 6, 8, 2, 8, 15, 15, 2, 8, 2, 2, 2, 15, 15, 6, 6, 2, 6, 8, 15, 15, 2, 2, 15, 15, 15, 15, 15, 2, 2, 15]
_A3A = [3, 3, 15, 15, 8, 3, 15, 15, 8, 8, 6, 6, 6, 5, 3, 3, 3, 3, 8, 15, 3, 3, 6, 10, 5, 8, 8, 6, 8, 5, 15, 15,
        8, 15, 3, 5, 6, 10, 8, 15, 15, 3, 15, 5, 15, 15, 15, 15, 3, 15, 5, 5, 5, 8, 5, 10, 5, 10, 8, 13, 15, 12, 3, 3]
_A3B = [15, 8, 8, 3, 15, 15, 3, 8, 15, 15, 15, 15, 15, 15, 15, 8, 15, 8, 15, 3, 15, 8, 15, 8, 3, 15, 6, 10, 15, 15, 10, 8,
        15, 3, 15, 10, 10, 8, 9, 10, 6, 15, 8, 15, 3, 6, 6, 8, 15, 3, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 3, 15, 15, 8]
# subsets, partition bits, rotation bits, index-select bits, colour bits, alpha bits, endpoint p-bits,
# shared p-bits, index bits, second index bits
_MODES = {0: (3, 4, 0, 0, 4, 0, 1, 0, 3, 0), 1: (2, 6, 0, 0, 6, 0, 0, 1, 3, 0), 2: (3, 6, 0, 0, 5, 0, 0, 0, 2, 0),
          3: (2, 6, 0, 0, 7, 0, 1, 0, 2, 0), 4: (1, 0, 2, 1, 5, 6, 0, 0, 2, 3), 5: (1, 0, 2, 0, 7, 8, 0, 0, 2, 2),
          6: (1, 0, 0, 0, 7, 7, 1, 0, 4, 0), 7: (2, 6, 0, 0, 5, 5, 1, 0, 2, 0)}


def bc7_decode_block(block):
    """16 RGBA pixels of one BC7 block."""
    v = int.from_bytes(block, 'little'); pos = 0

    def bits(n):
        nonlocal pos
        r = (v >> pos) & ((1 << n) - 1); pos += n
        return r
    mode = 0
    while mode < 8 and not bits(1):
        mode += 1
    if mode == 8:
        return [(0, 0, 0, 0)] * 16
    ns, pb, rb, isb, cb, ab, epb, spb, ib, ib2 = _MODES[mode]
    part = bits(pb); rot = bits(rb); isel = bits(isb); ne = ns * 2
    col = [[bits(cb) for _ in range(ne)] for _ in range(3)]
    alp = [bits(ab) for _ in range(ne)] if ab else None
    if epb:
        p = [bits(1) for _ in range(ne)]
    elif spb:
        p = [bits(1) for _ in range(ns)]; p = [p[i // 2] for i in range(ne)]
    else:
        p = None

    def expand(x, n, e):
        if p is not None:
            x = (x << 1) | p[e]; n += 1
        return (x << (8 - n)) | (x >> (2 * n - 8)) if n < 8 else x
    eps = [[expand(col[c][e], cb, e) for c in range(3)] + [expand(alp[e], ab, e) if alp else 255] for e in range(ne)]
    if ns == 1:
        sub = [0] * 16; anchors = [0]
    elif ns == 2:
        sub = [(_P2[part] >> i) & 1 for i in range(16)]; anchors = [0, _A2[part]]
    else:
        sub = [int(c) for c in _P3[part]]; anchors = [0, _A3A[part], _A3B[part]]
    idx = [bits(ib - (1 if i in anchors and anchors.index(i) == sub[i] else 0)) for i in range(16)]
    idx2 = [bits(ib2 - (1 if i == 0 else 0)) for i in range(16)] if ib2 else None
    out = []
    for i in range(16):
        e0, e1 = eps[2 * sub[i]], eps[2 * sub[i] + 1]
        if idx2:
            ci, ai = (idx2[i], idx[i]) if isel else (idx[i], idx2[i])
            wc = _W[ib2 if isel else ib][ci]; wa = _W[ib if isel else ib2][ai]
        else:
            wc = wa = _W[ib][idx[i]]
        px = [((64 - wc) * e0[k] + wc * e1[k] + 32) >> 6 for k in range(3)] + [((64 - wa) * e0[3] + wa * e1[3] + 32) >> 6]
        if rot:
            px[rot - 1], px[3] = px[3], px[rot - 1]
        out.append(tuple(px))
    return out


def bc7_encode_block(px):
    """One BC7 mode-6 block (one subset, 7-bit RGBA endpoints with p-bits, 4-bit indices) for 16
    RGBA pixels: endpoints at the colour bounding box, each pixel projected onto that line."""
    def endpoint(vals):
        best = None
        for p in (0, 1):
            qs = [max(0, min(127, (v - p + 1) // 2)) for v in vals]
            err = sum(abs(((q << 1) | p) - v) for q, v in zip(qs, vals))
            if best is None or err < best[0]:
                best = (err, qs, p)
        return best[1], best[2]
    q0, p0 = endpoint([min(c[k] for c in px) for k in range(4)])
    q1, p1 = endpoint([max(c[k] for c in px) for k in range(4)])
    e0 = [(q << 1) | p0 for q in q0]; e1 = [(q << 1) | p1 for q in q1]
    d = [b - a for a, b in zip(e0, e1)]; dd = sum(x * x for x in d) or 1
    weights = _W[4]
    idx = []
    for c in px:
        w = max(0.0, min(1.0, sum((c[k] - e0[k]) * d[k] for k in range(4)) / dd)) * 64
        idx.append(min(range(16), key=lambda i: abs(weights[i] - w)))
    if idx[0] >= 8:  # the anchor index has 3 bits: swap the endpoints
        q0, q1, p0, p1 = q1, q0, p1, p0
        idx = [15 - i for i in idx]
    v = 1 << 6; pos = 7
    for k in range(4):
        v |= q0[k] << pos; pos += 7
        v |= q1[k] << pos; pos += 7
    v |= p0 << pos; v |= p1 << (pos + 1); pos += 2
    for i, x in enumerate(idx):
        v |= x << pos; pos += 3 if i == 0 else 4
    return v.to_bytes(16, 'little')


def paste_region(base, source, rect):
    """`base` texture data with the fractional `rect` taken from `source` (both BC7). The same
    size copies the blocks; a source half the size (the game's own 1x sheet) is enlarged 2x with
    bilinear filtering and encoded. Returns the new data, or None when the sizes do not fit."""
    if base['dxgi'] != 98 or source['dxgi'] != 98:
        return None
    bw, bh = base['w'] // 4, base['h'] // 4
    x0, y0, x1, y1 = (round(rect[0] * bw), round(rect[1] * bh), round(rect[2] * bw), round(rect[3] * bh))
    lin = deswizzle(base['data'], bw, bh, 16)
    if (source['w'], source['h']) == (base['w'], base['h']):
        src = deswizzle(source['data'], bw, bh, 16)
        for y in range(y0, y1):
            o = (y * bw + x0) * 16
            lin[o:(y * bw + x1) * 16] = src[o:(y * bw + x1) * 16]
    elif (source['w'] * 2, source['h'] * 2) == (base['w'], base['h']):
        sw, sh = source['w'] // 4, source['h'] // 4
        src = deswizzle(source['data'], sw, sh, 16)
        # Source pixels of the rectangle (plus a 1-pixel border for the filter).
        px0, py0, px1, py1 = x0 * 2 - 1, y0 * 2 - 1, x1 * 2 + 1, y1 * 2 + 1
        rows = {}
        for by in range(max(0, py0 // 4), min(sh, (py1 + 3) // 4)):
            for bx in range(max(0, px0 // 4), min(sw, (px1 + 3) // 4)):
                o = (by * sw + bx) * 16
                for i, c in enumerate(bc7_decode_block(bytes(src[o:o + 16]))):
                    rows[(bx * 4 + i % 4, by * 4 + i // 4)] = c

        xs = [k[0] for k in rows]; ys = [k[1] for k in rows]
        lox, hix, loy, hiy = min(xs), max(xs), min(ys), max(ys)

        def get(x, y):
            return rows[(min(hix, max(lox, x)), min(hiy, max(loy, y)))]

        def sample(fx, fy):  # bilinear in source pixels
            ix, iy = int(fx // 1), int(fy // 1); tx, ty = fx - ix, fy - iy
            a, b, c, d = get(ix, iy), get(ix + 1, iy), get(ix, iy + 1), get(ix + 1, iy + 1)
            return tuple(round(a[k] * (1 - tx) * (1 - ty) + b[k] * tx * (1 - ty) + c[k] * (1 - tx) * ty + d[k] * tx * ty)
                         for k in range(4))
        for by in range(y0, y1):
            for bx in range(x0, x1):
                px = [sample((bx * 4 + i % 4 + 0.5) / 2 - 0.5, (by * 4 + i // 4 + 0.5) / 2 - 0.5) for i in range(16)]
                o = (by * bw + bx) * 16
                lin[o:o + 16] = bc7_encode_block(px)
    else:
        return None
    return swizzle(lin, bw, bh, 16)


def with_prompts(base, source):
    """`base` (the 4K archive) with the prompt images of `source`: the key guide textures whole
    (each keeps its own size: the movies give the key guide 64x64 and the game samples a smaller
    image over the same area), and only the buttons' rectangle of the HUD sheet."""
    by_name = {t['name']: t for t in source['textures']}
    out = dict(base, textures=[])
    for t in base['textures']:
        if t['name'] in PROMPT_TEXTURES:
            t = dict(by_name[t['name']])
        elif t['name'] in PROMPT_REGIONS and t['name'] in by_name:
            data = t['data']
            for rect in PROMPT_REGIONS[t['name']]:
                data = paste_region(dict(t, data=data), by_name[t['name']], rect) or data
            t = dict(t, data=data)
        out['textures'].append(t)
    return out


# ---------------------------------------------------------------------------------------------
# Scaleform GFX movies

def gfx_tags(data):
    if data[:3] not in (b'GFX', b'FWS'):
        raise ValueError('not an uncompressed GFX movie')
    bits = data[8] >> 3
    at = 8 + (5 + 4 * bits + 7) // 8 + 4
    head, tags = data[:at], []
    while at < len(data):
        word = struct.unpack_from('<H', data, at)[0]
        code, size, skip = word >> 6, word & 0x3f, 2
        if size == 0x3f:
            size, skip = struct.unpack_from('<I', data, at + 2)[0], 6
        tags.append((code, data[at + skip:at + skip + size], skip == 6))
        at += skip + size
        if code == 0:
            break
    return head, tags


def gfx_write(head, tags):
    out = bytearray(head)
    for code, body, long in tags:
        # Each record keeps the header form it had (Flash needs the long one for some tags).
        if len(body) < 0x3f and not long:
            out += struct.pack('<H', code << 6 | len(body))
        else:
            out += struct.pack('<HI', code << 6 | 0x3f, len(body))
        out += body
    struct.pack_into('<I', out, 4, len(out))
    return bytes(out)


# The records UI 4K changes: external images (GFx DefineExternalImage2) and shapes with bitmap fills.
IMAGE_TAGS = {1009: 4}
SHAPE_TAGS = {2: 2, 22: 2, 32: 2, 83: 2}


def record_key(code, body):
    width = IMAGE_TAGS.get(code) or SHAPE_TAGS.get(code)
    return (code, body[:width]) if width and len(body) >= width else None


def scale_movie(base, reference, original):
    """`base` with each image/shape record of `reference` (UI 4K's copy of the game's movie
    `original`) where `base` still has the game's own record. Returns (movie, records replaced)."""
    head, tags = gfx_tags(base)
    ref = {record_key(c, b): (b, l) for c, b, l in gfx_tags(reference)[1] if record_key(c, b)}
    orig = {record_key(c, b): b for c, b, _l in gfx_tags(original)[1] if record_key(c, b)}
    out, replaced = [], 0
    for code, body, long in tags:
        key = record_key(code, body)
        if key and key in ref and orig.get(key) == body and ref[key][0] != body:
            body, long = ref[key]
            replaced += 1
        out.append((code, body, long))
    return gfx_write(head, out), replaced


# Shape records: where each bitmap fill's type byte is, to turn non-smoothed fills (0x42/0x43,
# nearest-pixel) into smoothed ones (0x40/0x41, bilinear) in place.

class Bits:
    def __init__(self, b, pos=0):
        self.b, self.byte, self.bit = b, pos, 0

    def align(self):
        if self.bit:
            self.byte += 1; self.bit = 0

    def ub(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.b[self.byte] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8:
                self.bit = 0; self.byte += 1
        return v

    def u8(self):
        self.align(); v = self.b[self.byte]; self.byte += 1; return v

    def u16(self):
        self.align(); v = self.b[self.byte] | self.b[self.byte + 1] << 8; self.byte += 2; return v


def rect(r):
    r.align(); n = r.ub(5); r.ub(4 * n); r.align()


def matrix(r):
    r.align()
    if r.ub(1):
        n = r.ub(5); r.ub(2 * n)
    if r.ub(1):
        n = r.ub(5); r.ub(2 * n)
    n = r.ub(5); r.ub(2 * n); r.align()


def gradient(r, version, focal):
    flags = r.u8(); count = flags & 15
    r.byte += count * (1 + (4 if version >= 3 else 3))
    if focal:
        r.byte += 2


def fill_styles(r, version, found):
    count = r.u8()
    if count == 0xFF and version >= 2:
        count = r.u16()
    for _ in range(count):
        at = r.byte; kind = r.u8()
        if kind == 0x00:
            r.byte += 4 if version >= 3 else 3
        elif kind in (0x10, 0x12, 0x13):
            matrix(r); gradient(r, version, kind == 0x13)
        elif kind in (0x40, 0x41, 0x42, 0x43):
            found.append((at, kind)); r.byte += 2; matrix(r)
        else:
            raise ValueError(f'fill style {kind:#x}')


def line_styles(r, version, found):
    count = r.u8()
    if count == 0xFF:
        count = r.u16()
    for _ in range(count):
        if version == 4:
            r.byte += 2  # width
            r.align(); r.ub(2); join = r.ub(2); has_fill = r.ub(1); r.ub(11)  # 16 flag bits
            if join == 2:
                r.byte += 2
            if has_fill:
                fill_styles_one(r, version, found)
            else:
                r.byte += 4
        else:
            r.byte += 2 + (4 if version >= 3 else 3)


def fill_styles_one(r, version, found):
    at = r.byte; kind = r.u8()
    if kind == 0x00:
        r.byte += 4
    elif kind in (0x10, 0x12, 0x13):
        matrix(r); gradient(r, version, kind == 0x13)
    elif kind in (0x40, 0x41, 0x42, 0x43):
        found.append((at, kind)); r.byte += 2; matrix(r)
    else:
        raise ValueError(f'fill style {kind:#x}')


VERSIONS = {2: 1, 22: 2, 32: 3, 83: 4}


def bitmap_fills(code, body):
    """[(offset in body, fill type)] of every bitmap fill style in a shape tag."""
    version = VERSIONS[code]
    r = Bits(body, 2)
    rect(r)
    if version == 4:
        rect(r); r.byte += 1
    found = []
    fill_styles(r, version, found); line_styles(r, version, found)
    r.align(); fbits = r.ub(4); lbits = r.ub(4)
    while True:
        if r.ub(1):  # edge
            straight = r.ub(1); n = r.ub(4) + 2
            if straight:
                if r.ub(1):
                    r.ub(2 * n)
                else:
                    r.ub(1); r.ub(n)
            else:
                r.ub(4 * n)
            continue
        flags = r.ub(5)
        if flags == 0:
            break
        new_styles, line, fill1, fill0, move = (flags >> 4) & 1, (flags >> 3) & 1, (flags >> 2) & 1, (flags >> 1) & 1, flags & 1
        if move:
            n = r.ub(5); r.ub(2 * n)
        if fill0:
            r.ub(fbits)
        if fill1:
            r.ub(fbits)
        if line:
            r.ub(lbits)
        if new_styles and version >= 2:
            fill_styles(r, version, found); line_styles(r, version, found)
            r.align(); fbits = r.ub(4); lbits = r.ub(4)
    r.align()
    if r.byte != len(body):
        raise ValueError(f'shape parse ended at {r.byte} of {len(body)}')
    return found


def smooth_movie(movie):
    """`movie` with every non-smoothed bitmap fill made smoothed. Returns (movie, fills changed)."""
    head, tags = gfx_tags(movie)
    out, changed = [], 0
    for code, body, long in tags:
        if code in VERSIONS:
            fills = [at for at, kind in bitmap_fills(code, body) if kind in (0x42, 0x43)]
            if fills:
                body = bytearray(body)
                for at in fills:
                    body[at] &= ~0x02
                body = bytes(body); changed += len(fills)
        out.append((code, body, long))
    return gfx_write(head, out), changed


# ---------------------------------------------------------------------------------------------
# What the game would use without this mod

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def effective(relative, layers, game):
    """The file at `relative` (a dvdroot_ps4 path) from the topmost layer providing it, else the game's."""
    import mods
    key = relative.casefold()
    found = None
    for _name, root in layers:
        try:
            for rel, source in mods.mod_files(root):
                if rel.as_posix().casefold() == key:
                    found = source
        except (OSError, ValueError):
            continue
    return found or Path(game) / relative


def in_use(mods_dir, config, enabled):
    """Whether this mod is among the mods in use (the launcher's Mods page, mods.json)."""
    import mods
    if enabled != '1':
        return False
    try:
        return MOD_NAME in mods.selected(Path(mods_dir), config)
    except (OSError, ValueError):
        return False


def previous_archive(mods_dir):
    """The SHA-256 of the interface archive made at an earlier start, if it is still there."""
    folder = Path(mods_dir) / MOD_NAME
    try:
        entry = json.loads((folder / DATA_FOLDER / STAMP).read_text(encoding='utf-8'))['files'][ARCHIVE]
        if (folder / ARCHIVE).stat().st_size == entry['size']:
            return entry['sha256']
    except (OSError, ValueError, KeyError):
        pass
    return None


def prepare(game, generated, mods_dir, config, enabled, log=print):
    """Make this mod's launch-time files. `generated` are the port's own layers (in order),
    `game` the original game folder. Returns the archive's SHA-256, or None when the mod is not
    in use."""
    import mods
    if enabled != '1':
        return None
    mods_dir = Path(mods_dir)
    order = mods.selected(mods_dir, config)
    if MOD_NAME not in order:
        return None
    folder = mods_dir / MOD_NAME
    data_dir = folder / DATA_FOLDER
    below = [(Path(g).name, Path(g)) for g in generated if mods.content_root(g)]
    below += [(name, mods_dir / name) for name in order[:order.index(MOD_NAME)]]
    above = order[order.index(MOD_NAME) + 1:]

    stamp_path = data_dir / STAMP
    try:
        stamp = json.loads(stamp_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        stamp = {}
    files = stamp.get('files', {}) if stamp.get('identity') == IDENTITY else {}
    made = {}

    def write(relative, inputs, build):
        target = folder / relative
        key = sha256('\n'.join(inputs).encode())
        old = files.get(relative)
        if old and old.get('inputs') == key and target.is_file() and target.stat().st_size == old.get('size'):
            made[relative] = old
            return old['sha256']
        data = build()
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + '.ui4k-tmp')
        temp.write_bytes(data)
        temp.replace(target)
        made[relative] = dict(inputs=key, size=len(data), sha256=sha256(data))
        return made[relative]['sha256']

    def fingerprint(path):
        info = Path(path).stat()
        return f'{path}|{info.st_size}|{int(info.st_mtime)}'

    # Menu movies
    count = 0
    for reference in sorted((data_dir / 'movies').glob('*.gfx')):
        relative = f'dvdroot_ps4/menu/{reference.name}'
        original = Path(game) / relative
        if not original.is_file():
            continue
        base = effective(relative, below, game)
        inputs = [IDENTITY, fingerprint(base), fingerprint(reference), fingerprint(original)]

        def build(base=base, reference=reference, original=original):
            data, _replaced = scale_movie(base.read_bytes(), reference.read_bytes(), original.read_bytes())
            return smooth_movie(data)[0]
        write(relative, inputs, build)
        count += 1

    # Interface archive with the prompts in use
    source_archive = data_dir / 'common.tpf.dcx'
    prompts = effective(ARCHIVE, below, game)
    inputs = [IDENTITY, fingerprint(source_archive), fingerprint(prompts)]
    style = []

    def build_archive():
        header, base = read_archive(source_archive)
        _h, source = read_archive(prompts)
        try:
            keyboard = json.loads((data_dir / 'prompts.json').read_text(encoding='utf-8'))['keyboard_source']
        except (OSError, ValueError, KeyError):
            keyboard = ''
        if prompt_digest(source) == keyboard:
            style.append('made (keyboard prompts, upscaled)')
            return source_archive.read_bytes()
        style.append('made')
        return dcx_pack(header, tpf_write(with_prompts(base, source)))
    archive_hash = write(ARCHIVE, inputs, build_archive)

    # Files made earlier that are no longer wanted (a reference removed in an update).
    for relative in set(files) - set(made):
        old = folder / relative
        if old.is_file() and relative.startswith('dvdroot_ps4/'):
            old.unlink()
    data_dir.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(json.dumps(dict(identity=IDENTITY, files=made), indent=1), encoding='utf-8')
    log(f'UI 4K: {count} menu movies; interface archive {style[0] if style else "up to date"}, '
        f'button prompts from {prompts}')
    for name in above:
        try:
            if any(rel.as_posix().casefold() == ARCHIVE.casefold() for rel, _s in mods.mod_files(mods_dir / name)):
                log(f'UI 4K: {name} is after UI 4K and replaces its interface archive; '
                    'place UI 4K last in the mod order for the 4K interface')
        except (OSError, ValueError):
            pass
    return archive_hash


if __name__ == '__main__':
    # Maintenance: python ui4k_assets.py check <base.gfx> <reference.gfx> <original.gfx> [expected.gfx]
    if sys.argv[1:2] == ['check']:
        base, ref, orig = (Path(p).read_bytes() for p in sys.argv[2:5])
        data, replaced = scale_movie(base, ref, orig)
        print(replaced, 'records replaced;', 'matches expected' if len(sys.argv) > 5 and
              data == Path(sys.argv[5]).read_bytes() else sha256(data))
