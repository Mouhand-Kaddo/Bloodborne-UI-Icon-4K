# Changelog

## 1.1.0 (fork for bbport 2.1)

- **bbport 2.1** (`qml-launcher-preview-23`): the integration is remade from the 2.1 scripts (`tools/make_integration.py`), and the installer checks 2.1's scripts and `bb-probe.exe`.
- **1440p:** text is drawn at the output's size at every 16:9 output above 1080p while UI 4K is enabled, not only at 3840×2160. Such outputs start with the resolution patch, so resolution changes take a restart.
- **Button prompts kept:** the interface archive is made at start with the prompt images of the prompt mod in use (Xbox, keyboard) or the game's own (PlayStation). Xbox prompts are no longer disabled, and PCBButtons is no longer bundled (the launcher downloads it).
- **Menu movies made at start** (`scripts/ui4k_assets.py`) from the port's own versions (PC menu, Quit Game, ultrawide HUD layout, language files) plus UI 4K's image and shape records, instead of fixed copies that replaced the port's PC menu movies.
- **One mod folder**, `UI 4K`, holds the 4K archive (UI 2×, icons 4×) and the reference movies. The installer puts it last in the mod order and removes the files made at start on uninstall.
- Another mod replacing the interface archive after UI 4K now prints a warning and skips the icon correction, instead of stopping the start.
- **Smooth image filtering:** the menu movies' bitmap fills are switched from non-smoothed (nearest-pixel) to smoothed (bilinear) when they are made at start, so upscaled art is not stair-stepped at 1440p/4K. This is what made the HUD's Blood Echoes and Insight symbols look unchanged.
- **In-game test runner** (`tests/ingame`): starts the game at normal rights on a copy of the saves, plays a scripted scenario, checks the log, takes HDR-correct screenshots and closes the game; `-WithoutMod` gives the before/after comparison.
- Installer tests updated (files made at launch, mod order, leftover 1.0.0 folder).
- Known limitation: the HUD's Blood Vial and Quicksilver Bullet slot pictures do not come from any menu texture and stay at the game's resolution.

## 1.0.0 (aoho60372)

- Initial English/Russian installer for Jgamrot bbport 1.9.7 / preview-21.
- UI 4K artwork, all 20 inventory atlases and 4K movie-viewport text rendering.
- Included PCBButtons keyboard/mouse images with attribution.
- Exact-version and payload checks, ordinary-file backups, rollback, verification and uninstall.
- Six icon crop comparisons and the interface-decoration comparison.
- Folder, compatibility, payload and installed-file checks run automatically with an inline red/green status.
