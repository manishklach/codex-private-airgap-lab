param()

$checks = @(
  @{ Name = "codex"; Command = "codex --version" },
  @{ Name = "ollama"; Command = "ollama --version" },
  @{ Name = "wsl"; Command = "wsl -l -v" },
  @{ Name = "python"; Command = "python --version" },
  @{ Name = "gh"; Command = "gh --version" }
)

foreach ($check in $checks) {
  Write-Host "==> $($check.Name)"
  try {
    Invoke-Expression $check.Command
  } catch {
    Write-Warning "Failed: $($check.Command)"
  }
  Write-Host ""
}

