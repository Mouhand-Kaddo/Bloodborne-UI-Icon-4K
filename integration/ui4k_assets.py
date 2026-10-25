# SPDX-License-Identifier: GPL-2.0-or-later
"""Bloodborne UI 4K: game files made at launch for the bbport version in use.

Two kinds of files are made into the mod's own dvdroot_ps4 folder each time the game starts
(and only remade when an input changes):

* Menu movies (menu/*.gfx). The package ships the UI 4K copies only as references. Each movie
  is rebuilt from the copy the game would otherwise use (the port's generated PC menu, HUD
  layout or language files, other mods below this one, or the game's own), with UI 4K's image
  and shape records put in: the doubled image sizes and the halved bitmap-fill scales. A record
  is replaced only where the base still has the game's original one, so the port's own edits
  (PC menu rows, Quit Game, ultrawide layout) are kept.
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
IDENTITY = 'ui4k-assets 2'


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


# The button prompt images (KG_*, the key guide) and the atlas with the larger prompt pictures.
PROMPT_TEXTURES = ('KG_Cancel', 'KG_L1', 'KG_L2', 'KG_L3', 'KG_LS', 'KG_L_D', 'KG_L_LR', 'KG_L_U',
                   'KG_L_UD', 'KG_L_UDLR', 'KG_OK', 'KG_R1', 'KG_R2', 'KG_R3', 'KG_RS', 'KG_R_L',
                   'KG_R_U', 'KG_Start', 'KG_TP_L', 'KG_TP_R', 'MENU_Common_00091')


def prompt_digest(tpf):
    by_name = {t['name']: t for t in tpf['textures']}
    digest = hashlib.sha256()
    for name in PROMPT_TEXTURES:
        t = by_name[name]
        digest.update(name.encode() + struct.pack('<HHi', t['w'], t['h'], t['dxgi']) + t['data'])
    return digest.hexdigest()


def with_prompts(base, source):
    """`base` (the 4K archive) with the prompt images of `source`. Each keeps its own size: the
    menu movies give the key guide 64x64 and the atlas 2048x1024, and the game samples a smaller
    image over the same area."""
    by_name = {t['name']: t for t in source['textures']}
    out = dict(base, textures=[])
    for t in base['textures']:
        out['textures'].append(dict(by_name[t['name']]) if t['name'] in PROMPT_TEXTURES else t)
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
            return data
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
