#!/bin/bash

# Stats Solver Rollback Test Script
# This script verifies that rollback procedures work correctly

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Functions
print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Test 1: Check if git is available
print_info "Testing git availability..."
if command -v git &> /dev/null; then
    print_pass "Git is available"
else
    print_fail "Git is not available"
    exit 1
fi

# Test 2: Check if git repo is initialized
print_info "Testing git repository status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    print_pass "Git repository is initialized"
else
    print_fail "Git repository is not initialized"
    exit 1
fi

# Test 3: Check if tags exist
print_info "Testing git tags..."
if git tag > /dev/null 2>&1; then
    TAG_COUNT=$(git tag | wc -l)
    if [ "$TAG_COUNT" -gt 0 ]; then
        print_pass "Git tags exist ($TAG_COUNT tags found)"
    else
        print_fail "No git tags found"
    fi
else
    print_fail "Failed to list git tags"
fi

# Test 4: Check if config file exists
print_info "Testing configuration file..."
if [ -f "config/default.yaml" ]; then
    print_pass "Configuration file exists"
else
    print_fail "Configuration file not found"
fi

# Test 5: Check if .env.example exists
print_info "Testing environment template..."
if [ -f ".env.example" ]; then
    print_pass "Environment template exists"
else
    print_fail "Environment template not found"
fi

# Test 6: Check if pyproject.toml exists
print_info "Testing project configuration..."
if [ -f "pyproject.toml" ]; then
    print_pass "Project configuration exists"
else
    print_fail "Project configuration not found"
fi

# Test 7: Check git history
print_info "Testing git history..."
if git log --oneline -1 > /dev/null 2>&1; then
    print_pass "Git history is accessible"
else
    print_fail "Git history is not accessible"
fi

# Test 8: Check feature flags in config
print_info "Testing feature flags..."
if grep -q "features:" config/default.yaml 2>/dev/null; then
    print_pass "Feature flags section exists in config"
else
    print_fail "Feature flags section not found in config"
fi

# Test 9: Check rollback documentation
print_info "Testing rollback documentation..."
if [ -f "docs/rollback.md" ]; then
    print_pass "Rollback documentation exists"
else
    print_fail "Rollback documentation not found"
fi

# Test 10: Test git tag rollback simulation
print_info "Testing tag rollback simulation..."
if [ "$TAG_COUNT" -gt 0 ]; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LATEST_TAG" ]; then
        print_pass "Can identify latest tag: $LATEST_TAG"

        # Simulate checkout (don't actually do it)
        print_info "Simulating checkout to tag $LATEST_TAG..."
        if git rev-parse "$LATEST_TAG" > /dev/null 2>&1; then
            print_pass "Tag is valid and accessible"
        else
            print_fail "Tag is not valid"
        fi
    else
        print_fail "Could not identify latest tag"
    fi
else
    print_info "Skipping tag rollback test (no tags)"
fi

# Summary
echo ""
echo "=========================================="
echo "Rollback Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi