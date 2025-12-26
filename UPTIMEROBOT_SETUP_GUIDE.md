# 📡 UptimeRobot Monitoring Setup Guide

**التاريخ:** 2025-12-26  
**الحالة:** ✅ **جاهز للتفعيل**  
**المدة:** 1 ساعة  
**التكلفة:** $0/month (Free tier: 50 monitors)

---

## 📋 الخلاصة

**UptimeRobot** يوفر monitoring مجاني على مدار الساعة للتطبيق:
- 🔔 **Uptime Monitoring** - مراقبة 24/7 على فترات 5 دقائق
- 📊 **Status Page** - صفحة حالة عامة للمستخدمين
- 📧 **Alerts** - تنبيهات فورية عبر Email/SMS/Slack
- 📈 **Uptime Reports** - تقارير uptime percentage
- 🌍 **Multi-location checks** - فحص من مواقع متعددة

---

## 🚀 Quick Start (10 دقائق)

### Step 1: إنشاء حساب UptimeRobot (مجاني)

1. اذهب إلى: https://uptimerobot.com/signUp
2. سجّل باستخدام Email أو Google
3. فعّل حسابك من Email

---

### Step 2: إضافة Monitors

بعد تسجيل الدخول، أنشئ 3 monitors:

#### Monitor #1: Backend Health Check
```
Type: HTTP(s)
Friendly Name: AI-Manus Backend Health
URL: https://your-domain.com/api/v1/health
Monitoring Interval: 5 minutes (free tier)
Monitor Timeout: 30 seconds
Alert Contacts: your-email@example.com
```

**Expected Response:**
- Status Code: `200 OK`
- Response Time: < 500ms
- Body Contains: `"status": "healthy"`

#### Monitor #2: Backend Readiness Check
```
Type: HTTP(s)
Friendly Name: AI-Manus Backend Ready
URL: https://your-domain.com/api/v1/ready
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
Alert Contacts: your-email@example.com
```

**Expected Response:**
- Status Code: `200 OK`
- Body Contains: `"status": "ready"`
- **Note:** If dependencies (MongoDB, Redis) are down, this returns `503`

#### Monitor #3: Frontend Homepage
```
Type: HTTP(s)
Friendly Name: AI-Manus Frontend
URL: https://your-domain.com/
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
Alert Contacts: your-email@example.com
```

**Expected Response:**
- Status Code: `200 OK`
- Response Time: < 2000ms

---

### Step 3: Configure Alert Contacts

#### Email Notifications (Default)
```
Contact Type: E-mail
E-mail: your-email@example.com
Friendly Name: Primary Email

Alerts to send:
✅ Monitor is down
✅ Monitor is up (after downtime)
✅ Monitor is paused
✅ Monitor is started
```

#### SMS Notifications (Optional - Paid)
```
Contact Type: SMS
Phone: +1-XXX-XXX-XXXX
Friendly Name: Emergency Phone

Alerts to send:
✅ Monitor is down (only critical)
```

#### Slack Integration (Recommended)
```
Contact Type: Slack
Slack Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Friendly Name: DevOps Slack Channel

Alerts to send:
✅ Monitor is down
✅ Monitor is up
```

**How to get Slack Webhook URL:**
1. Go to: https://api.slack.com/messaging/webhooks
2. Create new Incoming Webhook
3. Select channel (e.g., `#alerts` or `#devops`)
4. Copy webhook URL
5. Paste in UptimeRobot

---

### Step 4: Create Public Status Page

1. Go to: **My Settings** → **Status Pages**
2. Click **Add New Status Page**
3. Configure:

```
Status Page URL: manus-status (becomes: status.uptimerobot.com/manus-status)
Custom Domain: status.yourdomain.com (optional, requires DNS setup)
Page Title: AI-Manus System Status
Page Description: Real-time status and uptime monitoring for AI-Manus SaaS

Monitors to Display:
✅ AI-Manus Backend Health
✅ AI-Manus Backend Ready
✅ AI-Manus Frontend

Display Options:
✅ Show uptime percentage
✅ Show response time graph
✅ Show incident history (last 30 days)
⬜ Show monitor details (optional)

Password Protection: Off (public)
Timezone: UTC
```

4. Click **Create Status Page**
5. Your status page will be live at:
   ```
   https://status.uptimerobot.com/YOUR_PAGE_ID
   ```

**Public Status Page Example:**
```
AI-Manus System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All Systems Operational ✅

Services:
🟢 Backend Health       99.98% uptime (30 days)
🟢 Backend Ready        99.95% uptime (30 days)
🟢 Frontend             99.99% uptime (30 days)

Recent Incidents:
No incidents in the last 30 days
```

---

## 📊 Monitor Configuration Details

### Free Tier Limits
- ✅ **50 monitors** (more than enough for our use case)
- ✅ **5-minute intervals** (checks every 5 minutes)
- ✅ **Unlimited email alerts**
- ✅ **1 public status page**
- ✅ **2-month logs**

### Paid Tier Benefits ($7/month - Pro)
- ⚡ **1-minute intervals** (checks every minute)
- 📱 **SMS alerts** (up to 50 SMS/month)
- 📞 **Voice call alerts**
- 📊 **Advanced analytics**
- 🔗 **Custom domain for status page**
- 📈 **90-day logs**

**Recommendation:** 🟢 **Start with Free Tier** - upgrade to Pro only if you need 1-min checks or SMS alerts

---

## 🔔 Alert Configuration Best Practices

### Alert Frequency
```
Down alerts:
- Send immediately when down
- Re-alert every 30 minutes if still down

Up alerts:
- Send immediately when service recovers
- No re-alerts needed
```

### Alert Channels Priority
```
Critical (Backend down):
- 📧 Email to all team members
- 💬 Slack to #alerts channel
- 📱 SMS to on-call engineer (if Pro plan)

Warning (Frontend slow):
- 📧 Email to DevOps
- 💬 Slack to #devops channel

Maintenance:
- 📧 Email only (no urgent alerts)
```

### Sample Alert Email
```
Subject: 🔴 ALERT: AI-Manus Backend Health is DOWN

Monitor: AI-Manus Backend Health
URL: https://your-domain.com/api/v1/health
Status: DOWN
Reason: HTTP 503 Service Unavailable
Last Check: 2024-12-26 14:32:15 UTC
Down Since: 2024-12-26 14:27:03 UTC
Duration: 5 minutes 12 seconds

Action Required:
1. Check server status
2. Review logs: kubectl logs -f deployment/backend
3. Check dependencies: MongoDB, Redis
4. Check Sentry for errors

View Details: https://uptimerobot.com/dashboard#MONITOR_ID
```

---

## 📈 Dashboard & Reports

### Real-Time Dashboard
```
UptimeRobot Dashboard shows:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monitor                Status    Uptime (30d)  Response Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend Health         🟢 UP     99.98%        245ms
Backend Ready          🟢 UP     99.95%        312ms
Frontend               🟢 UP     99.99%        1.2s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recent Alerts:
- Backend Ready: DOWN → UP (2 min downtime, 2024-12-20 03:15 UTC)
- Frontend: Slow response (3.5s, 2024-12-18 12:42 UTC)
```

### Uptime Reports
```
Monthly Uptime Report (December 2024):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Service                Uptime    Downtime    Incidents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend Health         99.98%    5 min       1
Backend Ready          99.95%    12 min      2
Frontend               99.99%    2 min       1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Uptime: 99.97% ✅
SLA Target: 99.9%
Status: MEETING SLA ✅
```

---

## 🧪 Testing Monitors

### Test #1: Verify Health Check Monitor

```bash
# 1. Stop backend temporarily
docker-compose stop backend

# 2. Wait 5-10 minutes for UptimeRobot to detect
# 3. You should receive alert email

# 4. Restart backend
docker-compose start backend

# 5. Wait 5-10 minutes
# 6. You should receive "service is UP" email
```

### Test #2: Verify Alert Notifications

```bash
# In UptimeRobot dashboard:
1. Select a monitor
2. Click "Pause"
3. Wait 5 minutes
4. Check email for "Monitor is paused" alert
5. Click "Resume"
6. Check email for "Monitor is started" alert
```

### Test #3: Status Page

```bash
# Visit your status page
open https://status.uptimerobot.com/YOUR_PAGE_ID

# Verify:
✅ All monitors shown
✅ Uptime percentages displayed
✅ Response time graphs visible
✅ Incident history shown (if any)
```

---

## 🔗 Integration with Other Tools

### Slack Webhook Setup

**Step 1:** Create Incoming Webhook
```bash
1. Go to: https://api.slack.com/messaging/webhooks
2. Click "Create New App" → "From scratch"
3. App Name: "UptimeRobot Alerts"
4. Workspace: Your workspace
5. Click "Incoming Webhooks" → Activate
6. Click "Add New Webhook to Workspace"
7. Choose channel: #alerts
8. Copy webhook URL
```

**Step 2:** Add to UptimeRobot
```bash
1. UptimeRobot → My Settings → Alert Contacts
2. Add Alert Contact → Slack
3. Webhook URL: paste from Step 1
4. Friendly Name: "Slack DevOps Channel"
5. Save
```

**Step 3:** Test
```bash
# In UptimeRobot:
1. Edit any monitor
2. Alert Contacts → Select your Slack contact
3. Pause monitor
4. Check Slack channel for alert
```

### PagerDuty Integration (Optional)

For 24/7 on-call rotation:
```bash
1. UptimeRobot → My Settings → Alert Contacts
2. Add Alert Contact → Webhook
3. Webhook URL: Your PagerDuty integration URL
4. Method: POST
5. Post Value: (PagerDuty requires specific format)
```

---

## 📊 Monitoring Best Practices

### 1. Monitor Hierarchy
```
Primary (Critical):
- /api/v1/health - Basic health check
- /api/v1/ready - Dependencies check

Secondary (Important):
- Frontend homepage
- /api/v1/version - Version info

Optional (Nice-to-have):
- Specific critical endpoints (e.g., /billing/subscription)
```

### 2. Response Time Thresholds
```
Excellent: < 200ms
Good: 200-500ms
Acceptable: 500-1000ms
Slow: 1000-2000ms
Critical: > 2000ms
```

**Configure alerts:**
```
Backend /health:
- Alert if > 1000ms for 5 consecutive checks
- Critical if > 2000ms

Frontend:
- Alert if > 3000ms
```

### 3. Downtime Response Procedure
```
WHEN: UptimeRobot alert received "Monitor is DOWN"

1. Immediate (0-5 min):
   - Acknowledge alert
   - Check status page
   - Check Sentry for errors
   - Check server logs

2. Investigation (5-15 min):
   - Check MongoDB/Redis status
   - Check system resources (CPU, Memory)
   - Check recent deployments
   - Check external dependencies

3. Resolution (15-30 min):
   - Apply fix
   - Restart services if needed
   - Verify via /health, /ready
   - Monitor UptimeRobot for "Monitor is UP"

4. Post-Incident (30+ min):
   - Document incident
   - Update status page with resolution
   - Post-mortem (if significant downtime)
   - Implement preventive measures
```

---

## 📞 Webhook API (Advanced)

### Get Monitor Status via API

```bash
# Get your API key from UptimeRobot settings
API_KEY="YOUR_API_KEY"

# List all monitors
curl -X POST "https://api.uptimerobot.com/v2/getMonitors" \
  -d "api_key=$API_KEY" \
  -d "format=json"

# Get specific monitor status
curl -X POST "https://api.uptimerobot.com/v2/getMonitors" \
  -d "api_key=$API_KEY" \
  -d "monitors=MONITOR_ID" \
  -d "format=json"
```

### Custom Integration Example

```python
# backend/scripts/check_uptime.py
import requests
import os

API_KEY = os.getenv("UPTIMEROBOT_API_KEY")

def get_monitor_status(monitor_id):
    response = requests.post(
        "https://api.uptimerobot.com/v2/getMonitors",
        data={
            "api_key": API_KEY,
            "monitors": monitor_id,
            "format": "json"
        }
    )
    data = response.json()
    monitor = data["monitors"][0]
    
    return {
        "name": monitor["friendly_name"],
        "status": monitor["status"],  # 2 = UP, 9 = DOWN
        "uptime": monitor["custom_uptime_ratio"],
        "response_time": monitor["average_response_time"]
    }

# Usage
status = get_monitor_status("123456789")
print(f"{status['name']}: {status['uptime']}% uptime")
```

---

## 💰 Cost Analysis

### Free Tier (Recommended for MVP)
```
Cost: $0/month
Monitors: 50 (we use 3)
Interval: 5 minutes
Alerts: Unlimited email
Status Page: 1 public page
Logs: 2 months

Perfect for:
✅ MVP phase
✅ Beta testing (< 1,000 users)
✅ Budget-conscious startups
```

### Pro Plan ($7/month)
```
Cost: $7/month
Monitors: 50
Interval: 1 minute (5x more frequent)
Alerts: Email + SMS (50 SMS/month)
Status Page: 10 pages + custom domain
Logs: 90 days

Upgrade when:
- Need 1-minute checks (faster detection)
- Need SMS alerts for on-call
- > 1,000 active users
- SLA requirements demand faster detection
```

---

## ✅ Production Deployment Checklist

- [ ] UptimeRobot account created ✅
- [ ] Backend /health monitor configured ⏳
- [ ] Backend /ready monitor configured ⏳
- [ ] Frontend monitor configured ⏳
- [ ] Email alert contact added ⏳
- [ ] Slack webhook configured (optional) ⏳
- [ ] Public status page created ⏳
- [ ] Custom domain for status page (optional) ⏳
- [ ] Alert tests performed ⏳
- [ ] Response procedures documented ⏳
- [ ] Team members trained on alert handling ⏳

---

## 🚀 الخطوات التالية

1. ✅ **Create UptimeRobot account** (2 دقائق)
2. ⏳ **Add 3 monitors** (/health, /ready, frontend) (10 دقائق)
3. ⏳ **Configure email alerts** (2 دقائق)
4. ⏳ **Setup Slack webhook** (5 دقائق - optional)
5. ⏳ **Create status page** (5 دقائق)
6. ⏳ **Test monitors** (pause/resume test) (5 دقائق)
7. ⏳ **Share status page with team** (1 دقيقة)

**Total Time:** ~30 دقائق للتجهيز الكامل

---

## 📚 Resources

### Official Documentation
- UptimeRobot Docs: https://uptimerobot.com/help/
- API Documentation: https://uptimerobot.com/api/
- Status Page Docs: https://uptimerobot.com/help/status-pages/

### Community
- UptimeRobot Blog: https://blog.uptimerobot.com/
- Twitter: @uptimerobot

---

**Status:** ✅ **READY TO ACTIVATE**  
**Time to Production:** 30 دقائق  
**Cost:** $0/month (Free tier)  
**Impact:** Uptime Monitoring 0/10 → 9/10 🎉

---

**Prepared by:** AI-Manus Implementation Team  
**Date:** 2025-12-26  
**Version:** 1.0
