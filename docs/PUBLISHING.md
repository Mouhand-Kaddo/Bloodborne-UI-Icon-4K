# Publish on GitHub / Публикация на GitHub

## Repository

Create a repository and upload this folder's **source files**. `.gitignore` excludes `payload/`, `build/` and `dist/`. Keep the installer source, integration source and diffs, upstream source copies, GPL license, credits, both READMEs and `docs/images/`.

The binary texture payload is intentionally kept outside Git: the largest archive is about 86.5 MiB. The source checkout alone is not a complete end-user installer. Do not upload the entire bbport or game installation, local configuration, user saves, caches, account tokens or logs.

Create a GitHub Release for tag `v1.0.0` and attach:

- `Bloodborne-UI-4K-v1.0.0.zip`
- `SHA256SUMS.txt`

The supplied ZIP already includes `payload/` and is ready to extract and run. GitHub's automatically generated **Source code** archives do not include those textures.

## Rebuild from a working installation

Maintainer requirements: Python 3.10+; Windows PowerShell 5.1; the known supported bbport release. Pillow is needed only to regenerate comparison sheets.

```powershell
python tools/prepare_payload.py --bbport "D:\Games\bbport-windows"
python tests/test_installer.py --probe "D:\Games\bbport-windows\bin\bb-probe.exe"
python tools/build_release.py
```

`prepare_payload.py` reads the known working mod resources and native-UV helper, and creates ordinary copies. It regenerates minimal UI-only patched scripts from `upstream/`. It does not copy the personal camera fixes, game executable, saves, driver profiles or runtime caches. Review every integration diff and keep third-party attribution.

After changing payloads, rebuild `manifest.json` and rerun the tests. When updating to a different bbport version, first verify its source and runtime, port the changes explicitly and perform a real gameplay test. Do not make the installer accept unknown hashes to silence a version error.

## Release checklist

- Install and uninstall tests passed; `tests/last-results.json` is current.
- README compatibility and limitations match the actual build.
- Texture previews are labelled as texture comparisons.
- No personal paths, credentials, executable game dumps or save data are included.
- Full installer ZIP opens, all manifest files match, and `SHA256SUMS.txt` matches the final ZIP.
- Publish only after reviewing included third-party artwork permissions and preserving credits.

## По-русски

В репозиторий загружаются исходники этой папки с учётом `.gitignore`. Папки `payload`, `build` и `dist` коммитить не нужно. Полный готовый ZIP и `SHA256SUMS.txt` прикрепляются к релизу `v1.0.0`. Архивы **Source code**, которые GitHub создаёт автоматически, не заменяют установочный ZIP.

Для пересборки выполни три команды выше, подставив путь к совместимой рабочей установке. Перед публикацией другой версии проверь отпечатки исходников, изменения скриптов и работу в игре. Проверка файлов установщика сама по себе не подтверждает графический результат на новом порте.
