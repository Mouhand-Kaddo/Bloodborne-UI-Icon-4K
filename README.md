# Bloodborne UI and Icons 4K upscale for bbport

[Русская версия](README.ru.md) · [Compatibility and testing](docs/TESTING.md) · [Credits](THIRD_PARTY_NOTICES.md)

**Bloodborne UI and Icons 4K** is a texture upscale mod for **bbport** that improves interface artwork, HUD textures, inventory icons and text clarity at **3840×2160**. It includes an English/Russian Windows installer for **Jgamrot bbport Launcher 1.9.7** and preserves the original interface layout and on-screen icon sizes.

[**Download the installer**](https://github.com/aoho60372/Bloodborne-UI-Icon-4K/releases/latest) · [Installation](#install) · [FAQ](#faq)

## Before / after

These are **real texture comparisons, not gameplay screenshots**. The original and modified images show the same region at the same displayed size. The original icon crop is enlarged with bilinear filtering; no extra sharpening is applied. The enlarged views make differences easier to inspect and do not represent the normal on-screen icon size. The existing UI decoration comparison was retained from development. [Crop coordinates and method](docs/images/comparison-method.json).

### Inventory icons

![Bloodborne bbport inventory icons before and after the 4K texture upscale; original crops on the left](docs/images/inventory-consumables.png)

### Other inventory atlases

![Three more Bloodborne inventory icon texture crops before and after the bbport 4K upscale](docs/images/inventory-more.png)

### Interface decorations

![Bloodborne UI 4K texture comparison for bbport: interface ornament and frame before and after](docs/images/ui-decorations.png)

## Features

- **UI 4K:** 40 interface textures enlarged 2× per axis, with 79 Scaleform GFX files adjusted to preserve layout.
- **Inventory Icons 4K:** all 20 `MENU_Icon` atlases enlarged 4× per axis. Standard 1024×1024 atlases become 4096×4096; rectangular atlases retain their aspect ratio.
- **Correct icon coordinates:** a guarded native texture UV correction keeps icons in their original screen areas and at their original screen size.
- **4K text rendering:** matches the movie viewport to 3840×2160. Fonts remain the game's original vector fonts; this is not a replacement font pack.
- Keyboard and mouse prompts from **PCBButtons** are included and enabled.
- Install and uninstall from one English/Russian window. The selected folder is checked automatically. No Python installation or administrator rights required in a writable bbport folder.

## FAQ

### How can I improve Bloodborne UI clarity at 4K?

This package combines higher-resolution menu and HUD textures with a 3840×2160 movie viewport for text rendering. Install it from the [latest release](https://github.com/aoho60372/Bloodborne-UI-Icon-4K/releases/latest), select **3840×2160** in bbport and restart the game. The game’s original vector fonts are retained; this is not a replacement font pack.

### Does this include 4K inventory icons for bbport?

Yes. **Inventory Icons 4K** upscales all 20 `MENU_Icon` atlases by **4× per axis**, covering the inventory’s item, weapon and clothing icons. Standard 1024×1024 atlases become 4096×4096. The included runtime correction preserves the proper texture coordinates, so icons stay whole and match their items.

### Does this change Bloodborne UI scale or make the HUD bigger?

No. This mod improves texture resolution and 4K text rendering while preserving the original on-screen size and layout. It does not add a UI scale slider or enlarge the HUD and inventory slots.

### Which bbport version is supported?

Use **Jgamrot bbport Launcher 1.9.7**, tag **`qml-launcher-preview-21`**. The installer checks the port’s original scripts and runtime before installation. Download the supported port from its [release page](https://github.com/Jgamrot/bloodborne_pc/releases/tag/qml-launcher-preview-21).

## Requirements

| Component | Supported configuration |
|---|---|
| OS | Windows 10/11, Windows PowerShell 5.1 |
| Port | [Jgamrot bbport 1.9.7, `qml-launcher-preview-21`](https://github.com/Jgamrot/bloodborne_pc/releases/tag/qml-launcher-preview-21) |
| Output | **3840×2160** for the tested text-rendering improvement |
| Prompts | Keyboard/mouse; Xbox prompt compatibility is not established |

The installer checks exact upstream script fingerprints and the stock `bb-probe.exe` SHA-256. It refuses unsupported or modified installations before copying files. The larger item-description illustrations and world textures are not included.

## Install

1. Download [**Bloodborne-UI-4K-v1.0.0.zip from the latest release**](https://github.com/aoho60372/Bloodborne-UI-Icon-4K/releases/latest) and extract it. GitHub's automatic **Source code** ZIP does not include the binary texture payload.
2. Close the game **and launcher**.
3. Double-click **`Setup.cmd`**. Choose English or Russian.
4. Browse to the **bbport folder containing `Bloodborne.exe`**, not the game's `CUSA03173` folder. Validation runs automatically. Click **Install** once the folder passes validation.
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

