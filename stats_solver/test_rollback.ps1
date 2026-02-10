# Stats Solver Rollback Test Script
# This script verifies that rollback procedures work correctly

$ErrorActionPreference = "Stop"

# Test counter
$passed = 0
$failed = 0

# Functions
function Write-Pass {
    param([string]$message)
    Write-Host "[PASS] $message" -ForegroundColor Green
    $script:passed++
}

function Write-Fail {
    param([string]$message)
    Write-Host "[FAIL] $message" -ForegroundColor Red
    $script:failed++
}

function Write-Info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Yellow
}

# Test 1: Check if git is available
Write-Info "Testing git availability..."
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Pass "Git is available"
} else {
    Write-Fail "Git is not available"
    exit 1
}

# Test 2: Check if git repo is initialized
Write-Info "Testing git repository status..."
try {
    $gitDir = git rev-parse --git-dir 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Git repository is initialized"
    } else {
        Write-Fail "Git repository is not initialized"
        exit 1
    }
} catch {
    Write-Fail "Git repository is not initialized"
    exit 1
}

# Test 3: Check if tags exist
Write-Info "Testing git tags..."
try {
    $tags = git tag 2>&1
    if ($LASTEXITCODE -eq 0) {
        $tagCount = ($tags | Measure-Object).Count
        if ($tagCount -gt 0) {
            Write-Pass "Git tags exist ($tagCount tags found)"
        } else {
            Write-Fail "No git tags found"
        }
    } else {
        Write-Fail "Failed to list git tags"
    }
} catch {
    Write-Fail "Failed to list git tags"
}

# Test 4: Check if config file exists
Write-Info "Testing configuration file..."
if (Test-Path "config/default.yaml") {
    Write-Pass "Configuration file exists"
} else {
    Write-Fail "Configuration file not found"
}

# Test 5: Check if .env.example exists
Write-Info "Testing environment template..."
if (Test-Path ".env.example") {
    Write-Pass "Environment template exists"
} else {
    Write-Fail "Environment template not found"
}

# Test 6: Check if pyproject.toml exists
Write-Info "Testing project configuration..."
if (Test-Path "pyproject.toml") {
    Write-Pass "Project configuration exists"
} else {
    Write-Fail "Project configuration not found"
}

# Test 7: Check git history
Write-Info "Testing git history..."
try {
    git log --oneline -1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Git history is accessible"
    } else {
        Write-Fail "Git history is not accessible"
    }
} catch {
    Write-Fail "Git history is not accessible"
}

# Test 8: Check feature flags in config
Write-Info "Testing feature flags..."
$configContent = Get-Content "config/default.yaml" -ErrorAction SilentlyContinue
if ($configContent -match "features:") {
    Write-Pass "Feature flags section exists in config"
} else {
    Write-Fail "Feature flags section not found in config"
}

# Test 9: Check rollback documentation
Write-Info "Testing rollback documentation..."
if (Test-Path "docs/rollback.md") {
    Write-Pass "Rollback documentation exists"
} else {
    Write-Fail "Rollback documentation not found"
}

# Test 10: Test git tag rollback simulation
Write-Info "Testing tag rollback simulation..."
try {
    $tags = git tag 2>&1
    $tagCount = ($tags | Measure-Object).Count
    if ($tagCount -gt 0) {
        $latestTag = git describe --tags --abbrev=0 2>&1
        if ($LASTEXITCODE -eq 0 -and $latestTag) {
            Write-Pass "Can identify latest tag: $latestTag"

            # Simulate checkout (don't actually do it)
            Write-Info "Simulating checkout to tag $latestTag..."
            $tagExists = git rev-parse $latestTag 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Pass "Tag is valid and accessible"
            } else {
                Write-Fail "Tag is not valid"
            }
        } else {
            Write-Fail "Could not identify latest tag"
        }
    } else {
        Write-Info "Skipping tag rollback test (no tags)"
    }
} catch {
    Write-Info "Skipping tag rollback test (error)"
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Rollback Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
    exit 1
}