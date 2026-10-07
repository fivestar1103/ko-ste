param([switch]$Claude, [switch]$Codex)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\skills\ko-ste')).Path
if (-not $Claude -and -not $Codex) { $Claude = $true; $Codex = $true }
$locations = @()
if ($Claude) { $locations += '.claude' }
if ($Codex) { $locations += '.agents' }
$records = @()
foreach ($location in $locations) {
    $appRoot = Join-Path $env:USERPROFILE $location
    $skillsRoot = Join-Path $appRoot 'skills'
    $targetPath = [IO.Path]::GetFullPath((Join-Path $skillsRoot 'ko-ste'))
    if ($targetPath -ne [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "$location\skills\ko-ste"))) { throw 'Unexpected target path' }
    New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
    $backupPath = $null
    if (Test-Path -LiteralPath $targetPath) {
        $old = Get-Item -LiteralPath $targetPath -Force
        if ($old.LinkType -eq 'Junction' -and $old.Target -eq $sourcePath) {
            $records += [pscustomobject]@{ app=$location; target=$targetPath; source=$sourcePath; backup=$null; status='already-linked' }
            continue
        }
        if ($old.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Existing link differs: $targetPath" }
        $backupRoot = Join-Path $appRoot 'backups'
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        $backupPath = [IO.Path]::GetFullPath((Join-Path $backupRoot ('ko-ste-before-codex-' + [guid]::NewGuid().ToString('N'))))
        if (-not $backupPath.StartsWith([IO.Path]::GetFullPath($backupRoot) + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected backup path' }
        # Rollback: remove only the newly created junction, then move this exact backup back.
        Move-Item -LiteralPath $targetPath -Destination $backupPath
    }
    try {
        New-Item -ItemType Junction -Path $targetPath -Value $sourcePath | Out-Null
    } catch {
        if ($backupPath -and -not (Test-Path -LiteralPath $targetPath)) { Move-Item -LiteralPath $backupPath -Destination $targetPath }
        throw
    }
    $records += [pscustomobject]@{ app=$location; target=$targetPath; source=$sourcePath; backup=$backupPath; status='linked' }
}
$localRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.local'
New-Item -ItemType Directory -Path $localRoot -Force | Out-Null
$records | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $localRoot 'installation.json') -Encoding utf8
$records | Format-Table app,status,target,source -AutoSize
