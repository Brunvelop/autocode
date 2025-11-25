param(
    [int]$LastNCommits = 30,
    [string]$OutputPath = "reports/git/commits-context.md"
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

# Construye el header línea a línea para evitar problemas de comillas
$headerLines = @()
$headerLines += '# Historial reciente de commits'
$headerLines += ''
$headerLines += ("Generado: {0}" -f $now.ToString("yyyy-MM-dd HH:mm:ss"))
$headerLines += "Rama: $branch"
$headerLines += "Commits listados: $LastNCommits"
$headerLines += ''
$headerLines += '---'
$headerLines += ''
$headerLines += '```text'

$header = $headerLines -join [Environment]::NewLine

# Formato del log de git: incluye todo el mensaje (subject + body) y un separador entre commits
# Usamos %n (newline de git) para evitar problemas de escape en PowerShell
$logFormat = 'commit %H%nAuthor: %an%nDate: %ad%n%n%s%n%b%n---%n'

# Obtiene los últimos N commits con el formato definido
# --encoding=utf-8 asegura que git convierta internamente los mensajes a UTF-8
$gitLog = git log -n $LastNCommits --date=iso --encoding=utf-8 --pretty=format:"$logFormat"

$footer = [Environment]::NewLine + '```' + [Environment]::NewLine

# Escribe el archivo markdown
$header | Set-Content -Path $OutputPath -Encoding UTF8
$gitLog  | Add-Content -Path $OutputPath -Encoding UTF8
$footer  | Add-Content -Path $OutputPath -Encoding UTF8
