"""Maintainer tool. Build the release payload from a known working bbport installation.
End users do not need Python. All copies are ordinary files, never links.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,difflib

ROOT=Path(__file__).resolve().parents[1]
def digest(data):return hashlib.sha256(data).hexdigest()
def textdigest(path):return digest(path.read_text(encoding='utf-8-sig').replace('\r\n','\n').encode())
def one(source,old,new):
    assert source.count(old)==1,repr(old)
    return source.replace(old,new)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bbport',type=Path,required=True);args=ap.parse_args()
    port=args.bbport.resolve()
    run=(ROOT/'upstream/run.py').read_text(encoding='utf-8')
    patches=(ROOT/'upstream/patches.py').read_text(encoding='utf-8')
    hook="""        # Bloodborne UI 4K: coordinates for the selected 4x inventory atlases.
        from inventory_icons import boot_for_mods
        boot_image = boot_for_mods(out, game, Path(env.get('BB_MODS_DIR', data / 'mods')),
                                  Path(env.get('BB_MODS_CONFIG', data / 'mods.json')),
                                  env.get('BB_MODS_ENABLED', '1'))
"""
    run=one(run,"        run_script('link_modules.py', game, '--out', out)\n",
                "        run_script('link_modules.py', game, '--out', out)\n"+hook)
    run=one(run,"str(out / 'boot-linked.bin')",'str(boot_image)')
    run=one(run,"            else:\n                env.pop('BB_UI_RES', None)\n        else:\n",
                "            else:\n                # Rasterize text for the physical 4K viewport; keep the logical stage.\n                if (ow, oh) == (3840, 2160):\n                    env['BB_UI_RES'] = movie_output\n                else:\n                    env.pop('BB_UI_RES', None)\n        else:\n")
    patches=one(patches,'    elif out[0]*9 != out[1]*16: ui=out\n',
                '    # Bloodborne UI 4K: physical 4K movie viewport, original logical stage.\n    elif out == (3840,2160): ui=out\n    elif out[0]*9 != out[1]*16: ui=out\n')
    integration=ROOT/'integration';integration.mkdir(exist_ok=True)
    (integration/'run.py').write_text(run,encoding='utf-8',newline='\n')
    (integration/'patches.py').write_text(patches,encoding='utf-8',newline='\n')
    module=(port/'scripts/inventory_icons.py').read_text(encoding='utf-8')
    (integration/'inventory_icons.py').write_text('# SPDX-License-Identifier: GPL-2.0-or-later\n'+module,encoding='utf-8',newline='\n')
    for name,data in [('run.py',run),('patches.py',patches)]:
        original=(ROOT/'upstream'/name).read_text(encoding='utf-8')
        patch=''.join(difflib.unified_diff(original.splitlines(True),data.splitlines(True),fromfile='upstream/'+name,tofile='integration/'+name))
        (integration/(name+'.diff')).write_text(patch,encoding='utf-8')
        compile(data,name,'exec')
    files=[]
    for name,target in [('run.py','run.py'),('patches.py','scripts/patches.py'),('inventory_icons.py','scripts/inventory_icons.py')]:
        src=integration/name
        files.append(dict(source=src.relative_to(ROOT).as_posix(),target=target,kind='script',sha256=digest(src.read_bytes())))
    for name in ('Keyboard Prompts (PCBButtons)','UI 4K','Inventory Icons 4K'):
        folder=port/'mods'/name/'dvdroot_ps4'
        if not folder.is_dir():folder=port/'mods'/name
        assert folder.is_dir(),folder
        for source in sorted(folder.rglob('*')):
            if not source.is_file():continue
            assert not source.is_symlink()
            if source.suffix.casefold() in ('.txt','.json','.png','.md'):continue
            relative=Path('mods')/name/'dvdroot_ps4'/source.relative_to(folder)
            dest=ROOT/'payload'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
            files.append(dict(source=dest.relative_to(ROOT).as_posix(),target=relative.as_posix(),kind='asset',sha256=digest(dest.read_bytes())))
    manifest=dict(id='bloodborne-ui4k',version='1.0.0',bbport='Jgamrot Launcher 1.9.7 / qml-launcher-preview-21',
                  game='Bloodborne GOTY CUSA03173 / 1.09',inputs=[
        dict(path='run.py',text=True,sha256=textdigest(ROOT/'upstream/run.py')),
        dict(path='scripts/patches.py',text=True,sha256=textdigest(ROOT/'upstream/patches.py')),
        dict(path='bin/bb-probe.exe',text=False,sha256='9870a55dc94f33b83056b8477953e92bfde2276b5b131c9e02788a411f5c88e5')],files=files)
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Prepared',len(files),'files;',round(sum((ROOT/f['source']).stat().st_size for f in files)/1048576,2),'MiB')
if __name__=='__main__':main()
