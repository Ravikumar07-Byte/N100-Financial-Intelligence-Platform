$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "              DAY 41 VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ============================================================
# 1. REQUIRED FILES
# ============================================================

Write-Host ""
Write-Host "[1/5] Checking required Day 41 test files..." -ForegroundColor Yellow

$requiredFiles = @(
    "tests\etl\test_normalise.py",
    "tests\etl\test_loader.py",
    "tests\kpi\test_ratios.py",
    "tests\dq\test_rules.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "PASS  $file" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL  Missing: $file" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# 2. VERIFY ACTUAL PYTEST COLLECTION COUNTS
# ============================================================

Write-Host ""
Write-Host "[2/5] Checking actual pytest test counts..." -ForegroundColor Yellow

$expectedCounts = [ordered]@{
    "tests\etl\test_normalise.py" = 20
    "tests\etl\test_loader.py"    = 10
    "tests\kpi\test_ratios.py"    = 20
    "tests\dq\test_rules.py"      = 14
}

$totalExpected = 0
$totalCollected = 0

foreach ($file in $expectedCounts.Keys) {

    $expected = $expectedCounts[$file]
    $totalExpected += $expected

    Write-Host ""
    Write-Host "Checking $file ..." -ForegroundColor DarkCyan

    $output = @(pytest $file --collect-only -q 2>&1)

    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL  pytest collection failed for $file" -ForegroundColor Red
        $output | ForEach-Object { Write-Host $_ }
        exit 1
    }

    $summary = $output |
        Where-Object {
            $_ -match "collected\s+\d+\s+items" -or
            $_ -match "\d+\s+tests?\s+collected"
        } |
        Select-Object -Last 1

    if ($summary -match "collected\s+(\d+)\s+items") {
        $count = [int]$Matches[1]
    }
    elseif ($summary -match "(\d+)\s+tests?\s+collected") {
        $count = [int]$Matches[1]
    }
    else {
        Write-Host "FAIL  Could not determine pytest collection count for $file" -ForegroundColor Red
        $output | ForEach-Object { Write-Host $_ }
        exit 1
    }

    $totalCollected += $count

    if ($count -eq $expected) {
        Write-Host "PASS  $file -> $count collected / $expected expected" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL  $file -> $count collected / $expected expected" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "PASS  Day 41 required tests = $totalCollected / $totalExpected" -ForegroundColor Green

# ============================================================
# 3. REQUIRED KPI COVERAGE
# ============================================================

Write-Host ""
Write-Host "[3/5] Checking required KPI coverage..." -ForegroundColor Yellow

$kpiFile = "tests\kpi\test_ratios.py"

$kpiContent = Get-Content $kpiFile -Raw

$kpiRequirements = [ordered]@{

    "ROE with positive equity" =
        "roe_with_positive_equity"

    "ROE with negative equity returns None" =
        "roe_with_negative_equity"

    "D/E debt-free returns 0" =
        "debt_to_equity_debt_free"

    "ICR interest=0 returns None" =
        "interest_coverage_interest_zero"

    "D/E > 5 non-financial flag" =
        "debt_to_equity_above_five"

    "CAGR turnaround flag" =
        "(?i)cagr.*turnaround|turnaround.*cagr"

    "CAGR decline-to-loss" =
        "(?i)cagr.*decline.*loss|decline.*loss.*cagr"

    "Normal CAGR calculation" =
        "(?i)cagr.*normal|normal.*cagr|cagr.*calculation|calculate.*cagr"

    "OPM cross-check divergence" =
        "opm_crosscheck_divergence"

    "CFO quality score" =
        "(?i)cfo.*quality.*score|cfo_quality_score"
}

foreach ($requirement in $kpiRequirements.Keys) {

    $pattern = $kpiRequirements[$requirement]

    if ($kpiContent -match $pattern) {
        Write-Host "PASS  $requirement" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL  Missing KPI coverage: $requirement" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# 4. RUN COMPLETE DAY 41 TEST SUITE
# ============================================================

Write-Host ""
Write-Host "[4/5] Running complete Day 41 test suite..." -ForegroundColor Yellow
Write-Host ""

pytest tests\etl\ tests\kpi\ tests\dq\ -v

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAIL  Day 41 test suite contains failures." -ForegroundColor Red
    exit 1
}

# ============================================================
# 5. FINAL STATUS
# ============================================================

Write-Host ""
Write-Host "[5/5] Final Day 41 status..." -ForegroundColor Yellow

Write-Host "PASS  Required files exist." -ForegroundColor Green
Write-Host "PASS  test_normalise.py = 20 collected tests." -ForegroundColor Green
Write-Host "PASS  test_loader.py    = 10 collected tests." -ForegroundColor Green
Write-Host "PASS  test_ratios.py    = 20 collected tests." -ForegroundColor Green
Write-Host "PASS  test_rules.py     = 14 collected tests." -ForegroundColor Green
Write-Host "PASS  Required KPI coverage verified." -ForegroundColor Green
Write-Host "PASS  Full ETL + KPI + DQ suite passed." -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "              DAY 41 VERIFICATION PASSED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
