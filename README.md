# HireIQ SaaS Platform

A comprehensive AI-powered interview platform with a modern SaaS layer built on top of the original AI Interview Agent.

## 🚀 Architecture Overview

HireIQ consists of three main components:

1. **FastAPI Backend** - RESTful API with PostgreSQL database for tenant management
2. **Celery Workers** - Background task processing for emails, ranking, and reports
3. **React Frontends** - Separate HR Dashboard and Candidate Portal applications

### Technology Stack

- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL 16
- **Authentication**: JWT tokens with bcrypt password hashing
- **Task Queue**: Celery with Redis 7 broker
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Database**: MongoDB (AI engine) + PostgreSQL (SaaS layer)
- **Original AI Engine**: Preserved Streamlit-based interview agent

## 📁 Project Structure

```
hireiq-saas/
├── gateway/              # FastAPI application entry point
├── saas/                 # SaaS business logic
│   ├── auth/            # Authentication & authorization
│   ├── companies/       # Company management
│   ├── jobs/            # Job posting management
│   ├── candidates/      # Candidate interview flow
│   ├── dashboard/       # Analytics endpoints
│   └── middleware/      # Tenant isolation & rate limiting
├── database/
│   ├── postgres.py      # PostgreSQL connection & ORM base
│   ├── pg_models/       # SQLAlchemy models (Company, User, Job, Candidate)
│   └── migrations/      # Alembic database migrations
├── workers/
│   ├── celery_app.py    # Celery configuration
│   └── tasks/           # Background tasks (email, ranking, reports)
├── frontend/
│   ├── hr-dashboard/    # HR web application (port 5173)
│   └── candidate-portal/# Candidate interview interface (port 5174)
├── modules/             # Original AI interview engine (FROZEN - never modified)
└── docker-compose.yml   # Full stack orchestration
```

## 🛠️ Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+

### Running with Docker (Recommended)

```bash
# Start all services (PostgreSQL, Redis, MongoDB, API, Workers)
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Check service health
curl http://localhost:8000/health
```

**Note**: The legacy Streamlit app is available via Docker profile:
```bash
docker compose --profile legacy up -d
```

### Local Development

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start API server
uvicorn gateway.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info
```

#### Frontend Setup

```bash
# HR Dashboard
cd frontend/hr-dashboard
npm install
npm run dev  # Runs on http://localhost:5173

# Candidate Portal (separate terminal)
cd frontend/candidate-portal
npm install
npm run dev  # Runs on http://localhost:5174
```

## 🔑 Environment Variables

Copy `.env.example` to `.env` and configure:

### Database
- `POSTGRES_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string  
- `MONGO_URI` - MongoDB connection string

### Authentication
- `JWT_SECRET_KEY` - Secret key for JWT signing (generate random 256-bit string)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token lifetime
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token lifetime

### Email Configuration
- `MAIL_USERNAME`, `MAIL_PASSWORD` - SMTP credentials
- `MAIL_FROM`, `MAIL_SERVER`, `MAIL_PORT` - SMTP settings

### Application URLs
- `CANDIDATE_PORTAL_BASE_URL` - Candidate portal URL
- `HR_DASHBOARD_BASE_URL` - HR dashboard URL
- `FREE_TIER_INTERVIEW_LIMIT` - Monthly interview limit for free tier

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new company & admin user
- `POST /auth/login` - Login and receive JWT tokens
- `POST /auth/refresh` - Refresh access token

### Companies
- `GET /companies/me` - Get current company info
- `PUT /companies/me` - Update company details

### Jobs
- `POST /jobs/` - Create new job posting
- `GET /jobs/` - List all company jobs
- `GET /jobs/{job_id}` - Get job details
- `PUT /jobs/{job_id}` - Update job
- `DELETE /jobs/{job_id}/archive` - Archive a job
- `POST /jobs/{job_id}/invite` - Send interview invites
- `GET /jobs/{job_id}/candidates` - List candidates for job

### Candidates
- `GET /candidates/{token}/validate` - Validate invite token
- `POST /candidates/{token}/start` - Start interview session
- `GET /candidates/{token}/status` - Get interview status
- `GET /candidates/{token}/report` - Download PDF report

### Analytics
- `GET /analytics/dashboard` - Company-wide statistics
- `GET /analytics/jobs/{job_id}` - Job-specific analytics

Full API documentation available at: `http://localhost:8000/docs`

## 👥 User Roles

- **Admin**: Full access to company settings, jobs, and analytics
- **HR**: Can create jobs, invite candidates, view results
- **Viewer**: Read-only access to dashboard and reports

## 🎯 Key Features

### For HR Teams
- Create and manage job postings with skill requirements
- Invite candidates via email with unique interview links
- View real-time candidate rankings and scores
- Download detailed PDF interview reports
- Analytics dashboard with score distributions

### For Candidates
- Simple one-click interview access via email link
- AI-powered technical interviews with live feedback
- Automatic skill assessment and scoring
- Personal interview report download

### Platform Features
- Multi-tenant architecture with data isolation
- Rate limiting (100 requests/minute per IP)
- Quota management by subscription tier
- Background email sending with retry logic
- Automatic candidate ranking after completion

## 🧪 Testing

```bash
# Run test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gateway --cov=saas --cov=workers
```

## 📦 Deployment

### Render.com

The project includes `render.yaml` for one-click deployment:

```bash
# Push to GitHub first
git push origin feature/saas-foundation

# Connect repository in Render dashboard
# Set environment variables
# Deploy automatically
```

### Manual Deployment

1. Set up PostgreSQL 16 and Redis 7 instances
2. Configure environment variables
3. Run `alembic upgrade head`
4. Deploy FastAPI app: `uvicorn gateway.main:app --host 0.0.0.0 --port 8000`
5. Deploy Celery worker: `celery -A workers.celery_app worker`
6. Build and serve frontends as static sites

## 🔒 Security

- Passwords hashed with bcrypt
- JWT tokens with configurable expiration
- Role-based access control (RBAC)
- Tenant isolation prevents cross-company data access
- Rate limiting prevents abuse
- CORS configured for specific origins only

## 📊 Database Schema

### PostgreSQL Tables
- `companies` - Tenant organizations
- `users` - HR users within companies
- `jobs` - Job postings
- `candidates` - Interview candidates

### MongoDB Collections
- Interview sessions (managed by original AI engine)
- Skill graphs and assessment data
- Generated reports

## 🔄 Migration from Legacy

The original Streamlit AI Interview Agent remains fully functional:
- All `modules/` code is preserved and untouched
- MongoDB schema unchanged
- Existing interviews continue to work

The new SaaS layer adds:
- Multi-tenant company management
- User authentication and authorization
- Job posting and candidate tracking
- Professional HR dashboard
- Scalable background processing

## 📝 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Support

For issues and questions:
- API Documentation: `http://localhost:8000/docs`
- GitHub Issues: [Create an issue](https://github.com/ujjawalranjan09/hireiq-saas/issues)
