# 🚀 Deploy to Railway (Free Tier)

Deploy the Feedback Analysis Agent to Railway using their free tier with managed Postgres.

## 📋 Prerequisites

- [Railway account](https://railway.app/) (free)
- Railway CLI (optional but recommended)

## 💰 Cost Notes

- **Free**: 512MB RAM, 1GB disk, 100GB bandwidth/month
- **Postgres**: Free managed Postgres (256MB RAM, 1GB disk)
- **Redis**: Use Upstash free tier ($10/month credit)
- **Paid**: $5/month for 1GB RAM, $10/month for 4GB disk

## 🏗️ Architecture

- **API + Worker**: Single Railway service
- **Postgres**: Railway managed (free)
- **Redis**: Upstash free tier
- **ChromaDB**: Embedded in app
- **Frontend**: Railway static site (free)

## 🚀 Step-by-Step Deployment

### 1. Create Railway Project

```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Login
railway login

# Create project
railway init feedback-agent
cd feedback-agent
```

### 2. Add Services

```bash
# Add Postgres database
railway add postgresql

# Add Redis (optional - use Upstash free instead)
# railway add redis
```

### 3. Deploy Backend

```bash
# Link to existing project or create new
railway link

# Set environment variables
railway variables set DATABASE_URL="$(railway variables get DATABASE_URL)"
railway variables set REDIS_URL="redis://..."  # From Upstash
railway variables set CHROMA_URL="http://localhost:8000"
railway variables set SECURITY_SECRET_KEY="$(openssl rand -hex 32)"
railway variables set API_HOST="0.0.0.0"
railway variables set API_PORT="8080"

# User credentials
railway variables set SECURITY_ADMIN_USERNAME="admin"
railway variables set SECURITY_ADMIN_PASSWORD="admin123"
railway variables set SECURITY_VIEWER_USERNAME="viewer"
railway variables set SECURITY_VIEWER_PASSWORD="viewer123"
```

### 4. Configure Build Settings

In Railway dashboard or via CLI:

```bash
# Set build command
railway up --detach

# Or configure in dashboard:
# Build Command: pip install -e ./server && pip install uvicorn
# Start Command: uvicorn server.app.main:app --host 0.0.0.0 --port $PORT
```

### 5. Add Volume for ChromaDB

```bash
# Add persistent volume for ChromaDB data
railway volume add chroma-data
```

### 6. Deploy Frontend

```bash
# Create new service for frontend
railway service add --name frontend

# Configure frontend service
# Build Command: npm ci && npm run build --workspace=client
# Start Command: npx serve -s client/dist -l $PORT
# Root Directory: /
```

### 7. Run Database Migrations

```bash
# Connect to database
railway connect

# Run migrations
python -m alembic upgrade head

# Seed data (optional)
python server/scripts/seed_database.py
```

### 8. Configure Networking

Railway automatically provides URLs for each service:
- Backend: `https://feedback-agent-production.up.railway.app`
- Frontend: `https://feedback-agent-frontend-production.up.railway.app`

## 🔧 Environment Matrix

| Component | Railway Service | Environment Variables |
|-----------|-----------------|----------------------|
| API Server | `feedback-agent` | `DATABASE_URL`, `REDIS_URL`, `SECURITY_*` |
| Database | Managed Postgres | Auto-configured |
| Frontend | `frontend` | `API_URL` (set to backend URL) |
| Worker | Same as API | Same as API |

## 📊 Monitoring

```bash
# View logs
railway logs

# Check service status
railway status

# View metrics in dashboard
```

## 🔄 Updates

```bash
# Deploy changes
railway up

# Update environment variables
railway variables set NEW_VAR="value"
```

## 🚨 Troubleshooting

**Build failures:**
- Check Railway logs for build errors
- Ensure Dockerfile paths are correct
- Verify environment variables are set

**Database connection:**
- Check DATABASE_URL format
- Verify Postgres service is running
- Run migrations manually if needed

**Memory issues:**
- Free tier: 512MB RAM limit
- Upgrade to paid plan for more resources

## 📈 Scaling (Paid Tier)

```bash
# Upgrade to paid plans
railway service scale --cpu 1 --memory 1024
```

## 🌐 URLs

After deployment:
- **Frontend**: `https://[project]-frontend.up.railway.app`
- **API**: `https://[project].up.railway.app`
- **API Docs**: `https://[project].up.railway.app/docs`

## 🔗 Railway CLI Commands

```bash
# Initialize project
railway init

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Set variables
railway variables set KEY=value

# Connect to database
railway connect
```
