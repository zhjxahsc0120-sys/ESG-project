param(
  [switch]$SkipBuild,
  [switch]$Full
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$python = "C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

$env:PYTHONIOENCODING = "utf-8"

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Command
  )

  Write-Host ""
  Write-Host "==> $Name" -ForegroundColor Cyan
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed with exit code $LASTEXITCODE"
  }
}

$tests = @(
  "server\dashboard_acceptance_test.py",
  "server\dashboard_panels_mysql_test.py",
  "server\carbon_topic_mysql_test.py",
  "server\monthly_topic_mysql_test.py",
  "server\gis_business_summary_test.py"
)

if ($Full) {
  $tests = @(
    "server\dashboard_acceptance_test.py",
    "server\environment_safety_kpi_mysql_test.py",
    "server\e03_e04_kpi_mysql_test.py",
    "server\social_kpi_mysql_test.py",
    "server\governance_kpi_mysql_test.py",
    "server\dashboard_panels_mysql_test.py",
    "server\carbon_topic_mysql_test.py",
    "server\monthly_topic_mysql_test.py",
    "server\gis_business_summary_test.py",
    "server\workspace_acceptance_test.py",
    "server\multipart_upload_test.py",
    "server\ingestion_api_test.py",
    "server\ingestion_dashboard_refresh_test.py",
    "server\carbon_ingestion_dashboard_refresh_test.py",
    "server\ingestion_multi_kpi_refresh_test.py",
    "server\ingestion_more_kpi_refresh_test.py",
    "server\ingestion_social_kpi_refresh_test.py",
    "server\s01_safety_production_business_test.py",
    "server\parse_rule_dedup_test.py",
    "server\confirm_ingestion_trace_test.py",
    "server\confirm_updates_task_test.py"
  )
}

try {
  if ($Full) {
    Invoke-Step "server\reset_acceptance_baseline.py (before)" { & $python "server\reset_acceptance_baseline.py" }
  }

  foreach ($test in $tests) {
    Invoke-Step $test { & $python $test }
  }

  Invoke-Step "npm.cmd run check" { npm.cmd run check }

  if (-not $SkipBuild) {
    Invoke-Step "npm.cmd run build" { npm.cmd run build }
  }

  Write-Host ""
  Write-Host "[PASS] Local acceptance completed." -ForegroundColor Green
}
finally {
  if ($Full) {
    Write-Host ""
    Write-Host "==> server\reset_acceptance_baseline.py (after)" -ForegroundColor Cyan
    & $python "server\reset_acceptance_baseline.py"
    if ($LASTEXITCODE -ne 0) {
      Write-Host "[WARN] acceptance baseline reset failed after tests." -ForegroundColor Yellow
    }
  }
}
