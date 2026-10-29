<#
.SYNOPSIS
    Jarvis verification loop. Runs the full offline verification suite and
    writes a timestamped TEXT report to reports\verify_<timestamp>.txt so the
    agent (or a human) can read results after every change.

.USAGE
    powershell -File tools\verify.ps1
    powershell -File tools\verify.ps1 -Quick   # skip the slow wheel-resolution

.OUTPUT
    Prints the report to stdout and saves it under reports\. Exit code is 0
    when every stage passed, 1 otherwise.
#>

param(
    [switch]$Quick
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $RepoRoot "reports"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$reportPath = Join-Path $outDir "verify_$ts.txt"

$report = New-Object System.Collections.Generic.List[string]
$report.Add("=== Jarvis Verification Report ($ts) ===")
$report.Add("RepoRoot: $RepoRoot")
$report.Add("")

$fail = $false
function Add-Stage([string]$name, [scriptblock]$body) {
    $report.Add("--- $name ---")
    Push-Location $RepoRoot
    try {
        $out = & $body 2>&1 | Out-String
        $code = $LASTEXITCODE
        $report.Add($out.TrimEnd())
        $report.Add("exit=$code")
        if ($code -ne 0) { $script:fail = $true }
    } catch {
        $report.Add("  stage error: $($_.Exception.Message)")
        $script:fail = $true
    } finally {
        Pop-Location
    }
    $report.Add("")
}

if (-not (Test-Path $Py)) {
    $report.Add("FATAL: venv python not found at $Py")
    $report | Out-File -FilePath $reportPath -Encoding utf8
    $report | ForEach-Object { Write-Output $_ }
    exit 1
}

Add-Stage "Offline bundle readiness" {
    if ($Quick) {
        # Skip pip's wheel resolution; still check files + manifest by stubbing.
        & $Py -c "import sys; sys.path.insert(0,'tools'); from check_offline_bundle import check_bundle; b=check_bundle(resolve_wheels=False); print('blockers:', len(b)); [print('-',x) for x in b]; sys.exit(1 if b else 0)"
    } else {
        & $Py tools\check_offline_bundle.py
    }
}

Add-Stage "Offline bundle and runtime unit tests" {
    & $Py -m unittest discover -s tools -p "test_*.py" -q
}

Add-Stage "Python syntax (compileall)" {
    & $Py -m compileall -q main.py scripts tools test_llama.py
}

Add-Stage "Git hygiene (status + diff --check)" {
    # 'exit' inside this scriptblock would kill the whole -File process before
    # the report prints. diff --check runs LAST so its exit code surfaces via
    # $LASTEXITCODE in Add-Stage.
    & "C:\Program Files\Git\cmd\git.exe" status --short --branch
    & "C:\Program Files\Git\cmd\git.exe" diff --check
}

if ($fail) { $report.Add("=== RESULT: FAIL ===") } else { $report.Add("=== RESULT: PASS ===") }

$report | Out-File -FilePath $reportPath -Encoding utf8
$report | ForEach-Object { Write-Output $_ }
Write-Output ""
Write-Output "Report saved to: $reportPath"
if ($fail) { exit 1 }
exit 0
