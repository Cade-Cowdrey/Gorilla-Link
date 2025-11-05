# ⚡ ACTION CHECKLIST - DO THIS NOW!
## Complete These Steps in the Next Hour

---

## ✅ IMMEDIATE ACTIONS (RIGHT NOW)

### 1. Check Render Deployment (2 minutes)
- [ ] Go to: https://dashboard.render.com/
- [ ] Find: pittstate-connect service
- [ ] Status: Should show "Live" with green checkmark
- [ ] If still deploying: Wait for it to finish (usually 3-5 minutes)
- [ ] Check logs for any errors

**If deployment fails:**
- Look at error message in logs
- Most common: missing imports or syntax errors
- Fix and push again

---

### 2. Create Stripe Account & Get API Keys (10 minutes)

**Go to:** https://dashboard.stripe.com/register

**Step 1: Sign up**
- [ ] Enter your email, create password
- [ ] Verify email
- [ ] Enter business info (PittState/Your name)
- [ ] Skip verification for now (stay in TEST mode)

**Step 2: Get API Keys**
- [ ] Click: Developers → API keys
- [ ] Copy **Publishable key** (starts with `pk_test_`)
- [ ] Copy **Secret key** (starts with `sk_test_`) - Click "Reveal test key"
- [ ] Save both keys in a safe place

---

### 3. Create Stripe Products (15 minutes)

**Go to:** Products → Add Product

**Product 1: Professional Plan**
```
Name: Professional Plan
Description: 5 jobs, featured placement, unlimited views, AI matching
```
Pricing:
- [ ] Click "+ Add another price"
- [ ] Recurring: Monthly, $299.00
- [ ] Click "Add price"
- [ ] Copy the Price ID (looks like: price_1A2B3C...)
- [ ] Click "+ Add another price" again
- [ ] Recurring: Yearly, $2,988.00
- [ ] Copy this Price ID too

**Product 2: Enterprise Plan**
```
Name: Enterprise Plan
Description: Unlimited jobs, premium placement, account manager
```
Pricing:
- [ ] Monthly: $799.00 → Copy Price ID
- [ ] Yearly: $7,990.00 → Copy Price ID

**Product 3: Platinum Partnership**
```
Name: Platinum Partnership
Description: Dedicated pipeline, on-campus recruiting, scholarships
```
Pricing:
- [ ] Monthly: $2,499.00 → Copy Price ID
- [ ] Yearly: $24,990.00 → Copy Price ID

**You should now have 6 Price IDs** (3 monthly, 3 annual)

---

### 4. Set Up Webhook (5 minutes)

**Go to:** Developers → Webhooks → Add endpoint

```
Endpoint URL: https://pittstate-connect.onrender.com/payments/webhook
Description: Production webhook for subscriptions
```

**Events to send:**
- [ ] `checkout.session.completed`
- [ ] `customer.subscription.created`
- [ ] `customer.subscription.updated`
- [ ] `customer.subscription.deleted`
- [ ] `invoice.payment_succeeded`
- [ ] `invoice.payment_failed`

- [ ] Click "Add endpoint"
- [ ] Click on the webhook you just created
- [ ] Copy the **Signing secret** (starts with `whsec_`)

---

### 5. Add Environment Variables to Render (5 minutes)

**Go to:** https://dashboard.render.com/ → pittstate-connect → Environment

**Click "Add Environment Variable" for each:**

```bash
STRIPE_PUBLISHABLE_KEY
Value: pk_test_... (paste your publishable key)

STRIPE_SECRET_KEY
Value: sk_test_... (paste your secret key)

STRIPE_WEBHOOK_SECRET
Value: whsec_... (paste your webhook secret)

STRIPE_PROFESSIONAL_PRICE_ID
Value: price_... (monthly Professional price ID)

STRIPE_PROFESSIONAL_ANNUAL_ID
Value: price_... (annual Professional price ID)

STRIPE_ENTERPRISE_PRICE_ID
Value: price_... (monthly Enterprise price ID)

STRIPE_ENTERPRISE_ANNUAL_ID
Value: price_... (annual Enterprise price ID)

STRIPE_PLATINUM_PRICE_ID
Value: price_... (monthly Platinum price ID)

STRIPE_PLATINUM_ANNUAL_ID
Value: price_... (annual Platinum price ID)
```

- [ ] After adding all variables, click "Save Changes"
- [ ] Render will automatically redeploy (takes 2-3 minutes)

---

### 6. Update App to Register Blueprints (2 minutes)

**Open:** `app.py` (or `app_pro.py` if you use that)

**Find the section where blueprints are registered** (usually near the bottom), and add:

```python
# Import monetization models (add near top with other imports)
from models_monetization import (
    EmployerSubscription, ScholarshipSponsorship,
    CareerFairParticipation, JobBoost,
    EmployerBrandingPackage, RevenueTransaction
)

# Register payments blueprint (add with other blueprint registrations)
from blueprints.payments import payments_bp
app.register_blueprint(payments_bp)
```

**Save and commit:**
```powershell
git add app.py
git commit -m "Register payments blueprint for monetization"
git push origin main
```

---

### 7. Run Database Migration (3 minutes)

**Option A: Via Render Shell**
1. Go to Render dashboard → pittstate-connect
2. Click "Shell" button (top right)
3. Wait for shell to load
4. Run: `python add_monetization_migration.py`
5. Should see: "✅ Successfully created 6 tables"

**Option B: Via Python Console**
1. Open your local terminal
2. Connect to production database
3. Run migration script

**You should see:**
```
Creating monetization tables...
✅ Successfully created:
   - employer_subscriptions
   - scholarship_sponsorships
   - career_fair_participation
   - job_boosts
   - employer_branding_packages
   - revenue_transactions
```

---

### 8. Test Pricing Page (2 minutes)

**Visit:** https://pittstate-connect.onrender.com/payments/pricing

**Check:**
- [ ] Page loads without errors
- [ ] All 4 pricing tiers display
- [ ] ROI calculator works (change numbers, see it update)
- [ ] "Start Free Today" button works
- [ ] "Upgrade" buttons work

**If page doesn't load:**
- Check Render logs for errors
- Make sure blueprints are registered
- Verify templates folder exists

---

### 9. Test Upgrade Flow with Stripe Test Card (5 minutes)

**Step 1: Create Test Employer Account**
- [ ] Sign up as new employer (or use existing test account)
- [ ] Make sure you're logged in

**Step 2: Visit Upgrade Page**
- [ ] Go to: https://pittstate-connect.onrender.com/payments/upgrade?plan=professional
- [ ] Should see upgrade page with pricing details
- [ ] Click "Start 14-Day Free Trial"

**Step 3: Complete Stripe Checkout**
- [ ] Should redirect to Stripe Checkout page
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Expiry: Any future date (e.g., 12/25)
- [ ] CVC: Any 3 digits (e.g., 123)
- [ ] ZIP: Any 5 digits (e.g., 12345)
- [ ] Email: Your test email
- [ ] Click "Subscribe"

**Step 4: Verify Success**
- [ ] Should redirect to success page
- [ ] Should see "Welcome to Professional!" message
- [ ] Check Stripe Dashboard → Customers (should see new test customer)
- [ ] Check Stripe Dashboard → Subscriptions (should see active subscription)

**If something breaks:**
- Check Render logs for webhook errors
- Verify all Stripe environment variables are set correctly
- Make sure webhook endpoint is accessible

---

### 10. Test Webhook (2 minutes)

**Go to:** Stripe Dashboard → Webhooks → Your webhook

**Click:** Send test webhook
**Select:** `customer.subscription.updated`
**Click:** Send test webhook

**Should see:**
- Status: 200 OK
- Response shows success

**If you see errors:**
- Check webhook URL is correct
- Verify webhook secret matches environment variable
- Look at Render logs for error details

---

## 🎉 YOU'RE LIVE! (If all checkboxes above are ✅)

### Final Verification:
- [ ] Pricing page loads
- [ ] Upgrade flow works
- [ ] Test payment succeeds
- [ ] Subscription creates in database
- [ ] Webhook receives events
- [ ] No errors in Render logs

---

## 📧 NEXT: SEND SALES EMAILS (Tomorrow)

### Prepare Tonight:
1. **Create 100-person email list**
   - Kansas Chamber of Commerce members
   - PSU alumni business owners
   - Companies that hired PSU students before
   - Local businesses (manufacturers, tech, healthcare)

2. **Set up email tool**
   - Gmail with mail merge (free, easy)
   - Mailchimp (better tracking)
   - SendGrid (most professional)

3. **Customize email template**
   - Use template from QUICK_START_MONETIZATION.md
   - Add your name, phone, photo
   - Update signup link

### Tomorrow Morning:
1. **Send 10 emails** (9am)
2. **Send 40 more emails** (afternoon)
3. **Follow up with phone calls** (end of day)

### This Week:
- **Goal:** 20 FREE employers signed up
- **Metric:** 20% conversion rate from email → signup
- **Time investment:** 2-3 hours/day sending emails + calling

---

## 🎯 30-DAY REVENUE GOAL: $26,083

| Week | Goal | Actions |
|------|------|---------|
| Week 1 | 20 FREE signups | Send 100 emails, make 50 calls |
| Week 2 | 5 Professional ($1,495/mo) | Upsell email + demos |
| Week 3 | 1 Enterprise ($799/mo) | Direct sales to larger companies |
| Week 4 | 3 Scholarships ($15K) | Meet with local business owners |

---

## 🚨 TROUBLESHOOTING

### "No module named 'stripe'"
**Fix:** Stripe is in requirements.txt, but Render needs to reinstall. Trigger redeploy or add a comment to requirements.txt and push.

### "STRIPE_SECRET_KEY not found"
**Fix:** Environment variables not set. Go to Render → Environment → Add variables → Save changes → Wait for redeploy.

### "404 Not Found" on pricing page
**Fix:** Blueprint not registered. Add `app.register_blueprint(payments_bp)` to app.py and push.

### Webhook returns 500 error
**Fix:** Check Render logs. Usually missing database table or incorrect webhook secret.

### Test payment doesn't create subscription
**Fix:** Check webhook is firing. Go to Stripe → Webhooks → View logs. If events aren't being sent, check webhook URL.

---

## 💪 YOU GOT THIS!

**Status Right Now:**
- ✅ Code is deployed
- ⏳ Stripe needs configuration (you're doing this now)
- ⏳ Database needs migration (next step)
- ⏳ Testing needs to happen (after migration)
- ⏳ Sales emails need to go out (tomorrow)

**By end of today:**
- All checkboxes above should be ✅
- Pricing page should be live
- Payment flow should work
- You should be ready to send emails tomorrow

**By end of this week:**
- 20 FREE employers signed up
- First demo calls scheduled
- $1,000+ in pipeline

**By end of this month:**
- $26,083 in revenue
- 5 Professional subscribers
- 1 Enterprise client
- 3 scholarships secured

---

## 🦍 GO MAKE IT HAPPEN!

**Start with Step 1 above. Work through the list. You'll be live in 1 hour.**

**GO GORILLAS!** 💰
