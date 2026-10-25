# SPDX-License-Identifier: GPL-2.0-or-later
# In-game test runner: starts bbport, plays a scripted scenario (keys, waits, screenshots), checks the
# game log, then closes the game. Maintainer tool; it never changes bbport.ini, mods.json or saves.
#
#   powershell -ExecutionPolicy Bypass -File tests\ingame\run_scenario.ps1 -Port D:\Games\bbport-windows `
#       -Scenario tests\ingame\hud.json -Out build\ingame\with-mod -FFmpeg C:\tools\ffmpeg.exe [-WithoutMod]
#
# The game is started with __COMPAT_LAYER=RunAsInvoker, so a "Run as administrator" compatibility flag
# on Bloodborne.exe does not elevate it: an elevated game would ignore this script's input and could
# not be closed by it. Screenshots use ffmpeg's Desktop Duplication capture (ddagrab), which also
# works with HDR output. -WithoutMod starts the same scenario with UI 4K disabled: the launcher
# sets BB_MODS_CONFIG itself, so mods.json is changed for the run and its exact bytes are put back. The game runs on a copy of the user folder (saves, settings made in
# game) under -Out unless -RealSaves is given, so closing it mid-game cannot touch the real saves.
param(
    [Parameter(Mandatory)][string]$Port,
    [Parameter(Mandatory)][string]$Scenario,
    [Parameter(Mandatory)][string]$Out,
    [Parameter(Mandatory)][string]$FFmpeg,
    [switch]$WithoutMod,
    [switch]$RealSaves,
    # Extra environment for this run only, e.g. a capture layer: -ExtraEnv @{VK_INSTANCE_LAYERS='...'}
    [hashtable]$ExtraEnv = @{},
    # HDR displays: frames are captured as 16-bit float (scRGB) and scaled by this before the sRGB
    # conversion, so bright HUD white is not clipped (an 8-bit capture loses its antialiased edges).
    # 0 captures plain 8-bit.
    [double]$HdrScale = 0.3,
    [int]$StartTimeout = 300
)
$ErrorActionPreference = 'Stop'
Add-Type @"
using System; using System.Runtime.InteropServices;
public class BBTest {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, UIntPtr e);
}
"@
[BBTest]::SetProcessDPIAware() | Out-Null
$Port = (Resolve-Path $Port).Path
$Out = [IO.Path]::GetFullPath($Out); New-Item -ItemType Directory -Force $Out | Out-Null
$steps = Get-Content $Scenario -Raw | ConvertFrom-Json
$logs = @((Join-Path $Port 'user\last_run.log'))
$keys = @{ enter=@(0x0D,0x1C,0); escape=@(0x1B,0x01,0); backspace=@(0x08,0x0E,0); up=@(0x26,0x48,1); down=@(0x28,0x50,1)
           left=@(0x25,0x4B,1); right=@(0x27,0x4D,1); e=@(0x45,0x12,0); q=@(0x51,0x10,0); g=@(0x47,0x22,0)
           w=@(0x57,0x11,0); a=@(0x41,0x1E,0); s=@(0x53,0x1F,0); d=@(0x44,0x20,0); space=@(0x20,0x39,0); tab=@(0x09,0x0F,0)
           f12=@(0x7B,0x58,0) }
$report = [ordered]@{ scenario = (Split-Path $Scenario -Leaf); withoutMod = [bool]$WithoutMod; started = (Get-Date).ToString('s');
                      steps = @(); checks = @(); passed = $true }

function Game { Get-Process bb-probe -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1 }
function Focus {
    $p = $null
    for ($i = 0; $i -lt 20 -and -not ($p = Game); $i++) { Start-Sleep -Milliseconds 500 }
    if (-not $p) {
        if (Get-Process bb-probe -ErrorAction SilentlyContinue) { throw 'The game is running but has no window (10 s).' }
        throw 'The game exited (crash or quit).'
    }
    for ($i = 0; $i -lt 8 -and [BBTest]::GetForegroundWindow() -ne $p.MainWindowHandle; $i++) {
        [BBTest]::keybd_event(0x12, 0x38, 0, [UIntPtr]::Zero); [BBTest]::keybd_event(0x12, 0x38, 2, [UIntPtr]::Zero)
        [BBTest]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; Start-Sleep -Milliseconds 250
    }
    if ([BBTest]::GetForegroundWindow() -ne $p.MainWindowHandle) { throw 'Could not bring the game to the front.' }
}
function Press([string]$name, [int]$hold = 120) {
    $k = $keys[$name]; if (-not $k) { throw "Unknown key $name" }
    Focus
    [BBTest]::keybd_event([byte]$k[0], [byte]$k[1], [uint32]$k[2], [UIntPtr]::Zero); Start-Sleep -Milliseconds $hold
    [BBTest]::keybd_event([byte]$k[0], [byte]$k[1], [uint32](2 -bor $k[2]), [UIntPtr]::Zero)
}
function Snap([string]$name, $crops) {
    Focus
    $file = Join-Path $Out "$name.png"
    if ($HdrScale -gt 0) {
        $k = $HdrScale.ToString([Globalization.CultureInfo]::InvariantCulture)
        & $FFmpeg -hide_banner -loglevel error -y -f lavfi -i "ddagrab=output_idx=0:framerate=10:output_fmt=rgbaf16,hwdownload,format=rgbaf16le,format=gbrpf32le,colorchannelmixer=rr=${k}:gg=${k}:bb=${k},zscale=tin=linear:t=iec61966-2-1:pin=bt709:p=bt709,format=rgb24" -frames:v 1 $file
    }
    if ($HdrScale -le 0 -or -not (Test-Path $file)) {
        & $FFmpeg -hide_banner -loglevel error -y -f lavfi -i 'ddagrab=output_idx=0:framerate=10,hwdownload,format=bgra' -frames:v 1 $file
    }
    foreach ($c in @($crops)) {
        if (-not $c) { continue }
        & $FFmpeg -hide_banner -loglevel error -y -i $file -vf "crop=$($c.w):$($c.h):$($c.x):$($c.y),scale=iw*$($c.zoom):ih*$($c.zoom):flags=neighbor" (Join-Path $Out "$name-$($c.name).png")
    }
}
function LogPath { foreach ($l in $logs) { if ((Test-Path $l) -and (Get-Item $l).LastWriteTime -ge $launched) { return $l } }; $null }
function LogText {
    $l = LogPath; if (-not $l) { return '' }
    # The launcher keeps the log open for writing: read it with shared access.
    try {
        $fs = New-Object IO.FileStream($l, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try { (New-Object IO.StreamReader($fs)).ReadToEnd() } finally { $fs.Dispose() }
    } catch { '' }
}
function WaitLog([string]$pattern, [int]$seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if ((LogText) -match $pattern) { return }
        if (-not (Get-Process bb-probe -ErrorAction SilentlyContinue) -and (Get-Date) -gt $launched.AddSeconds(60)) { throw 'The game exited.' }
        Start-Sleep -Milliseconds 500
    }
    throw "Timed out waiting for log: $pattern"
}

if (Get-Process bb-probe -ErrorAction SilentlyContinue) { throw 'Close the game before running a test.' }
$env:__COMPAT_LAYER = 'RunAsInvoker'
$config = Join-Path $Port 'mods.json'
$configBytes = if (Test-Path $config) { [IO.File]::ReadAllBytes($config) } else { $null }
if ($WithoutMod) {
    [IO.File]::WriteAllBytes((Join-Path $Out 'mods.json.before'), $(if ($configBytes) { $configBytes } else { [byte[]]@() }))
    $value = if ($configBytes) { [Text.Encoding]::UTF8.GetString($configBytes) | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $value.PSObject.Properties['disabled']) { $value | Add-Member NoteProperty disabled @() }
    $value.disabled = @(@($value.disabled) + 'UI 4K' | Select-Object -Unique)
    [IO.File]::WriteAllText($config, ($value | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false)))
}
if (-not $RealSaves) {
    $userCopy = Join-Path $Out 'user'
    if (Test-Path $userCopy) { Remove-Item $userCopy -Recurse -Force }
    # Shader caches are left out (large, rebuilt by the game); saves and settings are copied.
    robocopy (Join-Path $Port 'user') $userCopy /E /XD shader cache captures screenshots /NFL /NDL /NJH /NJS /NP | Out-Null
    $env:BB_USER_DIR = $userCopy
    $logs = @((Join-Path $userCopy 'last_run.log')) + $logs
} else { Remove-Item Env:BB_USER_DIR -ErrorAction SilentlyContinue }
foreach ($k in $ExtraEnv.Keys) { Set-Item "Env:$k" $ExtraEnv[$k] }
$launched = (Get-Date).AddSeconds(-2)
Start-Process -FilePath (Join-Path $Port 'Play Bloodborne.exe') -WorkingDirectory $Port | Out-Null
try {
    foreach ($step in $steps) {
        $t0 = Get-Date
        switch ($step.do) {
            'waitlog' { WaitLog $step.pattern ([int]($step.seconds | ForEach-Object { if ($_) { $_ } else { $StartTimeout } })) }
            'wait'    { Start-Sleep -Milliseconds ([int]$step.ms) }
            'key'     { foreach ($i in 1..([int]($step.times | ForEach-Object { if ($_) { $_ } else { 1 } }))) {
                            Press $step.key ([int]($step.hold | ForEach-Object { if ($_) { $_ } else { 120 } })); Start-Sleep -Milliseconds ([int]($step.gap | ForEach-Object { if ($_) { $_ } else { 500 } })) } }
            'snap'    { Snap $step.name $step.crops }
            'expectlog' {
                $found = (LogText) -match $step.pattern
                $want = -not $step.absent
                if ($WithoutMod -and $step.modOnly) { $want = -not $want }
                $ok = ($found -eq $want)
                $report.checks += [ordered]@{ check = $step.label; pattern = $step.pattern; expected = $want; found = $found; passed = $ok }
                if (-not $ok) { $report.passed = $false }
            }
            default { throw "Unknown step: $($step.do)" }
        }
        $report.steps += [ordered]@{ step = $step.do; detail = ($step | ConvertTo-Json -Compress -Depth 5); seconds = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1) }
    }
} catch {
    $report.passed = $false; $report.error = $_.Exception.Message
    try { Snap 'failure' $null } catch {}
} finally {
    Get-Process bb-probe, 'Play Bloodborne' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
    Get-Process Bloodborne -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$Port*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    $l = LogPath; if ($l) { Copy-Item $l (Join-Path $Out 'last_run.log') -Force; $report.log = $l }
    if ($WithoutMod) {
        if ($configBytes) { [IO.File]::WriteAllBytes($config, $configBytes) } elseif (Test-Path $config) { Remove-Item $config -Force }
        $report.modsJsonRestored = $true
    }
    Remove-Item Env:__COMPAT_LAYER, Env:BB_MODS_CONFIG, Env:BB_USER_DIR -ErrorAction SilentlyContinue
    foreach ($k in $ExtraEnv.Keys) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
    $report.finished = (Get-Date).ToString('s')
    [IO.File]::WriteAllText((Join-Path $Out 'report.json'), ($report | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))
}
"passed=$($report.passed) $(if ($report.error) { 'error=' + $report.error })"
