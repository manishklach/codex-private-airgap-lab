param()

$repoRoot = "C:\Users\ManishKL\Documents\Playground\codex-private-airgap-lab"
$stdoutLog = Join-Path $repoRoot "artifacts\tinyllama_train.stdout.log"
$stderrLog = Join-Path $repoRoot "artifacts\tinyllama_train.stderr.log"
$artifactDir = Join-Path $repoRoot "artifacts\tinyllama-copilot-sre-lora"

Write-Host "==> WSL process"
wsl -d Ubuntu-24.04 -- bash -lc "ps -ef | grep tinyllama-base | grep train_lora.py | grep -v grep || true"

Write-Host ""
Write-Host "==> Artifact dir"
Get-ChildItem $artifactDir -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==> Stdout tail"
if (Test-Path $stdoutLog) {
  Get-Content $stdoutLog -Tail 40
} else {
  Write-Host "(no stdout log yet)"
}

Write-Host ""
Write-Host "==> Stderr tail"
if (Test-Path $stderrLog) {
  Get-Content $stderrLog -Tail 40
} else {
  Write-Host "(no stderr log yet)"
}

