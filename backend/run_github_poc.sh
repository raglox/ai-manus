#!/bin/bash

# GitHub MCP POC Runner
# This script runs the proof-of-concept test for GitHub MCP integration

set -e

echo "=========================================================================="
echo "  GitHub MCP Proof of Concept - The Devin Scenario"
echo "=========================================================================="
echo ""

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN environment variable not set"
    echo ""
    echo "Please set your GitHub Personal Access Token:"
    echo "  export GITHUB_TOKEN='ghp_xxxxxxxxxxxxxxxxxxxx'"
    echo ""
    echo "Token requirements:"
    echo "  - Scopes: repo, read:org"
    echo "  - Generate at: https://github.com/settings/tokens"
    echo ""
    exit 1
fi

echo "✅ GITHUB_TOKEN is set"
echo ""

# Check test repository settings
TEST_REPO_OWNER=${TEST_REPO_OWNER:-"raglox"}
TEST_REPO_NAME=${TEST_REPO_NAME:-"ai-manus"}

echo "Test Configuration:"
echo "  Repository: ${TEST_REPO_OWNER}/${TEST_REPO_NAME}"
echo "  Token: ${GITHUB_TOKEN:0:8}..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"
echo ""

echo "=========================================================================="
echo "  Running POC Tests"
echo "=========================================================================="
echo ""

# Run the POC test
python3 -m pytest tests/integration/test_github_poc.py \
    -v \
    --tb=short \
    --capture=no \
    -k "test_full_devin_scenario"

EXIT_CODE=$?

echo ""
echo "=========================================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✅ POC TEST: SUCCESS"
    echo ""
    echo "  The agent successfully performed autonomous GitHub operations via MCP!"
    echo "  Check your repository for the created issue as proof."
else
    echo "  ❌ POC TEST: FAILED"
    echo ""
    echo "  Exit code: $EXIT_CODE"
fi
echo "=========================================================================="
echo ""

exit $EXIT_CODE
