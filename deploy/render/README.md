# 🚀 Deploy to Render (Free Tier)

Deploy the Feedback Analysis Agent to Render using their free tier with managed Postgres.

## 📋 Prerequisites

- [Render account](https://render.com/) (free)
- GitHub repository (for deployment)

## 💰 Cost Notes

- **Free**: 750 hours/month (~31 days), then $7/month for persistent apps
- **Postgres**: Free managed Postgres (256MB RAM, 1GB disk)
- **Redis**: Use Upstash free tier
- **Static Sites**: Free unlimited bandwidth
- **Paid**: $7/month for web services, $7/month for Postgres

## 🏗️ Architecture

- **API + Worker**: Render Web Service (free tier)
- **Postgres**: Render managed (free)
- **Redis**: Upstash free tier
- **ChromaDB**: Embedded in app
- **Frontend**: Render Static Site (free)

## 🚀 Step-by-Step Deployment

### 1. Push Code to GitHub

```bash
# Create GitHub repository
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/feedback-agent.git
git push -u origin main
```

### 2. Create Render Services

#### Create Postgres Database

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "PostgreSQL"
3. Name: `feedback-agent-db`
4. Region: Oregon (or closest)
5. Click "Create Database"

#### Create Redis (Upstash)

1. Sign up for [Upstash](https://console.upstash.com/) (free tier)
2. Create Redis database
3. Copy the connection URL

### 3. Deploy Backend API

1. In Render Dashboard: "New" → "Web Service"
2. Connect GitHub repository
3. Configure service:
   ```
   Name: feedback-agent-api
   Environment: Docker
   Dockerfile Path: ./infra/Dockerfile.server
   Branch: main
   ```
4. Environment variables:
   ```
   DATABASE_URL=postgresql://... (from Postgres service)
   REDIS_URL=redis://... (from Upstash)
   CHROMA_URL=http://localhost:8000
   SECURITY_SECRET_KEY=your-secret-key-here
   API_HOST=0.0.0.0
   API_PORT=10000
   SECURITY_ADMIN_USERNAME=admin
   SECURITY_ADMIN_PASSWORD=admin123
   SECURITY_VIEWER_USERNAME=viewer
   SECURITY_VIEWER_PASSWORD=viewer123
   ```
5. Advanced settings:
   ```
   Health Check Path: /health
   ```

### 4. Deploy Frontend

1. In Render Dashboard: "New" → "Static Site"
2. Connect same GitHub repository
3. Configure service:
   ```
   Name: feedback-agent-web
   Build Command: npm ci && npm run build --workspace=client
   Publish Directory: client/dist
   Branch: main
   ```
4. Environment variables:
   ```
   API_URL=https://feedback-agent-api.onrender.com
   ```

### 5. Run Database Migrations

```bash
# Connect to database via Render dashboard
# Or use psql directly
psql $DATABASE_URL

# Run migrations (from local machine or SSH)
cd server
alembic upgrade head

# Seed data (optional)
python scripts/seed_database.py
```

### 6. Configure Custom Domain (Optional)

In each service settings:
- Go to "Settings" → "Custom Domain"
- Add your domain or use Render subdomain

## 🔧 Environment Matrix

| Component | Render Service | Environment Variables |
|-----------|----------------|----------------------|
| API Server | Web Service | `DATABASE_URL`, `REDIS_URL`, `SECURITY_*` |
| Database | PostgreSQL | Auto-configured |
| Frontend | Static Site | `API_URL` |
| Worker | Same as API | Same as API |

## 📊 Monitoring

```bash
# View logs in Render dashboard
# Check service status
# Monitor resource usage
```

## 🔄 Updates

Automatic deployments on git push to main branch.

## 🚨 Troubleshooting

**Build failures:**
- Check Render build logs
- Ensure Dockerfile is correct
- Verify environment variables

**Database connection:**
- Check DATABASE_URL format in Render dashboard
- Verify Postgres service is running
- Run migrations manually

**Free tier limits:**
- 750 hours/month (~31 days at 100% uptime)
- After limit: $7/month for persistent service

## 📈 Scaling (Paid Tier)

1. Upgrade web service to $7/month plan
2. Upgrade Postgres to $7/month plan
3. Add Redis via Upstash paid tier

## 🌐 URLs

After deployment:
- **Frontend**: `https://feedback-agent-web.onrender.com`
- **API**: `https://feedback-agent-api.onrender.com`
- **API Docs**: `https://feedback-agent-api.onrender.com/docs`

## 🔗 Render Features

- **Auto-deploy**: On git push
- **Free SSL**: Automatic HTTPS
- **CDN**: Global CDN for static sites
- **Monitoring**: Built-in logs and metrics
- **Backups**: Automatic database backups

## 🚀 Quick Deploy (Alternative)

Use Render's Blueprints (if supported):

```yaml
# render.yaml
services:
  - type: web
    name: feedback-agent-api
    dockerfile: infra/Dockerfile.server
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: feedback-agent-db
          property: connectionString
      - key: REDIS_URL
        value: redis://...

  - type: pserv
    name: feedback-agent-db
    ipAllowList: []

  - type: web
    name: feedback-agent-web
    staticSite:
      buildCommand: npm ci && npm run build --workspace=client
      publishDir: client/dist
```

Then run: `render deploy`
