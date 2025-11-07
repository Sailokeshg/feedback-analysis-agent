# 🚀 Deploy to Fly.io (Free Credits)

Deploy the Feedback Analysis Agent to Fly.io using their $5 free credits.

## 📋 Prerequisites

- [Fly.io account](https://fly.io/) (free)
- [Fly CLI](https://fly.io/docs/getting-started/installing-flyctl/)
- Docker installed locally

## 💰 Cost Notes

- **Free**: $5 credits (enough for ~2 small apps)
- **Postgres**: $0.000004/GB-hour (~$3/month for small DB)
- **App**: $0.000004/GB-hour (~$3/month for 512MB RAM)
- **Bandwidth**: Free up to limits

## 🏗️ Architecture

- **API + Worker**: Single Fly app (monolithic deployment)
- **Postgres**: Fly Postgres (managed)
- **Redis**: Upstash Redis (free tier)
- **ChromaDB**: Embedded in app (simplified)

## 🚀 Step-by-Step Deployment

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Verify
fly version
```

### 2. Authenticate

```bash
fly auth login
```

### 3. Create Fly Apps

```bash
# Create the main app
fly launch --name feedback-agent-api --region lax

# Create Postgres database
fly postgres create --name feedback-agent-db --region lax
```

### 4. Set Environment Variables

```bash
# Get database connection string
fly postgres connect --app feedback-agent-db

# Copy the DATABASE_URL and set it
fly secrets set DATABASE_URL="postgresql://..."

# Set other secrets
fly secrets set REDIS_URL="redis://..."  # From Upstash or Redis Labs free tier
fly secrets set SECURITY_SECRET_KEY="$(openssl rand -hex 32)"
fly secrets set API_HOST="0.0.0.0"
fly secrets set API_PORT="8080"

# User credentials (change in production!)
fly secrets set SECURITY_ADMIN_USERNAME="admin"
fly secrets set SECURITY_ADMIN_PASSWORD="admin123"
fly secrets set SECURITY_VIEWER_USERNAME="viewer"
fly secrets set SECURITY_VIEWER_PASSWORD="viewer123"
```

### 5. Configure fly.toml

Update the generated `fly.toml`:

```toml
app = "feedback-agent-api"
primary_region = "lax"

[build]
  dockerfile = "infra/Dockerfile.server"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[mounts]
  source = "chroma_data"
  destination = "/app/chroma_db"

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### 6. Deploy

```bash
# Deploy the API
fly deploy

# Attach to database
fly postgres attach feedback-agent-db --app feedback-agent-api
```

### 7. Run Database Migrations

```bash
# SSH into the running app
fly ssh console

# Run migrations
cd /app && python -m alembic upgrade head

# Seed with sample data (optional)
python server/scripts/seed_database.py
```

### 8. Deploy Frontend

```bash
# Create separate app for frontend
fly launch --name feedback-agent-web --region lax --no-deploy

# Configure for static hosting
```

Update `fly.toml` for frontend:

```toml
app = "feedback-agent-web"
primary_region = "lax"

[build]
  dockerfile = "infra/Dockerfile.client"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

```bash
# Deploy frontend
fly deploy --config fly-frontend.toml
```

## 🔧 Environment Matrix

| Component | Fly.io Config | Environment Variables |
|-----------|---------------|----------------------|
| API Server | `feedback-agent-api` | `DATABASE_URL`, `REDIS_URL`, `SECURITY_*` |
| Database | Fly Postgres | Auto-configured |
| Frontend | `feedback-agent-web` | `API_URL` (set to API app URL) |
| Worker | Same app as API | Same as API |

## 📊 Monitoring

```bash
# Check app status
fly status

# View logs
fly logs

# Check Postgres
fly postgres connect --app feedback-agent-db
```

## 🔄 Updates

```bash
# Deploy changes
fly deploy

# Update secrets
fly secrets set NEW_SECRET="value"
```

## 🚨 Troubleshooting

**App won't start:**
- Check logs: `fly logs`
- Verify environment variables: `fly secrets list`
- Check database connectivity

**Database issues:**
- Run migrations manually via SSH
- Check connection string format

**Memory issues:**
- Increase VM memory in `fly.toml`
- Monitor usage: `fly vm status`

## 📈 Scaling (When Credits Run Out)

```toml
# fly.toml - Paid tier example
[[vm]]
  memory = "1024mb"
  cpu_kind = "shared"
  cpus = 2
```

## 🌐 URLs

After deployment:
- **Frontend**: `https://feedback-agent-web.fly.dev`
- **API**: `https://feedback-agent-api.fly.dev`
- **API Docs**: `https://feedback-agent-api.fly.dev/docs`
