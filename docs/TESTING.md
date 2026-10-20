# Validation / Проверки

## Confirmed in the original game installation

- UI texture replacements and 79 adjusted GFX movies retain their layout.
- The 3840×2160 physical movie viewport improves text rendering without changing the logical stage.
- All 20 inventory atlases display in the correct positions and at their original screen sizes.
- Runtime observations recorded the corrected native texture UV function being called 240 times in the full-atlas user test.

These results refer to the user's working Jgamrot 1.9.7 / CUSA03173 1.09 installation, not every bbport fork or game region.

## Installer integration tests

`tests/test_installer.py` runs actual **Windows PowerShell 5.1** against an isolated folder containing genuine upstream scripts and an ordinary copy of the matching `bb-probe.exe`. It never launches the game. Fixture paths include spaces and Cyrillic characters.

Checks:

1. Clean install, verify, repeated install and exact restoration of original file bytes on uninstall.
2. Unknown upstream scripts rejected before target mutation.
3. Damaged payload rejected before target mutation.
4. User edits protected during uninstall; later unrelated mod choices retained.
5. Injected final-verification failure rolls back copied files and configuration exactly.
6. Manifest path traversal rejected.
7. Windows CRLF and UTF-8 BOM accepted for upstream scripts; exact restoration with no original `mods.json`.

Latest machine-readable result: [`tests/last-results.json`](../tests/last-results.json).

## Still requires a user gameplay check

The full release installer has not been used to launch a second clean game installation. Installer verification proves copying, configuration and rollback, not rendering on another computer. Other game regions, newer bbport builds, controller image sets and arbitrary interface replacements are not certified.

## Comparison images

The README contains texture comparisons, not gameplay screenshots. Six icon examples are cropped from original decoded PNGs and the enlarged BC-compressed DDS resources used to prepare the installed atlases. Both columns use the same display dimensions and bilinear resizing where needed. The older interface-decoration comparison retains its original picture pixels with updated headings. No game scene, font screenshot or performance result was generated to stand in for an actual capture.

## Русское резюме

Игровая проверка модов проведена на исходной рабочей установке пользователя. Проверка установщика выполняется отдельно, на копиях файлов: она подтверждает установку, отказ при несовместимости и откат, но не заменяет запуск игры на чистой установке. Установщик не использует жёсткие ссылки, корзину, изменение владельца файлов или прав доступа. Игровой дамп и сохранения не затрагиваются.
