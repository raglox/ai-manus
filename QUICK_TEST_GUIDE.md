# 🧪 Quick Integration Test Guide - AI-Manus Billing

**Date:** 2025-12-26  
**Status:** Ready for Testing  
**Time Required:** 15 minutes

---

## 🎯 Quick Test Checklist

### ✅ Prerequisites (2 minutes)

```bash
# 1. Install dependencies
cd /home/user/webapp/backend
pip install -r requirements.txt

# 2. Verify Stripe installed
python -c "import stripe; print(f'Stripe {stripe.VERSION} installed')"
# Expected: Stripe 14.1.0 installed

# 3. Verify billing imports
python -c "from app.domain.models.subscription import Subscription; from app.infrastructure.external.billing.stripe_service import StripeService; from app.infrastructure.middleware.billing_middleware import BillingMiddleware; print('✅ All OK')"
# Expected: ✅ All OK
```

### 🔧 Configuration (3 minutes)

```bash
# 1. Copy environment template
cd /home/user/webapp
cp .env.example .env

# 2. Edit .env and add Stripe test keys
# Get from: https://dashboard.stripe.com/test/apikeys
nano .env
```

Add these lines to `.env`:

```bash
# Stripe Configuration (TEST MODE)
STRIPE_SECRET_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_ID_BASIC=price_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO=price_xxxxxxxxxxxxxxxxxxxxx
```

### 🏗️ Stripe Dashboard Setup (5 minutes)

1. **Get API Keys**
   - Go to: https://dashboard.stripe.com/test/apikeys
   - Copy **Secret key** → `STRIPE_SECRET_KEY`

2. **Create BASIC Product**
   - Go to: https://dashboard.stripe.com/test/products
   - Click **+ Add product**
   - Name: `AI-Manus BASIC`
   - Description: `1,000 agent runs per month`
   - Pricing model: **Recurring**
   - Price: `$19.00 USD`
   - Billing period: **Monthly**
   - Click **Save product**
   - Copy **Price ID** (starts with `price_`) → `STRIPE_PRICE_ID_BASIC`

3. **Create PRO Product**
   - Click **+ Add product**
   - Name: `AI-Manus PRO`
   - Description: `5,000 agent runs per month`
   - Pricing model: **Recurring**
   - Price: `$49.00 USD`
   - Billing period: **Monthly**
   - Click **Save product**
   - Copy **Price ID** → `STRIPE_PRICE_ID_PRO`

4. **Setup Webhook (Local Testing)**
   ```bash
   # Install Stripe CLI
   brew install stripe/stripe-cli/stripe  # macOS
   # or download from https://stripe.com/docs/stripe-cli
   
   # Login
   stripe login
   
   # Forward webhooks to local server
   stripe listen --forward-to localhost:8000/api/v1/billing/webhook
   
   # Copy the webhook signing secret from output
   # Example: whsec_xxx → STRIPE_WEBHOOK_SECRET
   ```

### 🚀 Start Application (2 minutes)

```bash
# Terminal 1: Start MongoDB & Redis
cd /home/user/webapp
docker-compose up -d mongodb redis

# Terminal 2: Start Backend
cd /home/user/webapp/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Forward Stripe webhooks
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

Expected output:
```
INFO:     Application startup - Manus AI Agent initializing
INFO:     Successfully initialized Beanie
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 🧪 Test API (3 minutes)

#### Test 1: Health Check

```bash
curl http://localhost:8000/
```

Expected: `{"message":"Manus AI Agent API is running"}`

#### Test 2: Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "Test User",
    "email": "test@example.com",
    "password": "Test123456!"
  }'
```

Expected:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "refresh_token": "...",
  "user": {
    "id": "...",
    "fullname": "Test User",
    "email": "test@example.com",
    "role": "USER"
  }
}
```

**Save the `access_token` for next tests!**

#### Test 3: Check Subscription Status

```bash
export TOKEN="YOUR_ACCESS_TOKEN_FROM_TEST_2"

curl -X GET http://localhost:8000/api/v1/billing/subscription \
  -H "Authorization: Bearer $TOKEN"
```

Expected:
```json
{
  "id": "...",
  "user_id": "...",
  "plan": "FREE",
  "status": "ACTIVE",
  "monthly_agent_runs": 0,
  "monthly_agent_runs_limit": 10,
  "current_period_end": null,
  "cancel_at_period_end": false,
  "is_trial": false,
  "trial_end": null
}
```

#### Test 4: Activate Trial

```bash
curl -X POST http://localhost:8000/api/v1/billing/activate-trial \
  -H "Authorization: Bearer $TOKEN"
```

Expected:
```json
{
  "message": "Trial activated successfully",
  "trial_end": "2026-01-09T...",
  "runs_limit": 50
}
```

#### Test 5: Create Checkout Session (Upgrade to BASIC)

```bash
curl -X POST http://localhost:8000/api/v1/billing/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "BASIC",
    "success_url": "http://localhost:3000/settings/subscription?success=true",
    "cancel_url": "http://localhost:3000/settings/subscription?canceled=true"
  }'
```

Expected:
```json
{
  "checkout_session_id": "cs_test_...",
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

**Copy the `checkout_url` and open in browser!**

#### Test 6: Complete Payment in Stripe Checkout

1. Open the `checkout_url` in your browser
2. Fill in test card details:
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/34`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)
3. Click **Pay**
4. You should be redirected to success URL

#### Test 7: Verify Webhook Processed

Check your Terminal 3 (Stripe CLI) for webhook events:

```
✔ Received event checkout.session.completed
✔ Received event customer.subscription.created
```

#### Test 8: Verify Subscription Updated

```bash
curl -X GET http://localhost:8000/api/v1/billing/subscription \
  -H "Authorization: Bearer $TOKEN"
```

Expected:
```json
{
  "plan": "BASIC",
  "status": "ACTIVE",
  "monthly_agent_runs": 0,
  "monthly_agent_runs_limit": 1000,
  "current_period_end": "2026-01-26T...",
  "stripe_subscription_id": "sub_..."
}
```

**✅ If you see `monthly_agent_runs_limit: 1000`, the integration works!**

#### Test 9: Customer Portal

```bash
curl -X POST http://localhost:8000/api/v1/billing/create-portal-session \
  -H "Authorization: Bearer $TOKEN"
```

Expected:
```json
{
  "portal_url": "https://billing.stripe.com/p/session/..."
}
```

Open the `portal_url` in browser to:
- Update payment method
- View invoices
- Cancel subscription

---

## 🎯 Success Criteria

| Test | Status | Expected Result |
|------|--------|-----------------|
| **1. Health Check** | ⏳ | API responds with "running" message |
| **2. Register User** | ⏳ | Returns access_token and user object |
| **3. Check Subscription** | ⏳ | Returns FREE plan with 10 runs limit |
| **4. Activate Trial** | ⏳ | Returns trial_end date and 50 runs limit |
| **5. Create Checkout** | ⏳ | Returns Stripe checkout URL |
| **6. Complete Payment** | ⏳ | Redirects to success URL |
| **7. Webhook Processed** | ⏳ | Stripe CLI shows event received |
| **8. Subscription Updated** | ⏳ | Plan changed to BASIC, 1000 runs limit |
| **9. Customer Portal** | ⏳ | Returns portal URL for management |

**All 9 tests passed?** → ✅ **Integration Successful!**

---

## 🐛 Troubleshooting

### Problem: "Stripe API key not configured"

**Solution:**
```bash
# Check .env file
cat .env | grep STRIPE_SECRET_KEY

# If missing, add it:
echo "STRIPE_SECRET_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxx" >> .env

# Restart backend
```

### Problem: "Webhook signature verification failed"

**Solution:**
```bash
# Make sure Stripe CLI is running
stripe listen --forward-to localhost:8000/api/v1/billing/webhook

# Copy the webhook secret from CLI output
# Update .env with:
# STRIPE_WEBHOOK_SECRET=whsec_xxx

# Restart backend
```

### Problem: "Price ID not found"

**Solution:**
```bash
# Check Stripe Dashboard products
# Copy the correct Price ID (starts with price_)
# Update .env:
# STRIPE_PRICE_ID_BASIC=price_xxx
# STRIPE_PRICE_ID_PRO=price_xxx
```

### Problem: MongoDB connection error

**Solution:**
```bash
# Make sure MongoDB is running
docker-compose up -d mongodb

# Check logs
docker-compose logs mongodb
```

### Problem: Import errors

**Solution:**
```bash
# Reinstall dependencies
cd /home/user/webapp/backend
pip install -r requirements.txt --force-reinstall

# Verify
python -c "import stripe; print('OK')"
```

---

## 📊 Expected Test Results

### ✅ Successful Test Output

```bash
# Test 1: Health Check
{"message":"Manus AI Agent API is running"}

# Test 2: Register User
{"access_token":"eyJ...","token_type":"bearer","user":{...}}

# Test 3: Check Subscription
{"plan":"FREE","monthly_agent_runs_limit":10}

# Test 4: Activate Trial
{"message":"Trial activated successfully","runs_limit":50}

# Test 5: Create Checkout
{"checkout_url":"https://checkout.stripe.com/..."}

# Test 6: Payment Success
✅ Redirected to success URL

# Test 7: Webhook Events
✔ checkout.session.completed
✔ customer.subscription.created

# Test 8: Subscription Updated
{"plan":"BASIC","monthly_agent_runs_limit":1000}

# Test 9: Customer Portal
{"portal_url":"https://billing.stripe.com/..."}
```

---

## 🎉 Next Steps After Successful Test

1. **Frontend UI** - Build subscription settings page
2. **Production Setup** - Configure production Stripe keys
3. **Monitoring** - Setup Sentry/logging
4. **Documentation** - API documentation site
5. **Launch** - Beta testing with real users

---

## 📞 Need Help?

- **Documentation:** `/BILLING_INTEGRATION_COMPLETE.md`
- **Stripe Docs:** https://stripe.com/docs
- **Repository:** https://github.com/raglox/ai-manus

---

**Estimated Time:** 15 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** Docker, Python, Stripe account  
**Status:** ✅ Ready to test

Happy testing! 🚀
