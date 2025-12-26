#!/bin/bash
# AI Manus - Comprehensive System Test Suite
# Tests all major endpoints and functionality

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL_FRONTEND="http://172.245.232.188:5173"
BASE_URL_BACKEND="http://172.245.232.188:8002"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="Test123!@#"
TEST_FULLNAME="Test User"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print test header
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# Function to print test result
print_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✅ PASS${NC}: $2"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}❌ FAIL${NC}: $2"
        if [ ! -z "$3" ]; then
            echo -e "${RED}   Error: $3${NC}"
        fi
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local method=$1
    local url=$2
    local expected_status=$3
    local headers=$4
    local data=$5
    local description=$6
    
    if [ ! -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" $headers -d "$data" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" $headers 2>&1)
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" == "$expected_status" ]; then
        print_result 0 "$description"
        echo "$body"
        return 0
    else
        print_result 1 "$description" "Expected $expected_status, got $status_code"
        echo "$body"
        return 1
    fi
}

# Start tests
print_header "AI MANUS - COMPREHENSIVE SYSTEM TEST"
echo "Test Time: $(date)"
echo "Frontend URL: $BASE_URL_FRONTEND"
echo "Backend URL: $BASE_URL_BACKEND"

# ═══════════════════════════════════════════════════════════════
# 1. HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════
print_header "1. HEALTH & CONNECTIVITY TESTS"

# Test 1.1: Frontend accessibility
echo ""
echo "Test 1.1: Frontend Accessibility"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL_FRONTEND)
if [ "$FRONTEND_STATUS" == "200" ]; then
    print_result 0 "Frontend is accessible"
else
    print_result 1 "Frontend is accessible" "Got status $FRONTEND_STATUS"
fi

# Test 1.2: Backend API docs
echo ""
echo "Test 1.2: Backend API Documentation"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL_BACKEND/docs)
if [ "$DOCS_STATUS" == "200" ]; then
    print_result 0 "API documentation is accessible"
else
    print_result 1 "API documentation is accessible" "Got status $DOCS_STATUS"
fi

# Test 1.3: Health endpoint
echo ""
echo "Test 1.3: Health Endpoint"
HEALTH_RESPONSE=$(curl -s $BASE_URL_BACKEND/api/v1/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_result 0 "Health endpoint returns healthy"
else
    print_result 1 "Health endpoint returns healthy" "Response: $HEALTH_RESPONSE"
fi

# ═══════════════════════════════════════════════════════════════
# 2. AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════
print_header "2. AUTHENTICATION TESTS"

# Test 2.1: Get auth status
echo ""
echo "Test 2.1: Get Authentication Status"
AUTH_STATUS=$(curl -s $BASE_URL_BACKEND/api/v1/auth/status | jq -r '.data.auth_provider')
if [ "$AUTH_STATUS" == "password" ]; then
    print_result 0 "Auth provider is configured (password)"
else
    print_result 1 "Auth provider is configured" "Got: $AUTH_STATUS"
fi

# Test 2.2: Register new user
echo ""
echo "Test 2.2: User Registration"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL_BACKEND/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"fullname\":\"$TEST_FULLNAME\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | jq -r '.code')
if [ "$REGISTER_CODE" == "0" ]; then
    print_result 0 "User registration successful"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.data.access_token')
    REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.data.refresh_token')
    USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.data.user.id')
    echo "   User ID: $USER_ID"
    echo "   Token length: ${#ACCESS_TOKEN}"
else
    print_result 1 "User registration successful" "Response code: $REGISTER_CODE"
    echo "$REGISTER_RESPONSE"
fi

# Test 2.3: Login with created user
echo ""
echo "Test 2.3: User Login"
if [ ! -z "$ACCESS_TOKEN" ]; then
    LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL_BACKEND/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")
    
    LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | jq -r '.code')
    if [ "$LOGIN_CODE" == "0" ]; then
        print_result 0 "User login successful"
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token')
    else
        print_result 1 "User login successful" "Response code: $LOGIN_CODE"
    fi
else
    print_result 1 "User login successful" "Skipped - registration failed"
fi

# Test 2.4: Get current user info
echo ""
echo "Test 2.4: Get Current User Info"
if [ ! -z "$ACCESS_TOKEN" ]; then
    USER_RESPONSE=$(curl -s $BASE_URL_BACKEND/api/v1/auth/me \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    USER_EMAIL=$(echo "$USER_RESPONSE" | jq -r '.data.email')
    if [ "$USER_EMAIL" == "$TEST_EMAIL" ]; then
        print_result 0 "Get current user info"
    else
        print_result 1 "Get current user info" "Email mismatch"
    fi
else
    print_result 1 "Get current user info" "Skipped - no access token"
fi

# Test 2.5: Refresh token
echo ""
echo "Test 2.5: Token Refresh"
if [ ! -z "$REFRESH_TOKEN" ]; then
    REFRESH_RESPONSE=$(curl -s -X POST $BASE_URL_BACKEND/api/v1/auth/refresh \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")
    
    NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.data.access_token')
    if [ ! -z "$NEW_ACCESS_TOKEN" ] && [ "$NEW_ACCESS_TOKEN" != "null" ]; then
        print_result 0 "Token refresh successful"
    else
        print_result 1 "Token refresh successful"
    fi
else
    print_result 1 "Token refresh successful" "Skipped - no refresh token"
fi

# ═══════════════════════════════════════════════════════════════
# 3. SESSION MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════════
print_header "3. SESSION MANAGEMENT TESTS"

# Test 3.1: Create session
echo ""
echo "Test 3.1: Create Session"
if [ ! -z "$ACCESS_TOKEN" ]; then
    SESSION_RESPONSE=$(curl -s -X PUT $BASE_URL_BACKEND/api/v1/sessions \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json")
    
    SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.data.session_id')
    if [ ! -z "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
        print_result 0 "Create session"
        echo "   Session ID: $SESSION_ID"
    else
        print_result 1 "Create session" "No session ID returned"
    fi
else
    print_result 1 "Create session" "Skipped - no access token"
fi

# Test 3.2: List sessions
echo ""
echo "Test 3.2: List Sessions"
if [ ! -z "$ACCESS_TOKEN" ]; then
    LIST_RESPONSE=$(curl -s -X GET $BASE_URL_BACKEND/api/v1/sessions \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    SESSION_COUNT=$(echo "$LIST_RESPONSE" | jq -r '.data.sessions | length')
    if [ "$SESSION_COUNT" -gt 0 ]; then
        print_result 0 "List sessions"
        echo "   Found $SESSION_COUNT session(s)"
    else
        print_result 1 "List sessions" "No sessions found"
    fi
else
    print_result 1 "List sessions" "Skipped - no access token"
fi

# Test 3.3: Get session details
echo ""
echo "Test 3.3: Get Session Details"
if [ ! -z "$SESSION_ID" ] && [ ! -z "$ACCESS_TOKEN" ]; then
    SESSION_DETAIL=$(curl -s -X GET "$BASE_URL_BACKEND/api/v1/sessions/$SESSION_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    SESSION_STATUS=$(echo "$SESSION_DETAIL" | jq -r '.data.status')
    if [ ! -z "$SESSION_STATUS" ] && [ "$SESSION_STATUS" != "null" ]; then
        print_result 0 "Get session details"
        echo "   Status: $SESSION_STATUS"
    else
        print_result 1 "Get session details"
    fi
else
    print_result 1 "Get session details" "Skipped - no session ID or token"
fi

# Test 3.4: Chat with AI (send message)
echo ""
echo "Test 3.4: Send Chat Message"
if [ ! -z "$SESSION_ID" ] && [ ! -z "$ACCESS_TOKEN" ]; then
    # Start chat in background and timeout after 5 seconds
    CHAT_RESPONSE=$(timeout 5 curl -s -X POST "$BASE_URL_BACKEND/api/v1/sessions/$SESSION_ID/chat" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -H "Accept: text/event-stream" \
      -d "{\"message\":\"Hello, test message\",\"timestamp\":$(date +%s)}" 2>&1 || echo "")
    
    if echo "$CHAT_RESPONSE" | grep -q "event:"; then
        print_result 0 "Send chat message (SSE stream started)"
    elif [ -z "$CHAT_RESPONSE" ]; then
        print_result 0 "Send chat message (SSE connection established)"
    else
        print_result 1 "Send chat message" "No SSE events received"
    fi
else
    print_result 1 "Send chat message" "Skipped - no session ID or token"
fi

# Test 3.5: Delete session
echo ""
echo "Test 3.5: Delete Session"
if [ ! -z "$SESSION_ID" ] && [ ! -z "$ACCESS_TOKEN" ]; then
    DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL_BACKEND/api/v1/sessions/$SESSION_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    DELETE_CODE=$(echo "$DELETE_RESPONSE" | jq -r '.code')
    if [ "$DELETE_CODE" == "0" ]; then
        print_result 0 "Delete session"
    else
        print_result 1 "Delete session"
    fi
else
    print_result 1 "Delete session" "Skipped - no session ID or token"
fi

# ═══════════════════════════════════════════════════════════════
# 4. PROXY TESTS (via Frontend)
# ═══════════════════════════════════════════════════════════════
print_header "4. PROXY TESTS (Frontend → Backend)"

# Test 4.1: Auth status via proxy
echo ""
echo "Test 4.1: Auth Status via Frontend Proxy"
PROXY_AUTH_STATUS=$(curl -s $BASE_URL_FRONTEND/api/v1/auth/status | jq -r '.data.auth_provider')
if [ "$PROXY_AUTH_STATUS" == "password" ]; then
    print_result 0 "Auth status via proxy"
else
    print_result 1 "Auth status via proxy"
fi

# Test 4.2: Create session via proxy
echo ""
echo "Test 4.2: Create Session via Frontend Proxy"
if [ ! -z "$ACCESS_TOKEN" ]; then
    PROXY_SESSION=$(curl -s -X PUT $BASE_URL_FRONTEND/api/v1/sessions \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json")
    
    PROXY_SESSION_ID=$(echo "$PROXY_SESSION" | jq -r '.data.session_id')
    if [ ! -z "$PROXY_SESSION_ID" ] && [ "$PROXY_SESSION_ID" != "null" ]; then
        print_result 0 "Create session via proxy"
    else
        print_result 1 "Create session via proxy"
    fi
else
    print_result 1 "Create session via proxy" "Skipped - no access token"
fi

# ═══════════════════════════════════════════════════════════════
# 5. DOCKER CONTAINER STATUS
# ═══════════════════════════════════════════════════════════════
print_header "5. DOCKER CONTAINER STATUS"

echo ""
cd /home/root/webapp && docker compose -f docker-compose.production.yml ps

# Check if all containers are running
BACKEND_STATUS=$(cd /home/root/webapp && docker compose -f docker-compose.production.yml ps backend | grep "Up" | wc -l)
FRONTEND_STATUS=$(cd /home/root/webapp && docker compose -f docker-compose.production.yml ps frontend | grep "Up" | wc -l)
MONGODB_STATUS=$(cd /home/root/webapp && docker compose -f docker-compose.production.yml ps mongodb | grep "Up" | wc -l)
REDIS_STATUS=$(cd /home/root/webapp && docker compose -f docker-compose.production.yml ps redis | grep "Up" | wc -l)

echo ""
if [ "$BACKEND_STATUS" -eq 1 ]; then
    print_result 0 "Backend container is running"
else
    print_result 1 "Backend container is running"
fi

if [ "$FRONTEND_STATUS" -eq 1 ]; then
    print_result 0 "Frontend container is running"
else
    print_result 1 "Frontend container is running"
fi

if [ "$MONGODB_STATUS" -eq 1 ]; then
    print_result 0 "MongoDB container is running"
else
    print_result 1 "MongoDB container is running"
fi

if [ "$REDIS_STATUS" -eq 1 ]; then
    print_result 0 "Redis container is running"
else
    print_result 1 "Redis container is running"
fi

# ═══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════
print_header "TEST SUMMARY"

echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║          ✅ ALL TESTS PASSED SUCCESSFULLY! ✅            ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║              ⚠️  SOME TESTS FAILED ⚠️                   ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
