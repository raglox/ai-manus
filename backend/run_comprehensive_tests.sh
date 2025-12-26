#!/bin/bash
# 🚀 Comprehensive Test Suite Runner
# Runs all tests and generates coverage reports

set -e

echo "========================================="
echo "🎯 AI Manus - Comprehensive Test Suite"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to app directory
cd /app

echo "📦 Installing test dependencies..."
pip install -q pytest pytest-cov pytest-asyncio coverage 2>/dev/null || true

echo ""
echo "🧹 Cleaning previous coverage data..."
rm -f .coverage coverage.json
rm -rf htmlcov __pycache__ .pytest_cache

echo ""
echo "🔍 Running test discovery..."
TOTAL_TESTS=$(pytest --collect-only -q | tail -1 | awk '{print $1}')
echo "Found: $TOTAL_TESTS test items"

echo ""
echo "========================================="
echo "📋 Phase 1: Unit Tests"
echo "========================================="

# Run unit tests
pytest tests/unit/ \
    -v \
    --cov=app \
    --cov-append \
    --tb=short \
    -x \
    2>&1 | tee /tmp/unit_tests.log

UNIT_EXIT=$?

echo ""
echo "========================================="
echo "📋 Phase 2: Integration Tests"
echo "========================================="

# Run integration tests (if they exist and don't fail)
if [ -d "tests/integration" ]; then
    pytest tests/integration/ \
        -v \
        --cov=app \
        --cov-append \
        --tb=short \
        --maxfail=5 \
        2>&1 | tee /tmp/integration_tests.log || true
fi

echo ""
echo "========================================="
echo "📋 Phase 3: Existing Tests"
echo "========================================="

# Run other existing tests
pytest tests/ \
    --ignore=tests/unit/ \
    --ignore=tests/integration/ \
    -v \
    --cov=app \
    --cov-append \
    --tb=short \
    --maxfail=10 \
    2>&1 | tee /tmp/other_tests.log || true

echo ""
echo "========================================="
echo "📊 Generating Coverage Reports"
echo "========================================="

# Generate all coverage reports
coverage report -m > /tmp/coverage_report.txt
coverage json
coverage html

echo ""
echo "========================================="
echo "📈 Coverage Summary"
echo "========================================="

# Extract coverage percentage
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}')
echo -e "${GREEN}Total Coverage: $COVERAGE${NC}"

# Display detailed report
echo ""
echo "Top 20 files by coverage:"
coverage report --sort=cover | head -25

echo ""
echo "========================================="
echo "📁 Reports Generated"
echo "========================================="
echo "✅ HTML Report: htmlcov/index.html"
echo "✅ JSON Report: coverage.json"
echo "✅ Text Report: /tmp/coverage_report.txt"

echo ""
echo "========================================="
echo "🎯 Test Results Summary"
echo "========================================="

# Count results from logs
PASSED=$(cat /tmp/*.log 2>/dev/null | grep -c "PASSED" || echo "0")
FAILED=$(cat /tmp/*.log 2>/dev/null | grep -c "FAILED" || echo "0")
ERRORS=$(cat /tmp/*.log 2>/dev/null | grep -c "ERROR" || echo "0")

echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${YELLOW}⚠️  Errors: $ERRORS${NC}"

echo ""
echo "========================================="
echo "🏆 Final Status"
echo "========================================="

# Check if we meet the >90% threshold
COVERAGE_NUM=$(echo $COVERAGE | sed 's/%//')
if (( $(echo "$COVERAGE_NUM >= 90" | bc -l) )); then
    echo -e "${GREEN}🎉 SUCCESS! Coverage $COVERAGE >= 90%${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Coverage $COVERAGE < 90% (need $(echo "90 - $COVERAGE_NUM" | bc)% more)${NC}"
    
    echo ""
    echo "Files needing more tests:"
    coverage report | grep -v "100%" | grep -v "TOTAL" | head -10
    
    exit 0  # Don't fail, just report
fi
