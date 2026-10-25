"""Maintainer tool. Make integration/run.py and integration/patches.py (and their .diff files)
from the clean bbport scripts in upstream/. Each edit must match exactly once, so a changed
upstream fails here instead of producing a half-patched script.

    python tools/make_integration.py
"""
from pathlib import Path
import difflib

ROOT = Path(__file__).resolve().parents[1]


def one(source, old, new):
    assert source.count(old) == 1, f'upstream changed near: {old[:70]!r}'
    return source.replace(old, new)


def patches(text):
    return one(text, """    if ultrawide(out): ui=hud_canvas(out)
    elif out[0]*9 != out[1]*16: ui=out
""", """    if ultrawide(out): ui=hud_canvas(out)
    elif out[0]*9 != out[1]*16: ui=out
    # Bloodborne UI 4K: 16:9 outputs above 1080p get the physical movie viewport, so text is
    # drawn at the output's size (the logical stage stays 1920x1080). run.py sets BB_UI4K_TEXT.
    elif out[1] > OUTPUT_SIZE[1] and os.environ.get('BB_UI4K_TEXT') == '1': ui=out
""")


def run(text):
    text = one(text, """    game = Path(run_script('mods.py', game, '--out', out,
""", """    # Bloodborne UI 4K (scripts/ui4k_assets.py): its menu movies and interface archive, made for
    # this port's own menu files and the button prompts in use, before the mods are put together.
    sys.path.insert(0, str(PORT / 'scripts'))
    import ui4k_assets
    ui4k_mods = (Path(env.get('BB_MODS_DIR', data / 'mods')), Path(env.get('BB_MODS_CONFIG', data / 'mods.json')),
                 env.get('BB_MODS_ENABLED', '1'))
    ui4k_on = ui4k_assets.in_use(*ui4k_mods)
    ui4k_archive = None
    if ui4k_on:
        try:
            ui4k_archive = ui4k_assets.prepare(game, generated, *ui4k_mods)
        except Exception as error:  # noqa: BLE001 - the game starts with the files made last time
            print(f'UI 4K: launch files not made ({error}); using the previous ones', file=sys.stderr)
            ui4k_archive = ui4k_assets.previous_archive(ui4k_mods[0])
    game = Path(run_script('mods.py', game, '--out', out,
""")
    text = one(text, """        run_script('link_modules.py', game, '--out', out)
""", """        run_script('link_modules.py', game, '--out', out)
        # Bloodborne UI 4K (scripts/inventory_icons.py): icon coordinates for the 4x inventory atlases.
        boot_image = out / 'boot-linked.bin'
        if ui4k_on:
            from inventory_icons import boot_for_archive
            try:
                boot_image = boot_for_archive(out, game, ui4k_archive)
            except Exception as error:  # noqa: BLE001
                fail(f'UI 4K: the inventory icon correction could not be made for this port ({error}). '
                     'Turn UI 4K off on the launcher\\'s Mods page to play without it.')
""")
    text = one(text, """        from patches import hud_canvas, ultrawide
        env.pop('BB_ASPECT_PATCHED', None)
""", """        from patches import hud_canvas, ultrawide
        env.pop('BB_ASPECT_PATCHED', None)
        env.pop('BB_UI4K_TEXT', None)
""")
    text = one(text, """            else:
                env.pop('BB_UI_RES', None)
        else:
            env.pop('BB_UI_RES', None)
""", """            elif ui4k_on and oh > 1080:
                # Bloodborne UI 4K: text drawn for the physical viewport (patches.py, BB_UI4K_TEXT).
                live = '0'
                env['BB_UI_RES'] = movie_output
                env['BB_UI4K_TEXT'] = '1'
                print(f'UI 4K: text drawn at {movie_output}; resolution changes require restart')
            else:
                env.pop('BB_UI_RES', None)
        else:
            env.pop('BB_UI_RES', None)
""")
    return one(text, """        command = [str(probe), str(out / 'boot-linked.bin'), '--content-profile',""",
               """        command = [str(probe), str(boot_image), '--content-profile',""")


def main():
    for name, change in (('run.py', run), ('patches.py', patches)):
        original = (ROOT / 'upstream' / name).read_text(encoding='utf-8')
        made = change(original)
        compile(made, name, 'exec')
        (ROOT / 'integration' / name).write_text(made, encoding='utf-8', newline='\n')
        diff = ''.join(difflib.unified_diff(original.splitlines(True), made.splitlines(True),
                                            fromfile='upstream/' + name, tofile='integration/' + name))
        (ROOT / 'integration' / (name + '.diff')).write_text(diff, encoding='utf-8', newline='\n')
        print(name, 'ok')


if __name__ == '__main__':
    main()
