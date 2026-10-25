# Validation

## 1.1.0 on bbport 2.1 (qml-launcher-preview-23)

Tested on one installation: Windows 11, AMD Radeon RX 6900 XT, 2560×1440 HDR display, CUSA03173 1.09, the port's scripts and `bb-probe.exe` identical to the official 2.1 release.

### Checked offline, against real files

- All 79 menu movies made by `scripts/ui4k_assets.py` from the game's movies, and from the 2.1 port's generated PC-menu movies (`optionsetting.gfx`, `title.gfx`, `title_dlc.gfx`), are **byte-identical** to the 1.0.0 package's copies before smoothing. Smoothing then changes only the type byte of 2,981 bitmap fills (same file sizes; running it twice changes nothing more). The shape parser reads all 6,370 bitmap fills in the game's and the package's movies with no errors.
- The DCX/TPF writer rebuilds the game's own `common.tpf.dcx` byte-identically.
- The inventory icon correction builds on 2.1's `boot-linked.bin`: all 20 atlas call sites found, the code page it uses is free.
- The interface archive is made with the Xbox prompts in about 7 s on first start, then reused (under 1 s).

### Checked in game (2560×1440 output)

- The game starts with the package. The log shows the movies and archive made, `Mods: UI 4K: 80 files`, the icon correction enabled, and `Patches: ... UI 2560x1440` (previously `UI 1920x1080`).
- Title screen and main menu render normally, with sharp text.
- HUD: quick item icons (from the 4× `MENU_Icon` atlases) appear in their frames at the original size; the Xbox prompt (A) shows at the right size in the lamp prompt.

### Automated in-game runs (`tests/ingame`, `hud.json`)

Each run starts the game, loads the save, captures the title menu, the HUD and the equipment menu, and checks the log. Runs with and without UI 4K (`-WithoutMod`) were compared:

- With UI 4K: the launch files, the icon correction and `UI 2560x1440` are in the log; all checks pass. Without it, none of them are, as expected.
- **Equipment menu:** weapon, armour and item icons in place and at their size; with smoothing visibly sharper than without the mod.
- **HUD Blood Echoes / Insight:** the upscaled symbol is used, and with smooth filtering it has clean edges instead of stair steps (compared in HDR-correct captures).
- **Which textures the HUD uses**, found by replacing textures with solid colours in test runs: the quick item uses the 4× `MENU_Icon` sheets; the Echoes/Insight panel uses `MENU_Common_00001`. The Blood Vial and Quicksilver Bullet slot pictures stayed unchanged even with every texture in every menu archive (and all 1,056 item pictures) coloured, so they come from elsewhere.

### Not yet checked in game

- The in-game PC menu (System > PC settings) and *Quit Game* on the title screen. Their movies are byte-identical to the 1.0.0 copies (apart from smoothing), which already contained the PC menu's rows.
- 3840×2160 output, and the PlayStation and keyboard prompt sets.
- A second, clean installation through `Setup.cmd` followed by a game start.

## Installer integration tests

`tests/test_installer.py` runs Windows PowerShell 5.1 against an isolated folder with the genuine 2.1 scripts and a copy of 2.1's `bb-probe.exe`. It never starts the game.

1. Clean install, verify, repeated install, exact restoration on uninstall, including the files made at start and the launch stamp. UI 4K is ordered last; the prompt mods stay enabled or disabled as chosen.
2. Unknown upstream scripts rejected before any change.
3. Damaged payload rejected before any change.
4. User edits protected during uninstall; later unrelated mod choices kept.
5. An injected final-verification failure rolls everything back exactly.
6. Manifest path traversal rejected.
7. Windows CRLF and UTF-8 BOM accepted; exact restoration with no original `mods.json`.
8. A leftover 1.0.0 `Inventory Icons 4K` folder rejected before any change.

Latest result: [`tests/last-results.json`](../tests/last-results.json).

## 1.0.0 on bbport 1.9.7 (aoho60372)

UI texture replacements and 79 adjusted movies kept their layout; the 3840×2160 movie viewport improved text; all 20 inventory atlases displayed in the right places and sizes. These results come from the original author's installation.
