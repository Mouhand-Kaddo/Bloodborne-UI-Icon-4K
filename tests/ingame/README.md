# In-game tests

`run_scenario.ps1` starts the real game through bbport, plays a scripted scenario, checks the game log
and takes screenshots, then closes the game. Run it on a machine with the game installed; nothing
here runs in CI.

```powershell
powershell -ExecutionPolicy Bypass -File tests\ingame\run_scenario.ps1 -Port D:\Games\bbport-windows `
    -Scenario tests\ingame\hud.json -Out build\ingame\with-mod -FFmpeg C:\tools\ffmpeg.exe
# the same scenario with UI 4K switched off, for before/after comparisons:
powershell -ExecutionPolicy Bypass -File tests\ingame\run_scenario.ps1 -Port D:\Games\bbport-windows `
    -Scenario tests\ingame\hud.json -Out build\ingame\without-mod -FFmpeg C:\tools\ffmpeg.exe -WithoutMod
```

Each run writes the screenshots, zoomed crops, a copy of `last_run.log` and `report.json` (log checks,
step timings, pass/fail) to `-Out`.

## What it takes care of

- **Admin rights.** A "Run as administrator" compatibility flag on `Bloodborne.exe` would start the game
  elevated, and Windows then blocks this script's key presses and cannot let it close the game. The
  game is started with `__COMPAT_LAYER=RunAsInvoker`, for this run only.
- **Your saves.** The game runs on a copy of the bbport `user` folder (without shader caches) inside
  `-Out`, through `BB_USER_DIR`. Closing the game at the end cannot touch the real saves. `-RealSaves`
  turns this off.
- **Without the mod.** The launcher sets `BB_MODS_CONFIG` itself, so `-WithoutMod` adds UI 4K to
  `disabled` in `mods.json` for the run and writes the file's exact original bytes back afterwards.
- **HDR.** An 8-bit desktop capture clips bright HUD white and loses its antialiased edges, which makes
  icons look more jagged than they are. Frames are captured as 16-bit float (ffmpeg `ddagrab`,
  `output_fmt=rgbaf16`), scaled by `-HdrScale` (default 0.3) and converted to sRGB. `-HdrScale 0`
  captures plain 8-bit.
- **The log.** It is held open by the launcher, so it is read with shared access.

## Scenario steps (JSON array)

| Step | Fields | Does |
|---|---|---|
| `waitlog` | `pattern`, `seconds` | Waits for a regular expression to appear in the game log. |
| `wait` | `ms` | Sleeps. |
| `key` | `key`, `hold`, `times`, `gap` | Presses a key in the game window (`enter`, `escape`, `backspace`, arrows, `e`, `q`, `g`, `w` `a` `s` `d`, `space`, `tab`). |
| `snap` | `name`, `crops` | Screenshot; each crop `{name, x, y, w, h, zoom}` is saved enlarged (nearest neighbour). |
| `expectlog` | `label`, `pattern`, `absent`, `modOnly` | A pass/fail check on the log. `modOnly` checks are expected to fail with `-WithoutMod`. |

`hud.json`: title screen, *Play Offline*, *Continue*, the HUD with crops of the vial/bullet slots,
the quick item and Blood Echoes/Insight, then the equipment menu. `title.json`: title screen only.

Key presses are the bbport keyboard defaults (Return confirm, Escape menu). Coordinates in the
scenarios are for 2560×1440.
