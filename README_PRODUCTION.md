# 🦍 PittState-Connect - Production-Grade Platform

**Official platform connecting the Pittsburg State University community**

[![CI/CD Pipeline](https://github.com/Cade-Cowdrey/Gorilla-Link/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Cade-Cowdrey/Gorilla-Link/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

## 🌟 Features

### Core Platform
- **Flask 3.0** web framework with modular Blueprint architecture
- **PostgreSQL** database with SQLAlchemy ORM
- **Redis** caching and message broker
- **Celery** async task queue
- **PWA** support with offline caching
- **WebSocket** real-time updates
- **RESTful API** with GraphQL support

### 🎓 Scholarship Hub Phase 2
- AI-powered smart matching
- Deadline tracking & reminders
- Essay library with AI assistance
- Progress tracking dashboard
- Financial literacy modules
- Donor portal & impact stories
- Faculty recommendation uploads

### 📊 Advanced Analytics
- Real-time admin dashboards
- Department scorecards
- Employer analytics portal
- University-wide metrics
- AI-generated insights
- Predictive analytics (churn, success)
- CSV/PDF exports
- Sentiment analysis

### 🤖 AI & Automation
- **GorillaGPT** - AI chat assistant
- Resume/essay builder
- Auto-tagging & categorization
- Smart scholarship matching
- Predictive success models
- Adaptive notifications

### 💬 Communication Suite
- Unified inbox (messages/email/alerts)
- Calendar sync (Google/Outlook/iCal)
- Department announcements
- Community forums
- Webinar hub with registration
- Push notifications (web/mobile/SMS)

### 🔐 Security & Compliance
- Two-factor authentication (TOTP)
- WebAuthn/FIDO2 support
- Encrypted secrets vault
- Comprehensive audit logs
- FERPA/GDPR consent management
- Role-based access control (RBAC)
- Message encryption

### 🌍 Integrations
- Canvas/Moodle/Banner LMS
- LinkedIn & Handshake
- Google & Microsoft SSO
- Stripe payments
- Twilio SMS/voice
- Salesforce/Raiser's Edge
- Firebase push notifications

### 💼 Alumni & Employer Engagement
- Alumni mentor directory
- Mentorship session scheduling
- Employer analytics portal
- Corporate sponsorship tiers
- Donor wall & recognition
- Premium analytics monetization

### 📱 Mobile & On-Site
- QR code check-ins
- Kiosk mode
- Geofenced events
- Offline mode support
- Progressive Web App

### 🔮 Future Vision
- AR Campus Explorer
- Voice Assistant "Hey Gorilla"
- Blockchain credentials
- Global impact map
- Digital twin dashboard

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend assets)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/Cade-Cowdrey/Gorilla-Link.git
cd Gorilla-Link
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
flask db upgrade
python seed_data.py
```

6. **Run development server**
```bash
python app_pro.py
```

Visit `http://localhost:5000`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f web

# Run migrations
docker-compose exec web flask db upgrade
```

## 📦 Production Deployment

### Render.com (Recommended)

1. **Connect GitHub repository** to Render

2. **Create services:**
   - Web Service (Flask app)
   - PostgreSQL database
   - Redis instance
   - Celery worker
   - Celery beat scheduler

3. **Set environment variables** in Render dashboard

4. **Deploy:** Automatic from `main` branch

### Manual Deployment

```bash
# Build Docker image
docker build -t pittstate-connect .

# Run with production settings
docker run -p 5000:5000 \
  -e DATABASE_URL=$DATABASE_URL \
  -e REDIS_URL=$REDIS_URL \
  -e SECRET_KEY=$SECRET_KEY \
  pittstate-connect
```

## 🛠️ Configuration

### Environment Variables

```bash
# App
APP_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
MAIL_USE_TLS=True

# AI (OpenAI)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Payments (Stripe)
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890

# Integrations
CANVAS_URL=https://canvas.pittstate.edu
GOOGLE_CLIENT_ID=xxx
MICROSOFT_CLIENT_ID=xxx

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
```

## 📖 API Documentation

### Authentication

All API endpoints require authentication unless specified.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Endpoints

#### Health Check
```http
GET /api/v1/health
```

#### AI Chat
```http
POST /api/v1/ai/chat
{
  "message": "How can I find scholarships?",
  "session_id": "optional-session-id"
}
```

#### Enable 2FA
```http
POST /api/v1/security/2fa/enable
```

#### Get Analytics Dashboard
```http
GET /api/v1/analytics/dashboard?days=30
```

#### Send Message
```http
POST /api/v1/messages/send
{
  "recipient_id": 123,
  "subject": "Hello",
  "body": "Message content"
}
```

Full API documentation available at `/api/docs` (when running).

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_ai_service.py

# Run linting
flake8 .
black --check .

# Security scan
bandit -r .
safety check
```

## 📊 Monitoring

### Prometheus Metrics
- Available at `/metrics`
- Scraped by Prometheus every 15s

### Grafana Dashboards
- Access at `http://localhost:3000` (Docker)
- Default credentials: admin/admin

### Health Checks
- `/health` - Overall health
- `/api/v1/status` - Detailed status (admin only)

## 🔒 Security

### Best Practices
- All secrets stored in environment variables
- Passwords hashed with bcrypt
- HTTPS enforced in production
- CORS configured appropriately
- Rate limiting enabled
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF tokens

### Compliance
- **FERPA** - Educational records privacy
- **GDPR** - User consent management
- **SOC 2 Type II** - Security controls
- **Audit trails** - Comprehensive logging

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Standards
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Run linters before committing

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 👥 Team

- **Cade Cowdrey** - Project Lead & Developer
- **Pittsburg State University** - Partner Institution

## 📧 Support

- **Email:** support@pittstate-connect.edu
- **Documentation:** https://docs.pittstate-connect.edu
- **Issues:** https://github.com/Cade-Cowdrey/Gorilla-Link/issues

## 🙏 Acknowledgments

- Pittsburg State University
- All contributors and testers
- Open source community

---

**Go Gorillas! 🦍**

*Built with ❤️ for the PSU community*
