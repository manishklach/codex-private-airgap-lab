param(
  [string]$Name = "codex-airgap-demo",
  [string]$Modelfile = ".\ollama\Modelfile"
)

Write-Host "Creating Ollama model: $Name"
ollama create $Name -f $Modelfile

