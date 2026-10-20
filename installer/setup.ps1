# SPDX-License-Identifier: GPL-2.0-or-later
param([ValidateSet('Install','Uninstall','Verify','Validate')][string]$Action='Install',
      [string]$Target='', [switch]$NoGui,
      [ValidateSet('en','ru','')][string]$Language='', [string]$PreviewPath='')
. (Join-Path $PSScriptRoot 'engine.ps1')
function Invoke-Action([string]$SelectedAction,[string]$Folder) {
    if (-not $Folder) {throw 'Select a bbport folder first.'}
    switch ($SelectedAction) {
        Install {Install-Package $Folder}
        Uninstall {Uninstall-Package $Folder}
        Verify {Test-Installation $Folder}
        Validate {Get-TargetReadiness $Folder | ConvertTo-Json -Compress}
    }
}
if ($NoGui) {
    try {Invoke-Action $Action $Target;exit 0}
    catch {Write-Error $_ -ErrorAction Continue;exit 1}
}
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$form=New-Object Windows.Forms.Form
$form.Text='Bloodborne UI 4K';$form.ClientSize=New-Object Drawing.Size(680,385)
$form.StartPosition='CenterScreen';$form.FormBorderStyle='FixedDialog';$form.MaximizeBox=$false
$form.Font=New-Object Drawing.Font('Segoe UI',10)
$lang=New-Object Windows.Forms.ComboBox
$lang.Location=New-Object Drawing.Point(500,18);$lang.Size=New-Object Drawing.Size(155,28)
$lang.DropDownStyle='DropDownList';$lang.Items.AddRange(@('English','Russian'))
$lang.SelectedIndex=if ([Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName -eq 'ru') {1} else {0}
if ($Language) {$lang.SelectedIndex=if ($Language -eq 'ru') {1} else {0}}
$form.Controls.Add($lang)
$label=New-Object Windows.Forms.Label;$label.Location=New-Object Drawing.Point(22,25);$label.Size=New-Object Drawing.Size(465,30)
$form.Controls.Add($label)
$pathBox=New-Object Windows.Forms.TextBox;$pathBox.Location=New-Object Drawing.Point(22,68);$pathBox.Size=New-Object Drawing.Size(520,28)
$pathBox.Text=$Target;$form.Controls.Add($pathBox)
$browse=New-Object Windows.Forms.Button;$browse.Location=New-Object Drawing.Point(550,66);$browse.Size=New-Object Drawing.Size(105,32)
$form.Controls.Add($browse)
$validation=New-Object Windows.Forms.Label
$validation.Location=New-Object Drawing.Point(22,103);$validation.Size=New-Object Drawing.Size(632,69)
$validation.Font=New-Object Drawing.Font('Segoe UI',9)
$form.Controls.Add($validation)
$info=New-Object Windows.Forms.Label;$info.Location=New-Object Drawing.Point(22,184);$info.Size=New-Object Drawing.Size(630,78)
$form.Controls.Add($info)
$install=New-Object Windows.Forms.Button;$install.Location=New-Object Drawing.Point(22,280);$install.Size=New-Object Drawing.Size(307,42)
$remove=New-Object Windows.Forms.Button;$remove.Location=New-Object Drawing.Point(347,280);$remove.Size=New-Object Drawing.Size(307,42)
$form.Controls.AddRange(@($install,$remove))
$status=New-Object Windows.Forms.Label;$status.Location=New-Object Drawing.Point(22,338);$status.Size=New-Object Drawing.Size(630,38)
$form.Controls.Add($status)
$timer=New-Object Windows.Forms.Timer;$timer.Interval=450
$script:Busy=$false;$script:Ready=$false;$script:Installed=$false
function Get-ValidationError([string]$Detail) {
    switch -Regex ($Detail) {
        '^Select the existing bbport folder' {return $script:Ui.path_missing}
        '^Missing bbport file: (.*)' {return ($script:Ui.not_bbport+' '+$Matches[1])}
        '^Unsupported or modified bbport file: ([^.]+\.py|[^.]+\.exe)' {return ($script:Ui.unsupported+' '+$Matches[1])}
        '^Close Bloodborne' {return $script:Ui.close_game}
        '^Incomplete installation state' {return $script:Ui.incomplete_state}
        '^Installed file changed or missing: (.*)' {return ($script:Ui.installed_damage+' '+$Matches[1])}
        '^Backup failed verification: (.*)' {return ($script:Ui.backup_damage+' '+$Matches[1])}
        '^Incomplete source checkout' {return $script:Ui.incomplete_payload}
        '^Damaged installer payload: (.*)' {return ($script:Ui.damaged_payload+' '+$Matches[1])}
        '^Read-only destination.*: (.*)' {return ($script:Ui.read_only+' '+$Matches[1])}
        '^A different mod already uses this path: (.*?)\. Move' {return ($script:Ui.conflict+' '+$Matches[1])}
        '^An existing inventory_icons.py' {return ($script:Ui.conflict+' scripts/inventory_icons.py')}
        'access.*denied|denied.*access|UnauthorizedAccess|\u043e\u0442\u043a\u0430\u0437\u0430\u043d\u043e|\u0434\u043e\u0441\u0442\u0443\u043f.*\u0437\u0430\u043f\u0440\u0435\u0449' {return $script:Ui.access_denied}
        default {return ($script:Ui.path_problem+' '+$Detail)}
    }
}
function Update-Readiness {
    $timer.Stop()
    if ($script:Busy) {return}
    $install.Enabled=$false;$remove.Enabled=$false
    $validation.ForeColor=[Drawing.Color]::Firebrick
    if ([string]::IsNullOrWhiteSpace($pathBox.Text)) {
        $validation.Text=$script:Ui.path_empty;$script:Ready=$false;return
    }
    $validation.Text=$script:Ui.path_checking;$form.Refresh()
    $result=Get-TargetReadiness $pathBox.Text.Trim()
    $script:Ready=[bool]$result.ready;$script:Installed=$result.mode -eq 'Installed'
    if ($script:Ready) {
        $validation.ForeColor=[Drawing.Color]::ForestGreen
        $validation.Text=if ($script:Installed) {$script:Ui.path_installed} else {$script:Ui.path_valid}
        $install.Enabled=-not $script:Installed;$remove.Enabled=$script:Installed
    } else {
        $validation.ForeColor=[Drawing.Color]::Firebrick
        $validation.Text=Get-ValidationError $result.detail
    }
}
function Queue-Validation {
    if ($script:Busy) {return}
    $script:Ready=$false;$install.Enabled=$false;$remove.Enabled=$false
    $validation.ForeColor=[Drawing.Color]::Firebrick
    $validation.Text=if ([string]::IsNullOrWhiteSpace($pathBox.Text)) {$script:Ui.path_empty} else {$script:Ui.path_checking}
    $timer.Stop();$timer.Start()
}
function Set-Language {
    $name=if ($lang.SelectedIndex -eq 1) {'ru'} else {'en'}
    $script:Ui=Read-JsonFile (Join-Path $PSScriptRoot ('locale/'+$name+'.json'))
    $label.Text=$script:Ui.folder;$browse.Text=$script:Ui.browse;$info.Text=$script:Ui.info
    $install.Text=$script:Ui.install;$remove.Text=$script:Ui.remove;$status.Text=$script:Ui.ready
    Queue-Validation
}
$timer.Add_Tick({Update-Readiness})
$pathBox.Add_TextChanged({Queue-Validation})
$lang.Add_SelectedIndexChanged({Set-Language})
$form.Add_Activated({if (-not $script:Busy) {Queue-Validation}})
$browse.Add_Click({
    $dialog=New-Object Windows.Forms.FolderBrowserDialog
    $dialog.Description=$script:Ui.folder;$dialog.ShowNewFolderButton=$false
    try {
        if ($pathBox.Text -and (Test-Path -LiteralPath $pathBox.Text)) {$dialog.SelectedPath=$pathBox.Text}
        if ($dialog.ShowDialog($form) -eq 'OK') {$pathBox.Text=$dialog.SelectedPath;Update-Readiness}
    } catch {
        $validation.ForeColor=[Drawing.Color]::Firebrick;$validation.Text=Get-ValidationError $_.Exception.Message
    } finally {$dialog.Dispose()}
})
function Run-UiAction([string]$SelectedAction) {
    Update-Readiness
    if (-not $script:Ready) {return}
    $script:Busy=$true;$timer.Stop();$install.Enabled=$false;$remove.Enabled=$false
    $browse.Enabled=$false;$pathBox.Enabled=$false;$lang.Enabled=$false;$form.UseWaitCursor=$true
    $status.Text=$script:Ui.working;$form.Refresh();$failure=$null
    try {
        $result=Invoke-Action $SelectedAction $pathBox.Text.Trim()
        $status.ForeColor=[Drawing.Color]::ForestGreen
        $status.Text=if ($SelectedAction -eq 'Install') {$script:Ui.installed} else {$script:Ui.removed}
    } catch {
        $failure=$_.Exception.Message;$status.ForeColor=[Drawing.Color]::Firebrick;$status.Text=$script:Ui.failed
    } finally {
        $script:Busy=$false;$browse.Enabled=$true;$pathBox.Enabled=$true;$lang.Enabled=$true;$form.UseWaitCursor=$false
        Update-Readiness
        if ($failure) {$validation.ForeColor=[Drawing.Color]::Firebrick;$validation.Text=Get-ValidationError $failure}
    }
}
$install.Add_Click({Run-UiAction 'Install'});$remove.Add_Click({Run-UiAction 'Uninstall'})
Set-Language
if ($PreviewPath) {
    $form.ShowInTaskbar=$false;$form.StartPosition='Manual'
    $form.Location=New-Object Drawing.Point(-32000,-32000)
    $form.Show();[Windows.Forms.Application]::DoEvents();Update-Readiness;$form.PerformLayout()
    $bitmap=New-Object Drawing.Bitmap($form.Width,$form.Height)
    $form.DrawToBitmap($bitmap,(New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)))
    $bitmap.Save([IO.Path]::GetFullPath($PreviewPath),[Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose();$timer.Dispose();$form.Dispose();exit 0
}
[Windows.Forms.Application]::Run($form)
$timer.Dispose();$form.Dispose()
