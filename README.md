# Bloodborne UI and Icons 4K for bbport 2.1

[Русская версия](README.ru.md) · [Compatibility and testing](docs/TESTING.md) · [Credits](THIRD_PARTY_NOTICES.md) · [Changelog](CHANGELOG.md)

Sharper interface artwork, 4× inventory icons and sharper text for **Jgamrot bbport Launcher 2.1** at **2560×1440 and 3840×2160**.

This is a fork of [aoho60372/Bloodborne-UI-Icon-4K](https://github.com/aoho60372/Bloodborne-UI-Icon-4K), which made the textures, the menu movie adjustments and the inventory icon correction for bbport 1.9.7. This fork brings them to bbport 2.1, adds 1440p, and keeps whichever button prompts you use (Xbox, keyboard or PlayStation).

[**Download the installer**](https://github.com/Mouhand-Kaddo/Bloodborne-UI-Icon-4K/releases/latest) · [Install](#install) · [What changed from 1.0.0](#what-changed-from-100) · [FAQ](#faq)

## Before / after

These are **texture comparisons, not gameplay screenshots**: the same region at the same displayed size, the original enlarged with bilinear filtering. [Crop coordinates and method](docs/images/comparison-method.json).

### Inventory icons

![Bloodborne inventory icons before and after the 4K texture upscale; original crops on the left](docs/images/inventory-consumables.png)

### Other inventory atlases

![Three more Bloodborne inventory icon texture crops before and after the 4K upscale](docs/images/inventory-more.png)

### Interface decorations

![Interface ornament and frame before and after](docs/images/ui-decorations.png)

## Features

- **Interface 2×:** 40 interface textures enlarged 2× per axis, with 79 Scaleform menu movies adjusted so the layout is unchanged.
- **Inventory icons 4×:** all 20 `MENU_Icon` atlases enlarged 4× per axis, with a guarded native texture UV correction that keeps icons in their original places and sizes.
- **Smooth image filtering:** the game's menu movies draw almost every image (6,328 of 6,370 fills) with nearest-pixel sampling, exact at 1080p but stair-stepped at 1440p and 4K. The movies are switched to bilinear filtering, so the upscaled art shows its detail at any size (the HUD's Blood Echoes and Insight symbols, menu frames, inventory icons).
- **Sharper text above 1080p:** at any 16:9 output above 1080p (2560×1440, 3840×2160) the game's vector fonts are drawn for the output's own size. Not a font replacement.
- **Your button prompts:** at each start the interface archive takes the prompt images of the prompt mod in use (Xbox, keyboard/PCBButtons, or the game's PlayStation ones). The keyboard prompts keep their 2× upscale.
- **Works with the port's own menu edits:** the menu movies are rebuilt at start from the port's versions (in-game PC menu, *Quit Game*, ultrawide HUD layout, language files), with only the upscale's image and shape records put in.
- One English/Russian install and uninstall window. No Python or administrator rights needed.

## Install

1. Download **`Bloodborne-UI-4K-v1.1.0.zip`** from the [latest release](https://github.com/Mouhand-Kaddo/Bloodborne-UI-Icon-4K/releases/latest) and extract it. GitHub's automatic *Source code* ZIP does not contain the textures.
2. Close the game **and the launcher**.
3. Double-click **`Setup.cmd`** and choose English or Russian.
4. Browse to the **bbport folder containing `Bloodborne.exe`** (not the game's `CUSA03173` folder). When it turns green, click **Install**.
5. Start bbport normally. Choose your button prompts in the launcher as usual.

The installer adds one mod, **UI 4K**, at the end of the mod order, so its interface archive is the one the game loads. Your other mods and prompt choice stay as they were. Resolution, key bindings, saves and the game dump are not changed.

The first start after installing, or after switching prompts, takes a few seconds longer while the interface archive is made (`UI 4K:` lines in `user\last_run.log`).

## Uninstall / update

Run **`Setup.cmd`**, select the same bbport folder and click **Uninstall**. The original scripts are restored from `.bbport-ui4k`, and the package's files, including those made at start, are removed. Later unrelated mod choices are kept.

Uninstall **before updating bbport**. If an installed file was changed by an update or by hand, uninstall stops instead of overwriting it.

To play without it for a while, turn **UI 4K** off on the launcher's **Mods** page. The port's own behaviour then comes back, including 1080p-sized text.

## Requirements

| Component | Supported configuration |
|---|---|
| OS | Windows 10/11, Windows PowerShell 5.1 |
| Port | [Jgamrot bbport 2.1, `qml-launcher-preview-23`](https://github.com/Jgamrot/bloodborne_pc/releases/tag/qml-launcher-preview-23) |
| Game | Bloodborne GOTY CUSA03173, version 1.09 |
| Output | Any; the sharper text applies to 16:9 outputs above 1080p |
| Prompts | Xbox, keyboard (PCBButtons) or PlayStation |

The installer checks the port's original scripts and the stock `bb-probe.exe` (SHA-256) and refuses anything else before copying files.

## What changed from 1.0.0

| | 1.0.0 (aoho60372) | 1.1.0 (this fork) |
|---|---|---|
| bbport | 1.9.7 | 2.1 |
| Sharper text | 3840×2160 only | Every 16:9 output above 1080p, while UI 4K is enabled |
| Button prompts | Keyboard only; Xbox prompts disabled | The prompt set in use, chosen in the launcher |
| Menu movies | Fixed copies, which replace the port's PC menu movies | Rebuilt at start from the port's own versions |
| Mod folders | `Keyboard Prompts (PCBButtons)`, `UI 4K`, `Inventory Icons 4K` | `UI 4K` only (keyboard prompts come from the launcher's own download) |
| Another mod replacing the interface archive | The game does not start | A warning; that mod's archive is used without the icon correction |

## Known limitation

The pictures in the HUD's **Blood Vial and Quicksilver Bullet slots** (top left) are not part of the menu textures: with every menu texture, item picture and icon sheet replaced by solid colours in a test, they still showed. They stay at the game's resolution, now drawn with smooth filtering instead of nearest-pixel. Where the game loads them from is not known yet.

## FAQ

### Does this change the UI scale or make the HUD bigger?

No. Textures and text get sharper; on-screen sizes and layout stay the same.

### Does it work with the Xbox prompts?

Yes. The prompt images of the topmost other mod with its own `menu/common.tpf.dcx` (such as *Xbox 360 Prompts (Elden Ring)*) are put into the 4K archive at each start. Without such a mod, the game's PlayStation prompts are used. Those images keep their original resolution; the keyboard ones are upscaled.

### Why does changing the resolution in game ask for a restart?

The sharper text draws the menus for the output size chosen at start, so, as with the port's own non-16:9 outputs, a resolution change applies at the next start.

## Troubleshooting

| Message / symptom | What to do |
|---|---|
| Unsupported or modified bbport | Use the clean 2.1 release. The installer does not overwrite unknown local changes. |
| A different mod already uses `mods/Inventory Icons 4K` | Remove the 1.0.0 package (or that folder) first. |
| `UI 4K: ... is after UI 4K and replaces its interface archive` | Move UI 4K to the end of the mod order. |
| `UI 4K: the inventory icon correction could not be made` | The port's game image is not the one this package supports. Turn UI 4K off to play. |
| Incomplete source checkout / damaged payload | Download and extract the full release ZIP again. |
| PowerShell blocked by organization policy | Use the machine's approved installation process. |
