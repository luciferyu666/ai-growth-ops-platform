$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $root
try {
  docker compose -f infra/docker-compose.yml up --build
}
finally {
  Pop-Location
}
