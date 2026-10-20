# SPDX-License-Identifier: GPL-2.0-or-later
# Windows PowerShell 5.1. No external runtime, elevation, links, or game process required.
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:PackageRoot = Split-Path $PSScriptRoot -Parent
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OwnedMods = @('Keyboard Prompts (PCBButtons)','UI 4K','Inventory Icons 4K')

function Read-JsonFile([string]$Path) {
    return ([IO.File]::ReadAllText($Path,$script:Utf8) | ConvertFrom-Json)
}
function Write-JsonFile([string]$Path,$Value) {
    [IO.File]::WriteAllText($Path,($Value | ConvertTo-Json -Depth 20),$script:Utf8)
}
function Get-Digest([string]$Path) {
    $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
    finally {$sha.Dispose();$stream.Dispose()}
}
function Get-TextDigest([string]$Path) {
    $text=[IO.File]::ReadAllText($Path,$script:Utf8).Replace("`r`n","`n")
    $sha=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($sha.ComputeHash($script:Utf8.GetBytes($text)))).Replace('-','').ToLowerInvariant()}
    finally {$sha.Dispose()}
}
function Get-SafePath([string]$Root,[string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative)) {throw "Absolute payload path refused: $Relative"}
    $base=[IO.Path]::GetFullPath($Root).TrimEnd('\')
    $full=[IO.Path]::GetFullPath((Join-Path $base $Relative))
    if (-not $full.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)) {throw "Unsafe path: $Relative"}
    $cursor=$full
    while ($cursor -and $cursor.Length -ge $base.Length) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Linked installation paths are unsupported: $cursor"
            }
        }
        $cursor=[IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}
function Assert-GameClosed {
    if (Get-Process -Name 'bb-probe','bb-probe-mouse-no-autorotate','Bloodborne','Play Bloodborne' -ErrorAction SilentlyContinue) {
        throw 'Close Bloodborne and the bbport launcher before installing or removing this package.'
    }
}
function Read-ModConfig([string]$Path) {
    if (Test-Path -LiteralPath $Path) {$value=Read-JsonFile $Path} else {$value=New-Object PSObject}
    foreach ($key in @('enabled','disabled','order')) {
        if (-not $value.PSObject.Properties[$key]) {$value | Add-Member NoteProperty $key @()}
        if ($null -eq $value.$key) {$value.$key=@()}
        foreach ($name in @($value.$key)) {if ($name -isnot [string]) {throw "Invalid mods.json: $key"}}
    }
    return $value
}
function Get-InstallConfig($Before) {
    $value=$Before | ConvertTo-Json -Depth 20 | ConvertFrom-Json
    foreach ($key in @('enabled','disabled','order')) {
        $value.$key=@($value.$key | Where-Object {$_ -notin $script:OwnedMods})
    }
    $value.enabled=@($value.enabled)+$script:OwnedMods
    $value.order=@($value.order)+$script:OwnedMods
    if ('Xbox 360 Prompts (Elden Ring)' -notin @($value.disabled)) {
        $value.disabled=@($value.disabled)+@('Xbox 360 Prompts (Elden Ring)')
    }
    return $value
}
function Clear-State([string]$StateRoot) {
    # Delete only ordinary files and empty directories in our private state directory.
    if (-not (Test-Path -LiteralPath $StateRoot)) {return}
    $entries=@(Get-ChildItem -LiteralPath $StateRoot -Recurse -Force)
    if (@($entries | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count) {
        throw 'Linked backup paths refused; state retained.'
    }
    foreach ($item in @($entries | Where-Object {-not $_.PSIsContainer})) {[IO.File]::Delete($item.FullName)}
    foreach ($item in @($entries | Where-Object {$_.PSIsContainer} | Sort-Object {$_.FullName.Length} -Descending)) {
        [IO.Directory]::Delete($item.FullName)
    }
    [IO.Directory]::Delete($StateRoot)
}
function Restore-Files([string]$Target,[string]$StateRoot,$State) {
    foreach ($entry in @($State.files)) {
        $path=Get-SafePath $Target $entry.target
        if ($entry.existed) {
            $source=Get-SafePath $StateRoot ('backup/'+$entry.target)
            if ((Get-Digest $source) -ne $entry.beforeHash) {throw "Damaged backup: $($entry.target)"}
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
            [IO.File]::Copy($source,$path,$true)
        } elseif (Test-Path -LiteralPath $path) {[IO.File]::Delete($path)}
    }
    foreach ($relative in @($State.createdDirectories | Sort-Object Length -Descending)) {
        $path=Get-SafePath $Target $relative
        if ((Test-Path -LiteralPath $path) -and @(Get-ChildItem -LiteralPath $path -Force).Count -eq 0) {
            [IO.Directory]::Delete($path)
        }
    }
}
function Test-Installation([string]$Target) {
    $stateRoot=Get-SafePath $Target '.bbport-ui4k'
    $state=Read-JsonFile (Join-Path $stateRoot 'state.json')
    foreach ($entry in @($state.files)) {
        $path=Get-SafePath $Target $entry.target
        if (-not (Test-Path -LiteralPath $path) -or (Get-Digest $path) -ne $entry.installedHash) {
            throw "Installed file changed or missing: $($entry.target)"
        }
    }
    return "Verified $(@($state.files).Count) installed files."
}
function Get-PackagePreflight([string]$Target) {
    Assert-GameClosed
    if ([string]::IsNullOrWhiteSpace($Target)) {throw 'Select the existing bbport folder.'}
    $Target=[IO.Path]::GetFullPath($Target)
    if (-not (Test-Path -LiteralPath $Target -PathType Container)) {throw 'Select the existing bbport folder.'}
    if (-not (Test-Path -LiteralPath (Get-SafePath $Target 'Bloodborne.exe') -PathType Leaf)) {throw 'Missing bbport file: Bloodborne.exe'}
    $manifest=Read-JsonFile (Join-Path $script:PackageRoot 'manifest.json')
    $stateRoot=Get-SafePath $Target '.bbport-ui4k'
    if (Test-Path -LiteralPath $stateRoot) {
        if (-not (Test-Path -LiteralPath (Join-Path $stateRoot 'state.json'))) {throw 'Incomplete installation state: restore or remove it before retrying.'}
        Test-Installation $Target | Out-Null
        $installed=Read-JsonFile (Join-Path $stateRoot 'state.json')
        foreach ($entry in @($installed.files)) {
            if ($entry.existed -and (Get-Digest (Get-SafePath $stateRoot ('backup/'+$entry.target))) -ne $entry.beforeHash) {
                throw "Backup failed verification: $($entry.target)"
            }
        }
        return @{mode='Installed';target=$Target;stateRoot=$stateRoot}
    }
    foreach ($inputFile in @($manifest.inputs)) {
        $path=Get-SafePath $Target $inputFile.path
        if (-not (Test-Path -LiteralPath $path)) {throw "Missing bbport file: $($inputFile.path)"}
        $hash=if ($inputFile.text) {Get-TextDigest $path} else {Get-Digest $path}
        if ($hash -ne $inputFile.sha256) {throw "Unsupported or modified bbport file: $($inputFile.path). Use clean Launcher 1.9.7 / qml-launcher-preview-21."}
    }
    $configPath=Get-SafePath $Target 'mods.json'
    $before=Read-ModConfig $configPath
    $after=Get-InstallConfig $before
    $plan=@();$directories=@()
    # Preflight every payload file before changing the target.
    foreach ($entry in @($manifest.files)) {
        $source=Get-SafePath $script:PackageRoot $entry.source
        if (-not (Test-Path -LiteralPath $source)) {throw 'Incomplete source checkout. Download the full installer ZIP from GitHub Releases.'}
        if ((Get-Digest $source) -ne $entry.sha256) {throw "Damaged installer payload: $($entry.source)"}
        $path=Get-SafePath $Target $entry.target
        $exists=Test-Path -LiteralPath $path
        if ($exists -and (Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReadOnly) {
            throw "Read-only destination refused before installation: $($entry.target)"
        }
        $oldHash=if ($exists) {Get-Digest $path} else {''}
        if ($exists -and $entry.kind -eq 'asset' -and $oldHash -ne $entry.sha256) {
            throw "A different mod already uses this path: $($entry.target). Move that mod out first."
        }
        if ($exists -and $entry.target -eq 'scripts/inventory_icons.py' -and $oldHash -ne $entry.sha256) {
            throw 'An existing inventory_icons.py would be overwritten. Keep it separately first.'
        }
        $plan+=@{target=$entry.target;source=$entry.source;existed=[bool]$exists;beforeHash=$oldHash;installedHash=$entry.sha256}
        $parent=[IO.Path]::GetDirectoryName($path)
        while ($parent.Length -gt $Target.TrimEnd('\').Length -and -not (Test-Path -LiteralPath $parent)) {
            $relative=$parent.Substring($Target.TrimEnd('\').Length+1)
            if ($relative -notin $directories) {$directories+=@($relative)}
            $parent=[IO.Path]::GetDirectoryName($parent)
        }
    }
    $state=@{version=$manifest.version;files=$plan;createdDirectories=$directories;
             configExisted=[bool](Test-Path -LiteralPath $configPath);configBefore=$before;configInstalledHash=''}
    return @{mode='Install';target=$Target;stateRoot=$stateRoot;state=$state;plan=$plan;configPath=$configPath;after=$after}
}
function Get-TargetReadiness([string]$Target) {
    try {
        $result=Get-PackagePreflight $Target
        # A disposable empty file checks actual write access without changing any existing file.
        $probe=Get-SafePath $result.target ('.bbport-ui4k-access-'+[Guid]::NewGuid().ToString('N')+'.tmp')
        $stream=New-Object IO.FileStream($probe,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,
                                        [IO.FileShare]::None,4096,[IO.FileOptions]::DeleteOnClose)
        $stream.Dispose()
        return @{ready=$true;mode=$result.mode;detail=''}
    } catch {
        return @{ready=$false;mode='Invalid';detail=$_.Exception.Message}
    }
}
function Install-Package([string]$Target) {
    $preflight=Get-PackagePreflight $Target
    if ($preflight.mode -eq 'Installed') {return 'This package is already installed. Its files passed verification.'}
    $Target=$preflight.target;$stateRoot=$preflight.stateRoot;$state=$preflight.state
    $plan=$preflight.plan;$configPath=$preflight.configPath;$after=$preflight.after
    [IO.Directory]::CreateDirectory($stateRoot) | Out-Null
    try {
        foreach ($entry in $plan) {
            if ($entry.existed) {
                $backup=Get-SafePath $stateRoot ('backup/'+$entry.target)
                [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($backup)) | Out-Null
                [IO.File]::Copy((Get-SafePath $Target $entry.target),$backup,$false)
            }
        }
        if ($state.configExisted) {[IO.File]::Copy($configPath,(Join-Path $stateRoot 'mods.json.before'),$false)}
    } catch {Clear-State $stateRoot;throw}
    Write-JsonFile (Join-Path $stateRoot 'state.json') $state
    try {
        foreach ($entry in $plan) {
            $path=Get-SafePath $Target $entry.target
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
            [IO.File]::Copy((Get-SafePath $script:PackageRoot $entry.source),$path,$true)
        }
        Write-JsonFile $configPath $after
        $state.configInstalledHash=Get-Digest $configPath
        Write-JsonFile (Join-Path $stateRoot 'state.json') $state
        Test-Installation $Target | Out-Null
    } catch {
        $reason=$_
        Restore-Files $Target $stateRoot $state
        if ($state.configExisted) {[IO.File]::Copy((Join-Path $stateRoot 'mods.json.before'),$configPath,$true)}
        elseif (Test-Path -LiteralPath $configPath) {[IO.File]::Delete($configPath)}
        Clear-State $stateRoot
        throw $reason
    }
    return 'Installed. Launch bbport normally. For the tested 4K text result, select 3840 x 2160 and restart the game.'
}
function Uninstall-Package([string]$Target) {
    Assert-GameClosed
    $stateRoot=Get-SafePath $Target '.bbport-ui4k'
    $state=Read-JsonFile (Join-Path $stateRoot 'state.json')
    # Never overwrite a newer runtime, a user edit, or a damaged backup.
    Test-Installation $Target | Out-Null
    foreach ($entry in @($state.files)) {
        if ($entry.existed -and (Get-Digest (Get-SafePath $stateRoot ('backup/'+$entry.target))) -ne $entry.beforeHash) {
            throw "Backup failed verification: $($entry.target)"
        }
    }
    $configPath=Get-SafePath $Target 'mods.json'
    $unchanged=(Test-Path -LiteralPath $configPath) -and (Get-Digest $configPath) -eq $state.configInstalledHash
    $current=Read-ModConfig $configPath
    Restore-Files $Target $stateRoot $state
    if ($unchanged) {
        if ($state.configExisted) {[IO.File]::Copy((Join-Path $stateRoot 'mods.json.before'),$configPath,$true)}
        else {[IO.File]::Delete($configPath)}
    } else {
        # Preserve later unrelated mod choices; restore this package's original entries.
        $managed=@($script:OwnedMods)+@('Xbox 360 Prompts (Elden Ring)')
        foreach ($key in @('enabled','disabled','order')) {
            $current.$key=@($current.$key | Where-Object {$_ -notin $managed})
            $original=@($state.configBefore.$key)
            for ($i=0;$i -lt $original.Count;$i++) {
                if ($original[$i] -in $managed) {
                    $list=New-Object 'System.Collections.Generic.List[string]'
                    foreach ($name in @($current.$key)) {$list.Add($name)}
                    $list.Insert([Math]::Min($i,$list.Count),$original[$i]);$current.$key=@($list.ToArray())
                }
            }
        }
        Write-JsonFile $configPath $current
    }
    Clear-State $stateRoot
    return 'Removed. Original scripts and previous mod choices restored. Launch bbport normally.'
}
