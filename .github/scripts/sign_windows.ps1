# Скрипт подписи Windows-сборки self-signed сертификатом
# Этап 3: Code Signing (Windows)
param(
    [string]$PfxBase64,
    [string]$PfxPassword,
    [string]$ExePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Windows Code Signing ==="
Write-Host "Signing: $ExePath"

# 1. Декодируем PFX из base64
$pfxBytes = [System.Convert]::FromBase64String($PfxBase64)
$pfxPath = Join-Path $env:TEMP "alchemy_cert.pfx"
[System.IO.File]::WriteAllBytes($pfxPath, $pfxBytes)

Write-Host "Certificate loaded from secrets."

# 2. Ищем signtool.exe (Windows SDK)
$signtoolPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.17763.0\x64\signtool.exe"
)

$signtool = $null
foreach ($path in $signtoolPaths) {
    if (Test-Path $path) {
        $signtool = $path
        break
    }
}

if (-not $signtool) {
    Write-Error "signtool.exe not found!"
    exit 1
}

Write-Host "Using signtool: $signtool"

# 3. Подписываем с timestamp
& $signtool sign /f $pfxPath /p $PfxPassword `
    /tr http://timestamp.digicert.com /td sha256 /fd sha256 `
    /v $ExePath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Code signing failed!"
    exit 1
}

# 4. Проверяем подпись
Write-Host "`n=== Signature Verification ==="
$sig = Get-AuthenticodeSignature -FilePath $ExePath
Write-Host "Status: $($sig.Status)"
Write-Host "Signer: $($sig.SignerCertificate.Subject)"

# 5. Удаляем временный PFX
Remove-Item $pfxPath -Force

Write-Host "`n=== Windows signing completed successfully! ==="