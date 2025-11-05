# 🚀 MONETIZATION DEPLOYMENT GUIDE
# Deploy Employer Pricing & Stripe Integration to Production

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Step 1: Stripe Account Setup (15 minutes)

1. **Create Stripe Account:** https://dashboard.stripe.com/register
2. **Get API Keys:**
   - Go to: Developers → API keys
   - Copy **Publishable key** (starts with `pk_`)
   - Copy **Secret key** (starts with `sk_`)
   - Copy **Webhook secret** (we'll create this in Step 3)

3. **Create Products & Prices in Stripe:**

Go to Products → Add Product:

**Product 1: Professional Plan**
- Name: `Professional Plan`
- Description: `5 jobs, featured placement, unlimited views, AI matching`
- Pricing:
  - Monthly: `$299.00/month` → Copy Price ID (e.g., `price_1234_monthly`)
  - Annual: `$2,988.00/year` → Copy Price ID

**Product 2: Enterprise Plan**
- Name: `Enterprise Plan`
- Description: `Unlimited jobs, premium placement, account manager, career fairs`
- Pricing:
  - Monthly: `$799.00/month` → Copy Price ID
  - Annual: `$7,990.00/year` → Copy Price ID

**Product 3: Platinum Partnership**
- Name: `Platinum Partnership`
- Description: `Dedicated pipeline, on-campus recruiting, major scholarships`
- Pricing:
  - Monthly: `$2,499.00/month` → Copy Price ID
  - Annual: `$24,990.00/year` → Copy Price ID

4. **Create Webhook:**
   - Go to: Developers → Webhooks → Add endpoint
   - Endpoint URL: `https://pittstate-connect.onrender.com/payments/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Copy **Signing secret** (starts with `whsec_`)

---

## 🔧 Step 2: Set Environment Variables on Render

Go to your Render dashboard → pittstate-connect → Environment

Add these variables:

```bash
# Stripe API Keys
STRIPE_PUBLISHABLE_KEY=pk_live_... (or pk_test_... for testing)
STRIPE_SECRET_KEY=sk_live_... (or sk_test_... for testing)
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs
STRIPE_PROFESSIONAL_PRICE_ID=price_..._professional_monthly
STRIPE_PROFESSIONAL_ANNUAL_ID=price_..._professional_annual
STRIPE_ENTERPRISE_PRICE_ID=price_..._enterprise_monthly
STRIPE_ENTERPRISE_ANNUAL_ID=price_..._enterprise_annual
STRIPE_PLATINUM_PRICE_ID=price_..._platinum_monthly
STRIPE_PLATINUM_ANNUAL_ID=price_..._platinum_annual
```

**Important:** Start with **TEST mode** keys (pk_test_, sk_test_) until you verify everything works!

---

## 📦 Step 3: Update Your Application Files

### A. Import monetization models in your main app

**Option 1: If using `app.py`:**

```python
# Add to your imports at top of app.py
from models_monetization import (
    EmployerSubscription, ScholarshipSponsorship,
    CareerFairParticipation, JobBoost,
    EmployerBrandingPackage, RevenueTransaction
)

# Register payments blueprint
from blueprints.payments import payments_bp
app.register_blueprint(payments_bp)
```

**Option 2: If using `app_pro.py`:**

```python
# Add to your imports
from models_monetization import (
    EmployerSubscription, ScholarshipSponsorship,
    CareerFairParticipation, JobBoost,
    EmployerBrandingPackage, RevenueTransaction
)

# Register payments blueprint
from blueprints.payments import payments_bp
app.register_blueprint(payments_bp)
```

### B. Add pricing link to navigation

In `templates/base.html` (or wherever your nav is), add:

```html
<!-- For employers/visitors -->
<li><a href="{{ url_for('payments.pricing') }}">Pricing</a></li>

<!-- For logged-in employers -->
{% if current_user.is_authenticated and current_user.user_type == 'employer' %}
    <li><a href="{{ url_for('payments.upgrade', plan='professional') }}">Upgrade</a></li>
{% endif %}
```

### C. Show upgrade prompts in employer dashboard

In `templates/dashboard/employer_dashboard.html`, add near the top:

```html
<!-- Include upgrade prompts -->
{% include 'components/upgrade_prompt.html' %}
```

---

## 🗄️ Step 4: Run Database Migration

**Local Testing First:**

```powershell
# Make sure you're in the project directory
cd c:\Users\conno\Downloads\Gorilla-Link1

# Activate virtual environment if you have one
# .\venv\Scripts\Activate

# Run migration
python add_monetization_migration.py
```

**Expected Output:**
```
Creating monetization tables...
✅ Successfully created:
   - employer_subscriptions
   - scholarship_sponsorships
   - career_fair_participation
   - job_boosts
   - employer_branding_packages
   - revenue_transactions

📊 Found 5 existing employers
✅ Created 5 FREE tier subscriptions for existing employers

🎉 Monetization database migration complete!
```

---

## 🚀 Step 5: Commit & Deploy to Render

```powershell
# Check status
git status

# Stage all new files
git add .

# Commit
git commit -m "Add employer monetization system with Stripe integration

- Add 4-tier pricing (FREE, Professional, Enterprise, Platinum)
- Stripe subscription checkout & webhooks
- Employer subscription management
- Database models for subscriptions, scholarships, career fairs, boosts
- Pricing page with ROI calculator
- Upgrade prompts in employer dashboard
- Revenue tracking and PSU revenue share (20%)
- Documentation and sales materials"

# Push to GitHub
git push origin main
```

**Render will automatically:**
1. Detect the new commit
2. Install dependencies (Stripe is already in requirements.txt)
3. Deploy your app
4. Restart the server

**Watch deployment:** https://dashboard.render.com/

---

## 🧪 Step 6: Test Everything (CRITICAL!)

### A. Test Pricing Page
1. Visit: `https://pittstate-connect.onrender.com/payments/pricing`
2. Verify:
   - ✅ All 4 tiers display correctly
   - ✅ ROI calculator works
   - ✅ CTA buttons work

### B. Test Upgrade Flow (Use Stripe TEST cards)
1. Log in as employer
2. Visit: `https://pittstate-connect.onrender.com/payments/upgrade?plan=professional`
3. Click "Start 14-Day Free Trial"
4. Should redirect to Stripe Checkout

**Use Stripe test card:**
- Card number: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

5. Complete checkout
6. Should redirect to success page
7. Verify subscription in database:

```python
# In Python console or via database query
subscription = EmployerSubscription.query.filter_by(user_id=YOUR_USER_ID).first()
print(subscription.tier)  # Should show 'professional'
print(subscription.status)  # Should show 'active'
```

### C. Test Webhook
1. Go to Stripe Dashboard → Webhooks
2. Click on your webhook
3. Click "Send test webhook"
4. Select `customer.subscription.updated`
5. Click "Send test webhook"
6. Should see 200 OK response

### D. Test Upgrade Prompts
1. Log in as FREE tier employer
2. Post 1 job (hit limit)
3. Visit dashboard
4. Should see upgrade prompt

---

## 🔄 Step 7: Run Database Migration on Production

**SSH into Render or use Python console:**

```python
from app import app, db
from models_monetization import *
from add_monetization_migration import add_monetization_tables

# Run migration
add_monetization_tables(app)
```

**OR via Render Shell:**

```bash
# In Render dashboard, click "Shell" button
python add_monetization_migration.py
```

---

## 🎉 Step 8: Verify Production Deployment

### Check these URLs:
- ✅ Pricing page: https://pittstate-connect.onrender.com/payments/pricing
- ✅ Upgrade page: https://pittstate-connect.onrender.com/payments/upgrade?plan=professional
- ✅ Webhook endpoint: https://pittstate-connect.onrender.com/payments/webhook (should return 405 Method Not Allowed for GET - that's correct!)

### Check Stripe Dashboard:
- ✅ Products created
- ✅ Prices created
- ✅ Webhook configured
- ✅ Test mode enabled initially

---

## 💰 Step 9: Go LIVE with Real Payments

**When ready to accept real payments:**

1. **Enable Stripe Live Mode:**
   - Complete Stripe verification (business info, bank account)
   - Get verified by Stripe

2. **Switch to Live Keys in Render:**
   - Replace `pk_test_...` with `pk_live_...`
   - Replace `sk_test_...` with `sk_live_...`
   - Update webhook secret to live mode secret

3. **Test with Real Card:**
   - Use YOUR OWN credit card (don't charge yourself, cancel immediately)
   - Verify subscription creates correctly
   - Verify webhook receives events
   - Cancel test subscription

4. **Ready to Launch! 🚀**

---

## 📧 Step 10: Start Sending Sales Emails

Now that everything is deployed and working:

1. **Get 100 Kansas employer emails** (use templates in QUICK_START_MONETIZATION.md)
2. **Send FREE tier launch email** (Day 1)
3. **Follow up with phone calls** (Days 2-7)
4. **Convert to Professional** (Days 8-14)
5. **Close Enterprise deals** (Days 15-21)
6. **Secure scholarships** (Days 22-30)

**Goal:** $26,083 in 30 days 💰

---

## 🐛 Troubleshooting

### Issue: "No module named 'models_monetization'"
**Fix:** Make sure you imported models in your app file:
```python
from models_monetization import *
```

### Issue: "Table already exists"
**Fix:** Tables were created previously. Skip migration or drop/recreate:
```python
db.drop_all()
db.create_all()
```

### Issue: Stripe checkout not loading
**Fix:** 
1. Check Stripe keys are set in environment variables
2. Check browser console for errors
3. Verify `STRIPE_PUBLISHABLE_KEY` is correct

### Issue: Webhook not working
**Fix:**
1. Verify webhook URL is correct
2. Check webhook secret matches environment variable
3. Look at webhook logs in Stripe Dashboard

### Issue: "Customer does not exist"
**Fix:** Delete old test data:
```python
subscription = EmployerSubscription.query.filter_by(user_id=USER_ID).first()
subscription.stripe_customer_id = None
db.session.commit()
```

---

## 📊 Monitoring After Launch

### Daily Checks:
- [ ] Check Render logs for errors
- [ ] Check Stripe dashboard for new subscriptions
- [ ] Monitor revenue_transactions table
- [ ] Track FREE → Professional conversion rate

### Weekly Checks:
- [ ] Review upgrade prompt performance
- [ ] Check churn rate (cancellations)
- [ ] Analyze which plans are most popular
- [ ] Review webhook error logs

### Monthly Checks:
- [ ] Calculate total revenue
- [ ] Calculate PSU's 20% share
- [ ] Prepare PittState report
- [ ] Review and optimize pricing

---

## 🎯 Success Metrics (30 Days)

| Metric | Goal | Current |
|--------|------|---------|
| FREE signups | 20 | ___ |
| Professional conversions | 5 | ___ |
| Enterprise conversions | 1 | ___ |
| Scholarships secured | 3 | ___ |
| Monthly Recurring Revenue | $2,294 | ___ |
| Total 30-day revenue | $26,083 | ___ |

---

## 🦍 YOU'RE READY TO LAUNCH!

**Deployment Status:**
- ✅ Stripe account created
- ✅ Products & prices configured
- ✅ Environment variables set
- ✅ Code committed & deployed
- ✅ Database migrated
- ✅ Testing complete

**Next Step:** Send your first 10 sales emails TODAY! 📧

**Remember:** The hardest part is DONE. Now it's just execution.

**GO GORILLAS!** 🦍💰
