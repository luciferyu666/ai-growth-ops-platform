$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $root
try {
  npm run lint --prefix apps/web
  docker compose -f infra/docker-compose.yml config --quiet
}
finally {
  Pop-Location
}
