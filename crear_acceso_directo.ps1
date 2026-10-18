$ErrorActionPreference = "Stop"+$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $project ".venv\Scripts\pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw)) {
    throw "Primero ejecuta run.bat para crear el entorno e instalar las dependencias."
}
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "JARVIS.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = ('"' + (Join-Path $project "main.py") + '"')
$shortcut.WorkingDirectory = $project
$shortcut.Description = "Asistente personal JARVIS"
$shortcut.Save()
Write-Output "Acceso directo creado: $shortcutPath"
