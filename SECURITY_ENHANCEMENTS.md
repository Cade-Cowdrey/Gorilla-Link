# 🔒 Security Enhancements - November 2, 2025

## Overview
This document details the security improvements added to PittState-Connect to enhance protection against common web vulnerabilities.

---

## ✅ **Enhancements Implemented**

### 1. **Input Sanitization (XSS Protection)**

**Files Modified:**
- `blueprints/scholarships/routes.py`
- `utils/input_validation.py` (new)

**What It Does:**
- Sanitizes HTML input in scholarship essays to prevent Cross-Site Scripting (XSS) attacks
- Uses `bleach` library to strip potentially malicious HTML/JavaScript
- Only allows safe HTML tags: `<p>`, `<br>`, `<strong>`, `<em>`, `<u>`

**Example:**
```python
from utils.input_validation import sanitize_html

# User input: <script>alert('XSS')</script><p>My essay</p>
# After sanitization: <p>My essay</p>
essay = sanitize_html(user_input, level='basic')
```

**Impact:** Prevents attackers from injecting malicious scripts through form inputs.

---

### 2. **File Upload Security**

**Files Modified:**
- `blueprints/scholarships/routes.py`

**What It Does:**
- Validates file extensions (only PDF, DOC, DOCX, JPG, PNG allowed)
- Checks file size (maximum 5MB per file)
- Uses `secure_filename()` to prevent directory traversal attacks
- Adds timestamp prefix to prevent filename collisions

**Security Checks:**
```python
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Rejects: dangerous.exe, ../../../etc/passwd, huge-file.pdf (>5MB)
# Accepts: resume.pdf, transcript.docx, photo.jpg
```

**Impact:** Prevents malicious file uploads and server resource exhaustion.

---

### 3. **Input Validation Utilities**

**Files Created:**
- `utils/input_validation.py`

**What It Provides:**
- `sanitize_html()` - Strip malicious HTML
- `validate_email()` - RFC 5322 compliant email validation
- `validate_phone()` - US/international phone validation
- `validate_url()` - URL format validation with optional HTTPS enforcement
- `sanitize_filename()` - Safe filename generation
- `validate_integer()` / `validate_float()` - Safe number conversion with range checking
- `sanitize_sql_like()` - Escape SQL LIKE wildcards
- `check_sql_injection_patterns()` - Detect suspicious SQL patterns
- `safe_redirect_url()` - Prevent open redirect vulnerabilities
- `sanitize_json_keys()` - Filter JSON to allowed keys only

**Usage Example:**
```python
from utils.input_validation import validate_email, validate_integer

# Email validation
if not validate_email(user_input):
    flash("Invalid email address", "danger")
    
# Integer validation with range
age = validate_integer(request.form.get('age'), min_val=18, max_val=120)
if age is None:
    abort(400, "Age must be between 18 and 120")
```

**Impact:** Centralized, reusable security functions for all endpoints.

---

### 4. **Security Headers**

**Files Created:**
- `utils/security_headers.py`

**What It Adds:**
- **Content-Security-Policy (CSP)** - Prevents XSS by controlling resource loading
- **X-Content-Type-Options** - Prevents MIME sniffing attacks
- **X-Frame-Options** - Prevents clickjacking attacks
- **Strict-Transport-Security (HSTS)** - Enforces HTTPS in production
- **Referrer-Policy** - Controls referrer information leakage
- **Permissions-Policy** - Restricts browser features (camera, mic, geolocation)

**Headers Applied:**
```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-xxx' https://cdn.jsdelivr.net; ...
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()...
```

**Integration:**
```python
from utils.security_headers import init_security_headers

# In app initialization
init_security_headers(app)
```

**Impact:** Comprehensive browser-level security against multiple attack vectors.

---

### 5. **Health Check & Monitoring**

**Files Created:**
- `blueprints/system/health.py`

**Endpoints Added:**

#### `/health/` - Basic Health Check
```json
{
  "status": "healthy",
  "timestamp": "2025-11-02T10:30:00",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "cache": {"status": "healthy"}
  }
}
```
Returns **200** if healthy, **503** if critical components down.

#### `/health/detailed` - Detailed Diagnostics
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "cache": {"status": "healthy"},
    "disk": {"status": "healthy", "percent_used": 45.2, "free_gb": 125.3},
    "memory": {"status": "healthy", "percent_used": 62.1, "available_gb": 3.8},
    "openai": {"status": "configured"}
  },
  "system": {
    "cpu_count": 4,
    "cpu_percent": 23.5,
    "python_version": "3.11.0"
  }
}
```

#### `/health/ready` - Kubernetes Readiness Probe
Returns **200** when ready to accept traffic.

#### `/health/live` - Kubernetes Liveness Probe
Returns **200** if application is alive.

#### `/health/metrics` - Prometheus Metrics
```
# HELP pittstate_users_total Total number of users
# TYPE pittstate_users_total gauge
pittstate_users_total 1247

# HELP pittstate_disk_usage_percent Disk usage percentage
# TYPE pittstate_disk_usage_percent gauge
pittstate_disk_usage_percent 45.2
```

**Impact:** Production-ready monitoring for DevOps, alerts, and debugging.

---

## 📊 **Security Posture Summary**

| Feature | Before | After | Impact |
|---------|--------|-------|--------|
| **XSS Protection** | ⚠️ Basic (Jinja2 escaping) | ✅ Enhanced (Input sanitization) | **High** |
| **File Upload Security** | ⚠️ Basic (secure_filename) | ✅ Comprehensive (type + size validation) | **High** |
| **Security Headers** | ⚠️ Partial | ✅ Complete (CSP, HSTS, etc.) | **Critical** |
| **Input Validation** | ⚠️ Ad-hoc | ✅ Centralized utilities | **Medium** |
| **Health Monitoring** | ❌ None | ✅ Multiple endpoints | **Medium** |

---

## 🚀 **Usage Guidelines**

### For Developers

#### 1. Always Sanitize User Input
```python
from utils.input_validation import sanitize_html

# For text with basic HTML
essay = sanitize_html(request.form.get('essay'), level='basic')

# For rich text (blog posts, etc.)
content = sanitize_html(request.form.get('content'), level='rich')

# Strip all HTML
plain_text = sanitize_html(user_input, level='none')
```

#### 2. Validate File Uploads
```python
from utils.input_validation import sanitize_filename

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if file and file.filename:
    if not allowed_file(file.filename):
        flash("Invalid file type", "danger")
        return redirect(request.url)
    
    if not check_file_size(file):
        flash("File too large", "danger")
        return redirect(request.url)
    
    filename = sanitize_filename(secure_filename(file.filename))
```

#### 3. Validate Numbers and Emails
```python
from utils.input_validation import validate_integer, validate_email

# Integer with range
age = validate_integer(request.form.get('age'), min_val=18, max_val=120)
if age is None:
    abort(400, "Invalid age")

# Email validation
if not validate_email(email):
    flash("Invalid email format", "danger")
```

#### 4. Use Security Headers (Automatic)
Security headers are automatically applied by the middleware. No code changes needed in routes.

#### 5. Monitor System Health
```bash
# Check if service is healthy
curl https://your-domain.com/health/

# Get detailed metrics
curl https://your-domain.com/health/detailed

# Kubernetes probes
readinessProbe:
  httpGet:
    path: /health/ready
    port: 5000

livenessProbe:
  httpGet:
    path: /health/live
    port: 5000
```

---

## 🔐 **Security Checklist**

Use this checklist when adding new features:

- [ ] **User Input**: All user inputs are sanitized using `sanitize_html()` or validated
- [ ] **File Uploads**: File type, size, and name are validated
- [ ] **Database Queries**: Using SQLAlchemy ORM (no raw SQL)
- [ ] **URLs**: External URLs validated with `validate_url()`
- [ ] **Redirects**: Using `safe_redirect_url()` to prevent open redirects
- [ ] **Numbers**: Using `validate_integer()` / `validate_float()` instead of `int()` / `float()`
- [ ] **Emails**: Validated with `validate_email()`
- [ ] **Rate Limiting**: Applied with `@limiter.limit()` decorator
- [ ] **Authentication**: Protected with `@login_required` decorator
- [ ] **Authorization**: Role checks with `@admin_required` or manual verification
- [ ] **CSRF**: Forms include CSRF token (automatic with Flask-WTF)

---

## 📚 **Additional Resources**

### OWASP Top 10 (2021)
1. ✅ **A01: Broken Access Control** - Role-based access + login_required
2. ✅ **A02: Cryptographic Failures** - HTTPS, bcrypt, secure cookies
3. ✅ **A03: Injection** - SQLAlchemy ORM, input validation
4. ✅ **A04: Insecure Design** - Security headers, CSP
5. ✅ **A05: Security Misconfiguration** - Environment-based config
6. ✅ **A06: Vulnerable Components** - Regular dependency updates
7. ✅ **A07: Authentication Failures** - Flask-Login, 2FA support
8. ✅ **A08: Software/Data Integrity** - CSRF tokens, secure file uploads
9. ✅ **A09: Logging Failures** - Comprehensive audit logging
10. ✅ **A10: Server-Side Request Forgery** - URL validation

### Security Testing
```bash
# Run security audit on dependencies
pip install safety
safety check

# Check for known vulnerabilities
pip install bandit
bandit -r blueprints/ utils/

# Test file upload security
curl -X POST -F "documents=@malicious.exe" http://localhost:5000/scholarships/apply/1
# Should reject with "File type not allowed"
```

---

## 🎯 **Next Steps (Optional Future Enhancements)**

1. **Web Application Firewall (WAF)** - Cloudflare, AWS WAF
2. **Penetration Testing** - Regular security audits
3. **Bug Bounty Program** - HackerOne, Bugcrowd
4. **Security Automation** - GitHub Dependabot, Snyk
5. **Secrets Management** - HashiCorp Vault, AWS Secrets Manager
6. **API Rate Limiting per User** - Track per API key, not just IP
7. **Advanced Threat Detection** - Integrate with SIEM tools
8. **Compliance Certifications** - SOC 2, ISO 27001

---

## 📞 **Security Contact**

For security issues or vulnerabilities, please contact:
- **Email**: security@pittstate.edu
- **Responsible Disclosure**: Report privately before public disclosure

---

**Last Updated**: November 2, 2025  
**Version**: 1.0  
**Status**: ✅ All enhancements implemented and tested
