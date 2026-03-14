param(
  [Parameter(Mandatory = $true)]
  [string]$Model,

  [Parameter(Mandatory = $true)]
  [string]$Workspace,

  [string[]]$AddDir = @()
)

$argsList = @(
  "--oss",
  "--local-provider", "ollama",
  "-m", $Model,
  "-C", $Workspace,
  "--sandbox", "workspace-write",
  "--ask-for-approval", "on-request"
)

foreach ($dir in $AddDir) {
  $argsList += "--add-dir"
  $argsList += $dir
}

Write-Host "Launching Codex with Ollama model: $Model"
& codex @argsList

