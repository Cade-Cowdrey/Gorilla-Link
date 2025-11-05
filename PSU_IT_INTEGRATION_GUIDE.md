# 🏫 PSU IT Integration Guide
## How to Connect PittState-Connect to Existing PSU Systems

**For**: Pittsburg State University IT Department  
**Platform**: PittState-Connect Career Services  
**Purpose**: Step-by-step integration with PSU infrastructure

---

## Overview 🎯

This guide shows PSU IT how to integrate PittState-Connect with:
1. ✅ PSU Single Sign-On (Azure AD)
2. ✅ Canvas LMS
3. ✅ PSU Email (@pittstate.edu)
4. ✅ Banner/Ellucian Student System
5. ✅ PSU Network & Firewall
6. ✅ PSU Monitoring Systems

**Integration Difficulty**: ⭐⭐ Moderate (2-3 weeks)

---

## 1. Azure AD Single Sign-On Integration 🔐

### What It Does:
- Students/faculty log in with PSU credentials
- Automatic account creation on first login
- No separate passwords to remember
- Centralized access control

### PSU IT Tasks:

#### Step 1: Register App in Azure AD
```bash
# Azure Portal > App Registrations > New Registration

Name: PittState-Connect
Supported account types: Single tenant (PSU only)
Redirect URI: 
  - https://pittstate-connect.onrender.com/auth/microsoft/callback
  - https://pittstate-connect.onrender.com/oauth/microsoft/callback

API permissions needed:
  - User.Read (basic profile)
  - email
  - openid
  - profile
```

#### Step 2: Get Credentials
After registration, copy these values:
- **Application (client) ID**: `12345678-1234-1234-1234-123456789abc`
- **Directory (tenant) ID**: `pittstate.edu` or GUID
- **Client secret**: Create one in "Certificates & secrets"

#### Step 3: Provide to Platform Team
Send us these environment variables:
```bash
MICROSOFT_CLIENT_ID=<your_client_id>
MICROSOFT_CLIENT_SECRET=<your_client_secret>
MICROSOFT_TENANT_ID=<your_tenant_id>

# Optional: Restrict to PSU domain
ALLOWED_EMAIL_DOMAINS=pittstate.edu,gus.pittstate.edu
```

#### Step 4: Configure User Sync (Optional)
If you want automatic user provisioning:
```bash
# Enable SCIM endpoint
SCIM_ENABLED=True
SCIM_TOKEN=<generate_secure_token>

# Azure AD > Enterprise Apps > PittState-Connect > Provisioning
Provisioning Mode: Automatic
Tenant URL: https://pittstate-connect.onrender.com/scim/v2
Secret Token: <SCIM_TOKEN>
```

### Testing SSO:
1. User visits: https://pittstate-connect.onrender.com
2. Clicks "Sign in with Microsoft"
3. Redirects to PSU login.microsoftonline.com
4. After PSU authentication, creates account automatically
5. Future logins are instant (no password needed)

**Estimated Time**: 2 hours

---

## 2. Canvas LMS Integration 📚

### What It Does:
- Import student course data
- Sync enrollment information
- Display student schedules
- Career advising based on major/courses

### PSU IT Tasks:

#### Step 1: Create Canvas API Token
```bash
# Canvas > Account > Settings > Approved Integrations > New Access Token

Purpose: PittState-Connect Career Platform
Expires: Never (or set 1-year renewal)
Scopes needed:
  - Read user data (url:GET|/api/v1/users/:id)
  - Read course data (url:GET|/api/v1/courses)
  - Read enrollment data (url:GET|/api/v1/courses/:id/enrollments)
```

#### Step 2: Provide Credentials
```bash
CANVAS_API_URL=https://pittstate.instructure.com
CANVAS_API_TOKEN=<your_access_token>
CANVAS_ACCOUNT_ID=<psu_account_id>  # Usually 1 or your root account ID
```

#### Step 3: Configure Sync Schedule
```bash
# How often to sync Canvas data
CANVAS_SYNC_ENABLED=True
CANVAS_SYNC_INTERVAL=daily  # Options: hourly, daily, weekly
CANVAS_SYNC_TIME=02:00      # 2 AM daily sync
```

### What Gets Synced:
- ✅ Student course enrollments
- ✅ Graduation year (calculated from cohort)
- ✅ Academic major (from Canvas profile)
- ✅ GPA (if stored in Canvas)
- ❌ Does NOT sync: Grades, assignments, private data

### Security:
- Read-only access
- No data modification in Canvas
- Canvas audit logs show all API calls
- Rate limited to Canvas guidelines (3000 req/hour)

**Estimated Time**: 3 hours

---

## 3. PSU Email Integration 📧

### What It Does:
- Send emails from @pittstate.edu domain
- Email verification for new users
- Notifications and reminders
- Employer communications

### PSU IT Tasks:

#### Option A: Use PSU SMTP Relay (Recommended)
```bash
# Add pittstate-connect.onrender.com to SMTP relay whitelist

MAIL_SERVER=smtp.pittstate.edu
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=pittstate-connect@pittstate.edu
MAIL_PASSWORD=<service_account_password>
MAIL_DEFAULT_SENDER=no-reply@pittstate.edu
```

#### Option B: Use SendGrid with PSU Domain
```bash
# SendGrid > Settings > Sender Authentication > Domain Authentication
# Add DNS records to pittstate.edu zone:

pittstate-connect._domainkey.pittstate.edu  CNAME  sendgrid.net
s1._domainkey.pittstate.edu                  CNAME  s1.domainkey.u12345.wl.sendgrid.net
s2._domainkey.pittstate.edu                  CNAME  s2.domainkey.u12345.wl.sendgrid.net

MAIL_SERVER=smtp.sendgrid.net
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sendgrid_api_key>
```

### Email Security:
- ✅ SPF record (prevents spoofing)
- ✅ DKIM signing (validates sender)
- ✅ DMARC policy (reject unauthorized)
- ✅ Unsubscribe links (CAN-SPAM compliant)

**Estimated Time**: 1-2 hours

---

## 4. Banner/Ellucian Integration 🎓

### What It Does:
- Validate student IDs
- Verify enrollment status
- Check alumni status
- Import academic history

### PSU IT Tasks:

#### Step 1: Create Banner API Access
```bash
# Banner > System Administration > Integration > API Management

Create Service Account: pittstate-connect-svc
Grant Permissions:
  - Student demographic data (read)
  - Enrollment verification (read)
  - Graduation status (read)
  - Alumni records (read)

# Ellucian Ethos API (if available)
BANNER_API_URL=https://banner.pittstate.edu/ethos/api
BANNER_API_KEY=<ethos_api_key>
```

#### Step 2: Configure Database Direct Access (Alternative)
If Banner API not available, provide read-only database access:
```bash
# Create read-only PostgreSQL/Oracle user

BANNER_DB_HOST=banner-db.pittstate.edu
BANNER_DB_PORT=1521
BANNER_DB_NAME=PROD
BANNER_DB_USER=pittstate_connect_ro
BANNER_DB_PASSWORD=<secure_password>

# Grant SELECT on these views:
- SATURN.SPRIDEN (student identification)
- SATURN.SGBSTDN (student data)
- SATURN.SHRDGMR (degree information)
- SATURN.SFBETRM (enrollment terms)
```

### Data Sync:
```python
# What we'll query from Banner
- Student ID validation (is this a real PSU ID?)
- Enrollment status (current student, graduated, withdrawn)
- Expected graduation date
- Academic program/major
- Alumni status and graduation year
```

**Security**:
- ✅ Read-only access (no data modification)
- ✅ IP whitelist (only Render servers)
- ✅ Encrypted connections (SSL/TLS)
- ✅ Query rate limiting
- ✅ PSU audit logs enabled

**Estimated Time**: 4-6 hours (depends on Banner setup)

---

## 5. Network & Firewall Configuration 🔥

### What PSU IT Needs to Allow:

#### Inbound Traffic (to PSU systems from Render):
```bash
# Render IP Ranges (whitelist these)
Source IPs: 
  - 44.234.xxx.xxx/32  (Render deployment region)
  - 52.xx.xxx.xxx/32    (Render deployment region)
  # Get exact IPs from Render dashboard > Settings > Network

Destinations:
  - PSU SMTP relay: smtp.pittstate.edu:587
  - Banner API: banner.pittstate.edu:443
  - Canvas API: pittstate.instructure.com:443 (already public)
  - Azure AD: login.microsoftonline.com:443 (already public)

Protocols: HTTPS (443), SMTP (587)
```

#### Outbound Traffic (from PSU to platform):
```bash
# PSU users accessing platform
Destination: pittstate-connect.onrender.com
Port: 443 (HTTPS)
Protocol: TCP

# Webhooks (Canvas, Banner notifications)
Webhook Endpoint: https://pittstate-connect.onrender.com/webhooks/*
Method: POST
Authentication: Shared secret or HMAC signature
```

### Firewall Rules:
```bash
# Rule 1: Allow PSU staff/students to access platform
Source: PSU network (all)
Destination: pittstate-connect.onrender.com (443)
Action: ALLOW

# Rule 2: Allow platform to query Banner API
Source: Render IPs (whitelist)
Destination: banner.pittstate.edu (443)
Action: ALLOW

# Rule 3: Allow platform to send email via SMTP
Source: Render IPs (whitelist)
Destination: smtp.pittstate.edu (587)
Action: ALLOW
```

**Estimated Time**: 2 hours

---

## 6. PSU Monitoring Integration 📊

### Connect to PSU SIEM/Splunk:

#### Option A: Syslog Integration
```bash
# Forward application logs to PSU Splunk
SYSLOG_HOST=splunk.pittstate.edu
SYSLOG_PORT=514
SYSLOG_PROTOCOL=tcp
SYSLOG_FACILITY=local5

# Log format: RFC5424
# Sends: Auth events, errors, security alerts
```

#### Option B: HTTP Event Collector
```bash
# Splunk HEC endpoint
SPLUNK_HEC_URL=https://splunk.pittstate.edu:8088/services/collector
SPLUNK_HEC_TOKEN=<hec_token>
SPLUNK_INDEX=pittstate_connect

# Real-time event streaming
```

### Monitoring Endpoints:
```bash
# Health check (for PSU monitoring tools)
GET https://pittstate-connect.onrender.com/health
Response: {"status": "healthy", "database": "ok", "redis": "ok"}

# Metrics (Prometheus format)
GET https://pittstate-connect.onrender.com/metrics
Response: Prometheus-compatible metrics

# Status page (public)
GET https://pittstate-connect.onrender.com/status
Response: System status dashboard
```

### Alerts to Send PSU IT:
- 🚨 Database connection failures
- 🚨 Authentication service down
- 🚨 Unusual failed login attempts (>10/min)
- 🚨 High error rate (>5% of requests)
- ⚠️ Slow response times (>2s average)
- ⚠️ Disk space low (<20% free)

**Estimated Time**: 3 hours

---

## 7. Production Deployment Checklist ✅

### Pre-Launch (PSU IT):
- [ ] Azure AD app registered and tested
- [ ] Canvas API token created and permissions verified
- [ ] PSU email relay configured and tested
- [ ] Banner integration credentials provided
- [ ] Firewall rules approved and deployed
- [ ] Monitoring integration configured
- [ ] SSL certificate valid (Render auto-manages)
- [ ] Backup procedures documented
- [ ] Incident response plan agreed upon

### Pre-Launch (Platform Team):
- [ ] All PSU credentials configured in Render environment
- [ ] Database migrations applied
- [ ] Initial admin accounts created for PSU IT
- [ ] Email templates customized with PSU branding
- [ ] Rate limits configured appropriately
- [ ] Monitoring alerts set up
- [ ] Backup schedule confirmed
- [ ] Rollback plan documented

### Launch Day:
1. **9:00 AM**: Final system checks
2. **10:00 AM**: Enable SSO for PSU users
3. **10:30 AM**: Test logins with 5 pilot users
4. **11:00 AM**: Enable email notifications
5. **1:00 PM**: Monitor for 2 hours (both teams)
6. **3:00 PM**: Go/No-Go decision
7. **4:00 PM**: Send announcement email to PSU community

### Post-Launch Monitoring (First Week):
- Day 1: Every 2 hours check logs, performance, errors
- Day 2-3: Every 4 hours
- Day 4-7: Daily checks
- Week 2+: Weekly reviews

---

## 8. Common Integration Issues & Solutions 🔧

### Issue 1: SSO Login Fails
**Symptom**: Users redirected to PSU login, but get error after authentication  
**Causes**:
- Redirect URI mismatch in Azure AD
- Tenant ID incorrect
- App permissions not granted

**Solution**:
```bash
# Verify redirect URI matches EXACTLY:
Azure AD: https://pittstate-connect.onrender.com/auth/microsoft/callback
Platform: MICROSOFT_REDIRECT_URI=https://pittstate-connect.onrender.com/auth/microsoft/callback

# Check admin consent granted for permissions
```

### Issue 2: Canvas Sync Not Working
**Symptom**: Student courses not appearing in platform  
**Causes**:
- API token expired or invalid
- Canvas account ID wrong
- Rate limit exceeded

**Solution**:
```bash
# Test Canvas API manually:
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://pittstate.instructure.com/api/v1/accounts/1/courses

# Check platform logs for Canvas API errors
# Verify CANVAS_ACCOUNT_ID matches your root account
```

### Issue 3: Emails Not Sending
**Symptom**: Users not receiving verification emails  
**Causes**:
- SMTP relay blocked by firewall
- Service account password expired
- SPF/DKIM not configured

**Solution**:
```bash
# Test SMTP connection:
telnet smtp.pittstate.edu 587

# Check Render logs for SMTP errors
# Verify PSU firewall allows Render IPs
```

### Issue 4: Banner Data Not Syncing
**Symptom**: Student IDs not validating  
**Causes**:
- Database credentials incorrect
- IP not whitelisted for Banner DB
- Wrong table/view names

**Solution**:
```bash
# Test database connection:
psql -h banner-db.pittstate.edu -U pittstate_connect_ro -d PROD

# Verify IP whitelisting:
SELECT * FROM v$session WHERE username='PITTSTATE_CONNECT_RO';

# Check exact table names in Banner (they vary by institution)
```

---

## 9. Maintenance & Updates 🔄

### Regular Maintenance Tasks:

#### Weekly (Automated):
- Database backups (Render automatic)
- Security updates (Render automatic)
- Log rotation
- Performance metrics review

#### Monthly (PSU IT + Platform Team):
- Review audit logs for anomalies
- Check API token expirations
- Update dependencies if needed
- Review error rates and fix issues
- Capacity planning (user growth)

#### Quarterly:
- Security audit review
- Update documentation
- Test disaster recovery procedures
- Review SLA metrics
- User feedback session

### Updating Platform Code:
```bash
# Platform updates deployed via Git push
# Render auto-deploys from main branch

# Zero-downtime deployment process:
1. Code pushed to GitHub
2. Render builds new version
3. Health checks pass
4. Automatic traffic switch
5. Old version shut down

# Rollback if needed:
Render Dashboard > Deployments > Redeploy previous version
```

### Emergency Contacts:
```bash
# Platform Team
Primary: Cade Cowdrey
Email: developer@pittstate-connect.com
Phone: (XXX) XXX-XXXX (during business hours)
Slack: #pittstate-connect-support

# PSU IT
Primary: <PSU IT Director>
Secondary: <PSU Network Admin>
Emergency Line: (620) XXX-XXXX
```

---

## 10. Cost & Resource Requirements 💰

### Platform Costs (Render Hosting):
- **Hosting**: $25-85/month (scales with users)
- **Database**: $7-50/month (PostgreSQL)
- **Redis Cache**: $10/month (optional)
- **Backups**: Included
- **SSL Certificates**: Included (auto-renew)

**Total**: ~$50-150/month depending on usage

### PSU IT Resources Required:

#### Initial Setup (One-Time):
- Network Administrator: 4 hours
- Active Directory Admin: 2 hours
- Banner Administrator: 4 hours
- Canvas Administrator: 2 hours
- Email Administrator: 2 hours
- **Total**: ~14 hours over 2-3 weeks

#### Ongoing Maintenance (Monthly):
- Monitoring: 2 hours/month (mostly automated)
- Updates/Changes: 1-2 hours/month
- **Total**: ~3-4 hours/month

### No Additional Infrastructure:
- ✅ No PSU servers required (cloud-hosted)
- ✅ No PSU database space needed
- ✅ No PSU storage needed
- ✅ No PSU bandwidth concerns (Render handles)

---

## 11. Security Review by PSU IT 🔒

**Before going live, PSU IT should verify:**

### Authentication:
- [ ] SSO works with PSU credentials
- [ ] Only @pittstate.edu emails can register
- [ ] Session timeouts configured appropriately
- [ ] Password policies match PSU standards (if local accounts allowed)

### Network Security:
- [ ] Firewall rules tested and working
- [ ] IP whitelisting effective
- [ ] All traffic encrypted (TLS 1.3)
- [ ] No unauthorized ports open

### Data Protection:
- [ ] Student data encrypted at rest and in transit
- [ ] PII redacted in logs
- [ ] Backup encryption enabled
- [ ] Data retention policy documented

### Compliance:
- [ ] FERPA requirements met
- [ ] PSU IT security policies followed
- [ ] Audit logging enabled and reviewed
- [ ] Incident response plan agreed upon

### Monitoring:
- [ ] PSU SIEM receiving logs
- [ ] Alerts configured and tested
- [ ] Health checks responding
- [ ] Performance metrics visible

**Sign-off Required**: PSU IT Director or designee

---

## 12. Go-Live Timeline 📅

### Week 1: Planning & Credentials
- **Day 1-2**: PSU IT reviews security audit
- **Day 3**: Kickoff meeting (PSU IT + Platform Team)
- **Day 4-5**: PSU IT creates service accounts and API tokens

### Week 2: Integration & Testing
- **Day 1**: Configure SSO (Azure AD)
- **Day 2**: Test SSO with pilot group (5 users)
- **Day 3**: Configure Canvas, email, Banner
- **Day 4**: End-to-end testing
- **Day 5**: Load testing with 50 users

### Week 3: Soft Launch
- **Day 1**: Firewall rules deployed
- **Day 2**: Monitoring integration verified
- **Day 3**: Soft launch to Career Services staff (10 users)
- **Day 4-5**: Bug fixes and adjustments

### Week 4: Full Launch
- **Day 1**: Final systems check
- **Day 2**: **GO-LIVE** 🚀
- **Day 3-5**: Intensive monitoring
- **Day 6-7**: First week review meeting

---

## 13. Success Metrics 📈

**How to measure successful integration:**

### Technical Metrics:
- ✅ SSO login success rate >95%
- ✅ Average page load time <2 seconds
- ✅ API error rate <1%
- ✅ Uptime >99.5%
- ✅ Zero security incidents

### User Adoption:
- Week 1: 50 users (Career Services staff)
- Month 1: 500 users (students, employers)
- Month 3: 2,000 users (campus-wide)
- Month 6: 5,000+ users (includes alumni)

### Business Impact:
- Student resume completion rate
- Employer job postings
- Career fair attendance
- Alumni engagement
- Revenue generated (subscriptions, sponsorships)

---

## 14. Documentation for PSU IT 📚

**All documentation available**:

1. **Security Audit**: `PSU_IT_SECURITY_AUDIT.md` (this review)
2. **Integration Guide**: `PSU_IT_INTEGRATION_GUIDE.md` (this document)
3. **API Reference**: `API_REFERENCE.md`
4. **Architecture**: `ARCHITECTURE.md`
5. **Deployment**: `FINAL_DEPLOYMENT_GUIDE.md`
6. **Monitoring**: `PRODUCTION_READINESS.md`
7. **Database Schema**: `DB_guide.md`
8. **OAuth Setup**: `OAUTH_SETUP_GUIDE.md`

**Access to source code**: Available to PSU IT upon request

---

## 15. Next Steps ➡️

**For PSU IT to approve integration:**

1. ✅ Review security audit (`PSU_IT_SECURITY_AUDIT.md`)
2. ✅ Review this integration guide
3. ✅ Schedule kickoff meeting
4. ✅ Assign PSU IT point of contact
5. ✅ Approve timeline (2-3 weeks)
6. ✅ Create service accounts and tokens
7. ✅ Begin Week 1 implementation

**Contact to get started**:
- Email: pittstate-connect-team@pittstate.edu
- Meeting: Schedule 1-hour kickoff call
- Documentation: Shared Google Drive with all docs

---

**🦍 Ready to integrate with PSU systems and launch to the Gorilla community!**

---

*Last Updated: November 4, 2025*  
*Version: 1.0 - Initial Integration Guide*
