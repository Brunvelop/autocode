param(
    [string]$OutputPath = "reports/git/staged-diff.md"
)

# Forzar UTF-8 en la salida de procesos externos (como git)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Comprueba que git está disponible
try {
    git --version *> $null
} catch {
    Write-Error "git no está disponible en el PATH."
    exit 1
}

# Comprueba que estamos dentro de un repositorio git
try {
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Este script debe ejecutarse dentro de un repositorio git."
        exit 1
    }
} catch {
    Write-Error "Error comprobando el estado del repositorio git."
    exit 1
}

# Obtiene la rama actual
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) {
    $branch = "(desconocida)"
}

# Asegura que existe el directorio de salida
$directory = Split-Path -Parent $OutputPath
if ($directory -and -not (Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$now = Get-Date

# Obtiene el diff de los cambios en staging
$stagedDiff = git --no-pager diff --cached

# Verifica si hay cambios en staging
if (-not $stagedDiff) {
    Write-Host "No hay cambios en staging (cached)."
    $stagedDiff = "(Sin cambios en staging)"
}

# Construye el header línea a línea para evitar problemas de comillas
$headerLines = @()
$headerLines += '# Cambios en staging (cached)'
$headerLines += ''
$headerLines += ("Generado: {0}" -f $now.ToString("yyyy-MM-dd HH:mm:ss"))
$headerLines += "Rama: $branch"
$headerLines += ''
$headerLines += '---'
$headerLines += ''
$headerLines += '```diff'

$header = $headerLines -join [Environment]::NewLine

$footer = [Environment]::NewLine + '```' + [Environment]::NewLine

# Escribe el archivo markdown
$header | Set-Content -Path $OutputPath -Encoding UTF8
$stagedDiff | Add-Content -Path $OutputPath -Encoding UTF8
$footer | Add-Content -Path $OutputPath -Encoding UTF8

Write-Host "Archivo generado: $OutputPath"
