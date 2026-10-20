# Bloodborne UI 4K

[Русская версия](README.ru.md) · [Compatibility and testing](docs/TESTING.md) · [Credits](THIRD_PARTY_NOTICES.md)

Sharper interface artwork, inventory icons and 4K text rendering for **Jgamrot bbport Launcher 1.9.7**.

## Before / after

These are **real texture comparisons, not gameplay screenshots**. The original and modified images show the same region at the same displayed size. The original icon crop is enlarged with bilinear filtering; no extra sharpening is applied. The enlarged views make differences easier to inspect and do not represent the normal on-screen icon size. The existing UI decoration comparison was retained from development. [Crop coordinates and method](docs/images/comparison-method.json).

### Inventory icons

![Original inventory icon crops on the left; upscaled texture crops on the right](docs/images/inventory-consumables.png)

### Other inventory atlases

![Three additional inventory atlas crops, before and after](docs/images/inventory-more.png)

### Interface decorations

![Interface ornament and frame texture comparison](docs/images/ui-decorations.png)

## Features

- **UI 4K:** 40 interface textures enlarged 2× per axis, with 79 Scaleform GFX files adjusted to preserve layout.
- **Inventory Icons 4K:** all 20 `MENU_Icon` atlases enlarged 4× per axis. Standard 1024×1024 atlases become 4096×4096; rectangular atlases retain their aspect ratio.
- **Correct icon coordinates:** a guarded native texture UV correction keeps icons in their original screen areas and at their original screen size.
- **4K text rendering:** matches the movie viewport to 3840×2160. Fonts remain the game's original vector fonts; this is not a replacement font pack.
- Keyboard and mouse prompts from **PCBButtons** are included and enabled.
- Install and uninstall from one English/Russian window. The selected folder is checked automatically. No Python installation or administrator rights required in a writable bbport folder.

## Requirements

| Component | Supported configuration |
|---|---|
| OS | Windows 10/11, Windows PowerShell 5.1 |
| Port | [Jgamrot bbport 1.9.7, `qml-launcher-preview-21`](https://github.com/Jgamrot/bloodborne_pc/releases/tag/qml-launcher-preview-21) |
| Output | **3840×2160** for the tested text-rendering improvement |
| Prompts | Keyboard/mouse; Xbox prompt compatibility is not established |

The installer checks exact upstream script fingerprints and the stock `bb-probe.exe` SHA-256. It refuses unsupported or modified installations before copying files. The larger item-description illustrations and world textures are not included.

## Install

1. Download **`Bloodborne-UI-4K-v1.0.0.zip` from this project's Releases** and extract it. GitHub's automatic **Source code** ZIP does not include the binary texture payload.
2. Close the game **and launcher**.
3. Double-click **`Setup.cmd`**. Choose English or Russian.
4. Browse to the **bbport folder containing `Bloodborne.exe`**, not the game's `CUSA03173` folder. Validation runs automatically: **green text** below the path means ready, and **red text** explains any problem. There are no pop-up prompts. Click **Install** once the folder passes validation.
5. Start bbport normally. Select **3840×2160** for the tested 4K text result, then restart the game.

The installer enables and orders these mods automatically:

```text
Keyboard Prompts (PCBButtons)
UI 4K
Inventory Icons 4K
```

Existing unrelated mod entries are preserved. Xbox image prompts are disabled because the included interface archive uses keyboard prompts. The installer does not change your resolution, key bindings, saves, game dump or graphics-driver settings. Keep the launcher's keyboard layout consistent with the prompt images.

## Uninstall / update

Run **`Setup.cmd`**, select the same bbport folder and click **Uninstall**. Original scripts and pre-existing package files are restored from ordinary backup copies under `.bbport-ui4k`; files added by this installer are removed. Later unrelated mod choices are preserved. Do not delete that backup directory while the package is installed.

Uninstall **before updating bbport**. If an installed file was modified by another update or by hand, uninstall stops instead of overwriting it. Keep a copy of that edited file, restore the matching installed version, then uninstall. Do not replace an unknown newer script with an old backup blindly.

## Troubleshooting

| Message / symptom | What to do |
|---|---|
| Unsupported or modified bbport | Use the exact clean supported release. This installer does not overwrite unknown local camera or launcher fixes. |
| Incomplete source checkout | Download the full installer ZIP from Releases. |
| Package/file verification failed | Re-extract the release and check its published SHA-256. |
| Different existing mod at a destination | Keep that mod separately before installing. |
| `common.tpf.dcx` conflict at game start | Put Inventory Icons 4K after UI 4K and other interface mods. It must be the effective interface archive. |
| Cropped, displaced or giant icons | Verify the package files. Do not install only the texture folder without its runtime integration. |
| PowerShell is blocked by organization policy | Use the machine's approved installation process. The package does not change machine execution policy. |

