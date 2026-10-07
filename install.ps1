[CmdletBinding()]
param([string]$SkillsRoot = '', [switch]$Update, [switch]$WithRenderedQa)
$ErrorActionPreference = 'Stop'
if (-not $SkillsRoot) {
    if ($env:CODEX_HOME) { $SkillsRoot = Join-Path $env:CODEX_HOME 'skills' }
    else { $SkillsRoot = Join-Path $env:USERPROFILE '.codex\skills' }
}
$destination = Join-Path $SkillsRoot 'skill-drawio-pj'
$sourceRoot = $PSScriptRoot
$marker = Join-Path $destination '.skill-drawio-pj-install.json'
if (Test-Path -LiteralPath $destination) {
    if (-not $Update) { throw "Destination exists. Use -Update for this project's managed installation: $destination" }
    if (-not (Test-Path -LiteralPath $marker)) { throw 'Refusing to overwrite an unmanaged skill directory.' }
    $record = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($record.project -ne 'CZPavel/Skill_Drawio_PJ') { throw 'Installation ownership mismatch.' }
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null
# Copy only the runnable skill package, not research, Git history or benchmarks.
foreach ($item in @('SKILL.md','LICENSE','THIRD_PARTY_NOTICES.md','requirements.txt','package.json','package-lock.json','references','scripts','assets','agents')) {
    Copy-Item -LiteralPath (Join-Path $sourceRoot $item) -Destination $destination -Recurse -Force
}
@{ project='CZPavel/Skill_Drawio_PJ'; source=$sourceRoot; installedUtc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding UTF8
if ($WithRenderedQa) {
    $npmCommand = Get-Command npm.cmd,npm -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $npmCommand) { throw 'Node/npm is required for -WithRenderedQa. Skill files were installed.' }
    & $npmCommand.Source ci --prefix $destination
    if ($LASTEXITCODE -ne 0) { throw 'Rendered QA dependency installation failed.' }
    & $npmCommand.Source --prefix $destination exec -- playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
}
Write-Output "Installed: $destination"
Write-Output 'Invoke $skill-drawio-pj in a new chat. Existing official skills were preserved.'
