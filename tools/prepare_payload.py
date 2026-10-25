"""Maintainer tool. Build the release payload and manifest.

Inputs (ordinary files, never links):
  --assets   the v1.0.0 release's payload/mods folder (UI 4K movies and the Inventory Icons 4K
             archive, which holds every upscaled texture: UI 2x, inventory icons 4x, prompts 2x)
  --keyboard the PCBButtons common.tpf.dcx the upscaled prompts were made from (its prompt
             images are fingerprinted, so the launch helper keeps the upscaled ones for it)
  --probe    the stock bin/bb-probe.exe of the supported bbport release
  --game, --esrgan, --ffmpeg  the game folder, realesrgan-ncnn-vulkan.exe and ffmpeg.exe: the HUD's
             Blood Vial and Quicksilver Bullet pictures are upscaled into the archive
             (tools/hud_sprites.py)

The integration scripts are made from upstream/ by tools/make_integration.py beforehand.
End users do not need Python.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integration'))
import ui4k_assets  # noqa: E402

VERSION = '1.1.1'
BBPORT = 'Jgamrot Launcher 2.1 / qml-launcher-preview-23'
MOD = 'mods/UI 4K'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def textdigest(path):
    return digest(path.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', type=Path, required=True)
    ap.add_argument('--keyboard', type=Path, required=True)
    ap.add_argument('--probe', type=Path, required=True)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--esrgan', type=Path, required=True)
    ap.add_argument('--ffmpeg', type=Path, required=True)
    args = ap.parse_args()
    payload = ROOT / 'payload'
    if payload.exists():
        shutil.rmtree(payload)
    data = payload / MOD / ui4k_assets.DATA_FOLDER
    (data / 'movies').mkdir(parents=True)

    archive = args.assets / 'Inventory Icons 4K/dvdroot_ps4/menu/common.tpf.dcx'
    shutil.copyfile(archive, data / 'common.tpf.dcx')
    _header, tpf = ui4k_assets.read_archive(archive)
    icons = [t for t in tpf['textures'] if t['name'].startswith('MENU_Icon_')]
    assert len(icons) == 20 and all(t['w'] >= 4096 for t in icons if t['h'] >= 1024), 'not the 4x icon archive'
    sys.path.insert(0, str(ROOT / 'tools'))
    import hud_sprites
    print('HUD vial/bullet blocks upscaled:', hud_sprites.apply(data / 'common.tpf.dcx', args.game, args.esrgan, args.ffmpeg))
    for movie in sorted((args.assets / 'UI 4K/dvdroot_ps4/menu').glob('*.gfx')):
        shutil.copyfile(movie, data / 'movies' / movie.name)
    _header, keyboard = ui4k_assets.read_archive(args.keyboard)
    (data / 'prompts.json').write_text(json.dumps({'keyboard_source': ui4k_assets.prompt_digest(keyboard)}, indent=1) + '\n',
                                       encoding='utf-8')

    files = []
    for name, target in [('run.py', 'run.py'), ('patches.py', 'scripts/patches.py'),
                         ('ui4k_assets.py', 'scripts/ui4k_assets.py'), ('inventory_icons.py', 'scripts/inventory_icons.py')]:
        src = ROOT / 'integration' / name
        compile(src.read_text(encoding='utf-8'), str(src), 'exec')
        files.append(dict(source=src.relative_to(ROOT).as_posix(), target=target, kind='script', sha256=digest(src.read_bytes())))
    for source in sorted(p for p in (payload / MOD).rglob('*') if p.is_file()):
        relative = source.relative_to(payload).as_posix()
        files.append(dict(source=source.relative_to(ROOT).as_posix(), target=relative, kind='asset',
                          sha256=digest(source.read_bytes())))
    manifest = dict(id='bloodborne-ui4k', version=VERSION, bbport=BBPORT, game='Bloodborne GOTY CUSA03173 / 1.09',
                    inputs=[dict(path='run.py', text=True, sha256=textdigest(ROOT / 'upstream/run.py')),
                            dict(path='scripts/patches.py', text=True, sha256=textdigest(ROOT / 'upstream/patches.py')),
                            dict(path='bin/bb-probe.exe', text=False, sha256=digest(args.probe.read_bytes()))],
                    # Made at launch by scripts/ui4k_assets.py; the folder must exist for the port to list the mod.
                    directories=[f'{MOD}/dvdroot_ps4/menu'],
                    generated=dict(root=f'{MOD}/dvdroot_ps4', stamp=f'{MOD}/{ui4k_assets.DATA_FOLDER}/{ui4k_assets.STAMP}'),
                    files=files)
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Prepared', len(files), 'files;', round(sum((ROOT / f['source']).stat().st_size for f in files) / 1048576, 2), 'MiB')


if __name__ == '__main__':
    main()
