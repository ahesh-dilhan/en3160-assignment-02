$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$archivePath = Join-Path $projectRoot 'a2images.zip'
$destination = Join-Path $projectRoot 'images'
$expectedHash = 'FA44D5F830872A69144AA16351E0265CDB2E1AEE4F9922A8327EB12D75F4638E'
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'Archive checksum differs from the reviewed assignment data.'
}
$expectedFiles = @(
    'flag.png', 'the_berry_farms_sunflower_field.jpeg', 'wadham.jpg',
    'pcbs/AAAA1.jpg', 'pcbs/ADAD1.jpg', 'pcbs/AECC1.jpg',
    'pcbs/AECC2.jpg', 'pcbs/AECC3.jpg', 'pcbs/AECC4.jpg'
)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $entries = @($archive.Entries | Where-Object { $_.Name -ne '' })
    $actualFiles = @($entries | ForEach-Object { $_.FullName -replace '^a2images/', '' })
    if (Compare-Object $expectedFiles $actualFiles) { throw 'Unexpected archive contents.' }
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    foreach ($entry in $entries) {
        $relativePath = $entry.FullName -replace '^a2images/', ''
        $outputPath = Join-Path $destination $relativePath
        New-Item -ItemType Directory -Force -Path (Split-Path $outputPath -Parent) | Out-Null
        # Keep any existing input untouched. Confirm it matches rather than overwriting.
        $inputStream = $entry.Open()
        try {
            if (Test-Path -LiteralPath $outputPath) {
                $sha = [Security.Cryptography.SHA256]::Create()
                try { $entryHash = [BitConverter]::ToString($sha.ComputeHash($inputStream)).Replace('-', '') }
                finally { $sha.Dispose() }
                if ((Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash -ne $entryHash) {
                    throw "Existing file differs: $relativePath"
                }
            } else {
                $outputStream = [IO.File]::Create($outputPath)
                try { $inputStream.CopyTo($outputStream) } finally { $outputStream.Dispose() }
            }
        } finally { $inputStream.Dispose() }
    }
    Write-Output "Validated and prepared $($entries.Count) images in $destination"
} finally { $archive.Dispose() }
