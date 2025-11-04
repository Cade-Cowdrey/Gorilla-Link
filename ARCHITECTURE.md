# PittState-Connect Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Web App     │  Mobile PWA  │  Admin Portal  │  API Clients             │
│  (Students)  │  (Alumni)    │  (Staff)       │  (Integrations)          │
└──────┬───────┴──────┬───────┴──────┬─────────┴──────┬───────────────────┘
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          NGINX REVERSE PROXY                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ SSL/TLS    │  │ Load       │  │ Rate       │  │ Static     │       │
│  │ Termination│  │ Balancing  │  │ Limiting   │  │ Files      │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLASK APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                         BLUEPRINTS                              │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  Auth  │  Profile  │  Scholarships  │  Events  │  Career       │    │
│  │  Admin │  Alumni   │  Employer      │  AI      │  Analytics    │    │
│  │  API   │  Security │  Notifications │  Forums  │  Webinars     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                      SERVICE LAYER                              │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │    │
│  │  │ AI Service    │  │ Security      │  │ Analytics     │      │    │
│  │  │               │  │ Service       │  │ Service       │      │    │
│  │  │ • GorillaGPT  │  │ • 2FA/WebAuth │  │ • Dashboards  │      │    │
│  │  │ • Resume      │  │ • Encryption  │  │ • Predictions │      │    │
│  │  │ • Matching    │  │ • Audit Logs  │  │ • Exports     │      │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │    │
│  │                                                                  │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │    │
│  │  │ Communication │  │ Integration   │  │ Monitoring    │      │    │
│  │  │ Service       │  │ Service       │  │ Service       │      │    │
│  │  │ • Inbox       │  │ • Stripe      │  │ • Prometheus  │      │    │
│  │  │ • Messaging   │  │ • Twilio      │  │ • Health      │      │    │
│  │  │ • Forums      │  │ • Firebase    │  │ • Alerts      │      │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │    │
│  │                                                                  │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │    │
│  │  │ Feature Flag  │  │ Data          │  │ Notification  │      │    │
│  │  │ Service       │  │ Governance    │  │ Hub Service   │      │    │
│  │  │ • Flags       │  │ • Lineage     │  │ • Multi-ch.   │      │    │
│  │  │ • A/B Tests   │  │ • Bias Detect │  │ • Routing     │      │    │
│  │  │ • Rollouts    │  │ • Retention   │  │ • Preferences │      │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │    │
│  │                                                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                      DATA ACCESS LAYER                          │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  SQLAlchemy ORM  │  Flask-Migrate  │  Database Connection Pool │    │
│  └────────────────────────────────────────────────────────────────┘    │
└───────────────────────┬───────────────────────────┬────────────────────┘
                        │                           │
                        ▼                           ▼
┌───────────────────────────────────┐  ┌──────────────────────────────────┐
│       POSTGRESQL DATABASE         │  │      REDIS CACHE/BROKER          │
├───────────────────────────────────┤  ├──────────────────────────────────┤
│                                   │  │  • Session Storage               │
│  Core Tables (50+):               │  │  • Cache Layer                   │
│  • User, Role, Post               │  │  • Celery Broker                 │
│  • Scholarship, Event, Job        │  │  • Rate Limiting                 │
│  • Department, Connection         │  │  • Feature Flag Cache            │
│  • Notification, Message          │  └──────────────────────────────────┘
│                                   │              │
│  Extended Tables (50+):           │              │
│  • TwoFactorAuth, AuditLog        │              ▼
│  • ScholarshipApplication         │  ┌──────────────────────────────────┐
│  • AlumniProfile, MentorSession   │  │    CELERY TASK WORKERS (4x)      │
│  • AIConversation, PredictiveModel│  ├──────────────────────────────────┤
│  • FeatureFlag, ABTest            │  │  Async Tasks:                    │
│  • DataLineage, BiasMonitoring    │  │  • Email sending                 │
│  • EventLog, PaymentTransaction   │  │  • Push notifications            │
│  • MicroCredential, Badge         │  │  • Analytics updates             │
│  • WebinarRegistration, Forum     │  │  • Data cleanup                  │
│                                   │  │  • ML training                   │
│  Indexes, Foreign Keys,           │  │  • Bias monitoring               │
│  JSONB columns for flexibility    │  │                                  │
└───────────────────────────────────┘  └──────────────────────────────────┘
                                                   │
                                                   ▼
                                       ┌──────────────────────────────────┐
                                       │   CELERY BEAT SCHEDULER          │
                                       ├──────────────────────────────────┤
                                       │  Scheduled Jobs (11 total):      │
                                       │  00:05 - Daily analytics         │
                                       │  01:00 - Retention policies      │
                                       │  02:00 - Data cleanup (Sun)      │
                                       │  03:00 - ML training (Sat)       │
                                       │  04:00 - Bias monitoring         │
                                       │  05:00 - Data quality scan       │
                                       │  08:00 - Weekly report (Mon)     │
                                       │  09:00 - Deadline reminders      │
                                       │  18:00 - Notification digests    │
                                       │  Every 6h - External sync        │
                                       └──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  OpenAI      │  Stripe      │  Twilio     │  Firebase   │  Canvas LMS   │
│  (AI)        │  (Payments)  │  (SMS)      │  (Push)     │  (Courses)    │
│                                                                           │
│  LinkedIn    │  Handshake   │  Google     │  Microsoft  │  Salesforce   │
│  (Profiles)  │  (Jobs)      │  (Cal/SSO)  │  (Cal/SSO)  │  (CRM)        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ Prometheus   │  │ Grafana      │  │ Sentry       │  │ CloudWatch  ││
│  │              │  │              │  │              │  │             ││
│  │ • Metrics    │  │ • Dashboards │  │ • Errors     │  │ • Logs      ││
│  │ • Alerts     │  │ • Graphs     │  │ • Performance│  │ • Traces    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  GitHub → Actions → [Lint → Test → Build → Security Scan] → Deploy      │
│                                                                           │
│  Environments: Staging → Production (with approval gates)                │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### 1. User Applies to Scholarship
```
User → Flask Route → Service Layer → Database
                         │
                         ├─→ AI Service (match scoring)
                         ├─→ Data Governance (track lineage)
                         ├─→ Notification Hub (send confirmation)
                         └─→ Analytics (update metrics)
```

### 2. Feature Flag Check
```
Request → Feature Flag Service → Cache Check → Database (if miss)
                                      ↓
                              Return enabled/disabled
```

### 3. Bias Detection Flow
```
ML Model Prediction → Data Governance Service
                              ↓
                    Calculate confusion matrix
                              ↓
                    Detect bias across groups
                              ↓
                    Apply 80% rule
                              ↓
                    Alert if bias detected → Notification Hub → Admins
```

### 4. Smart Notification Routing
```
Service calls send() → Notification Hub Service
                              ↓
                    Check user preferences
                              ↓
                    Determine channels (in-app, email, SMS, push)
                              ↓
        ┌───────────┬─────────┼─────────┬──────────┐
        ▼           ▼         ▼         ▼          ▼
    In-App      Email     SMS       Push       (skipped if disabled)
    (sync)    (Celery)  (Twilio) (Firebase)
```

## Security Layers

```
┌─────────────────────────────────────────┐
│ Layer 1: Network Security               │
│ • SSL/TLS encryption                    │
│ • Rate limiting (Flask-Limiter)         │
│ • DDoS protection (Cloudflare)          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Layer 2: Authentication                 │
│ • JWT tokens (Flask-Login)              │
│ • 2FA (TOTP) via Security Service       │
│ • WebAuthn (FIDO2)                      │
│ • SSO (Google, Microsoft)               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Layer 3: Authorization                  │
│ • Role-based access (admin_required)    │
│ • API key validation                    │
│ • Per-resource permissions              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Layer 4: Data Security                  │
│ • Encryption at rest (Fernet)           │
│ • SQL injection prevention (ORM)        │
│ • XSS protection (templating)           │
│ • CSRF tokens (Flask-WTF)               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Layer 5: Audit & Compliance             │
│ • Audit logs (all admin actions)        │
│ • Data lineage (FERPA/GDPR)             │
│ • Retention policies                    │
│ • Bias monitoring                       │
└─────────────────────────────────────────┘
```

## Scaling Strategy

### Horizontal Scaling
```
┌─────────────────────────────────────────┐
│        LOAD BALANCER (Nginx)            │
└─────────┬──────────┬──────────┬─────────┘
          │          │          │
    ┌─────▼────┐ ┌──▼─────┐ ┌──▼─────┐
    │ Flask 1  │ │ Flask 2│ │ Flask 3│
    └──────────┘ └────────┘ └────────┘
          │          │          │
          └──────────┴──────────┘
                     │
          ┌──────────▼──────────┐
          │ PostgreSQL (Primary)│
          │   + Read Replicas   │
          └─────────────────────┘
```

### Caching Strategy
```
Request → Check Cache → Hit? → Return from Redis
                    │
                    └─→ Miss → Query DB → Store in Cache → Return
```

### Background Processing
```
Web Request → Quick Response (200 OK)
                    │
                    └─→ Enqueue Celery Task
                              │
                              └─→ Worker processes async
                                    (emails, notifications, analytics)
```

---

*Architecture designed for 10,000+ concurrent users, 1M+ scholarships, enterprise-grade reliability*
