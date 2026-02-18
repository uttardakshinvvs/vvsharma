
$ErrorActionPreference = 'Stop'
$Origin = 'https://vvsharma.com'
$Tmp = '_mirror_tmp'
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

# Use wget if present, else try curl. (Windows has 'curl')
if (Get-Command wget.exe -ErrorAction SilentlyContinue) {
  & wget --mirror --convert-links --page-requisites --adjust-extension `
        --no-parent --no-host-directories -e robots=off `
        --directory-prefix $Tmp `
        "$Origin/"

  foreach ($p in 'index.html','biography.html','gallery.html','video.html','contact.php') {
    try { & wget -x -nH -P $Tmp -e robots=off "$Origin/$p" } catch {}
  }
} else {
  Write-Host "Please install GNU Wget for Windows, or use Git Bash."
}

if (Test-Path "$Tmp/contact.php") { Move-Item "$Tmp/contact.php" "$Tmp/contact.html" -Force }
# Copy to repo root
robocopy $Tmp . /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null

# Postprocess
python scripts/postprocess.py
Write-Host "Mirror complete. Review, then commit & push."
