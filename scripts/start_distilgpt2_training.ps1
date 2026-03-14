param()

$repoRoot = "C:\Users\ManishKL\Documents\Playground\codex-private-airgap-lab"
$stdoutLog = Join-Path $repoRoot "artifacts\distilgpt2_train.stdout.log"
$stderrLog = Join-Path $repoRoot "artifacts\distilgpt2_train.stderr.log"

if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }
if (Test-Path $stderrLog) { Remove-Item $stderrLog -Force }

$bashCommand = ". ~/codex-airgap-venv/bin/activate && cd /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab && bash wsl/run_distilgpt2_example.sh"

$process = Start-Process `
  -FilePath "wsl" `
  -ArgumentList @("-d", "Ubuntu-24.04", "--", "bash", "-lc", "`"$bashCommand`"") `
  -RedirectStandardOutput $stdoutLog `
  -RedirectStandardError $stderrLog `
  -PassThru

Write-Host "Started DistilGPT2 training."
Write-Host "PID: $($process.Id)"
Write-Host "Stdout: $stdoutLog"
Write-Host "Stderr: $stderrLog"

