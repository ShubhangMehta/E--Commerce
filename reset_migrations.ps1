$ErrorActionPreference = "Stop"

$apps = @(
    "customers",
    "accounts",
    "catalog",
    "orders",
    "users",
    "themes",
    "dashboard",
    "payments",
    "notifications"
)

Write-Host "Deleting migration files..." -ForegroundColor Cyan

foreach ($app in $apps) {
    $migPath = Join-Path $PSScriptRoot "$app\migrations"
    if (Test-Path $migPath) {
        Get-ChildItem $migPath -File |
            Where-Object { $_.Name -ne "__init__.py" } |
            Remove-Item -Force
        Write-Host "Cleaned: $migPath"
    }
    else {
        Write-Host "Skipped (not found): $migPath" -ForegroundColor Yellow
    }
}

Write-Host "Deleting __pycache__ folders..." -ForegroundColor Cyan

foreach ($app in $apps) {
    $cachePath = Join-Path $PSScriptRoot "$app\migrations\__pycache__"
    if (Test-Path $cachePath) {
        Remove-Item $cachePath -Recurse -Force
        Write-Host "Removed: $cachePath"
    }
}

Write-Host "Running makemigrations..." -ForegroundColor Cyan
foreach ($app in $apps) {
    & "$PSScriptRoot\venv\Scripts\python.exe" manage.py makemigrations $app
}

Write-Host "Running migrate..." -ForegroundColor Cyan
& "$PSScriptRoot\venv\Scripts\python.exe" manage.py migrate_schemas

Write-Host "Done." -ForegroundColor Green