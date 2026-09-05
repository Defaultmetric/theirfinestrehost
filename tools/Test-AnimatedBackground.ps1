param([string]$ModRoot = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$ModRoot = (Resolve-Path -LiteralPath $ModRoot).Path
$gfx = Get-Content -Raw -LiteralPath (Join-Path $ModRoot 'interface/tfr_backgrounds.gfx')
$refs = [regex]::Matches($gfx, '(?:texturefile|effectFile)\s*=\s*"([^"]+)"')
foreach ($ref in $refs) {
    $path = Join-Path $ModRoot $ref.Groups[1].Value
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing asset: $path" }
}
$include = Join-Path $ModRoot 'gfx/FX/tfr_flipbook.fxh'
if (!(Test-Path -LiteralPath $include)) { throw "Missing shader include: $include" }
$totalBytes = 0L
for ($i = 0; $i -lt 64; $i++) {
    $name = 'tfr_c{0:d2}' -f $i
    $path = Join-Path $ModRoot "gfx/interface/$name.dds"
    $data = [IO.File]::ReadAllBytes($path)
    if ($data.Length -ne 3864128 -or
        [Text.Encoding]::ASCII.GetString($data, 0, 4) -ne 'DDS ' -or
        [BitConverter]::ToUInt32($data, 16) -ne 4000 -or
        [BitConverter]::ToUInt32($data, 12) -ne 1932 -or
        [Text.Encoding]::ASCII.GetString($data, 84, 4) -ne 'DXT1') {
        throw "Unexpected atlas format or incomplete file: $path"
    }
    $totalBytes += $data.Length
}
Write-Output "PASS: all background sprite assets and shader include exist; 64 DXT1 atlases validated ($totalBytes bytes)."
Write-Output 'This checks package integrity, not in-game rendering or animation.'
