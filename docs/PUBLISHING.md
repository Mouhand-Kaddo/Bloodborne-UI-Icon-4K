# Rebuild and publish

## Repository

The repository holds the source: installer, integration and launch helper, upstream copies, diffs, tests, docs. `.gitignore` excludes `payload/`, `build/` and `dist/`: the textures (about 88 MiB) are attached to each GitHub Release as the full ZIP, never committed.

## Rebuild for a bbport release

Requirements: Python 3.10+ and Windows PowerShell 5.1.

```powershell
# 1. Put the new release's clean run.py and scripts/patches.py in upstream/, then:
python tools/make_integration.py
# 2. Textures and reference movies from the 1.0.0 release ZIP's payload/mods folder:
python tools/prepare_payload.py --assets "<1.0.0 ZIP>\Bloodborne-UI-4K\payload\mods" `
    --keyboard "<bbport>\mods\Keyboard Prompts (PCBButtons)\menu\common.tpf.dcx" --probe "<bbport>\bin\bb-probe.exe" `
    --game "<game folder>" --esrgan "<path>\realesrgan-ncnn-vulkan.exe" --ffmpeg "<path>\ffmpeg.exe"
python tests/test_installer.py --probe "<bbport>\bin\bb-probe.exe"
python tools/build_release.py
```

`--game`, `--esrgan` and `--ffmpeg` are for `tools/hud_sprites.py`: it upscales the HUD's Blood Vial and Quicksilver Bullet pictures from the game's own sheet with [Real-ESRGAN ncnn Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) (`realesrgan-x4plus`) and writes them into the archive. Neither tool is shipped.

`make_integration.py` stops if an edit no longer matches the upstream script exactly. Then read the new script, port the edit by hand, and test in game. Do not make the installer accept unknown hashes to silence a version error.

Before publishing a new bbport version, start the game with it: `user\last_run.log` must show `UI 4K: 20 inventory atlases at 4x; native UV correction enabled` and `Patches: ... UI <output size>`, and the inventory icons must sit in their frames.

## Release checklist

- `tests/last-results.json` passed and is current; README compatibility matches the build.
- The full ZIP opens, every manifest file matches, and `SHA256SUMS.txt` matches both ZIPs.
- No personal paths, credentials, game executables, saves or logs are included.
- Attach `Bloodborne-UI-4K-v<version>.zip` and `SHA256SUMS.txt` to the release.
