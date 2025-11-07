# 🚀 Deployment Guides

This directory contains deployment configurations for multiple cloud platforms using their free tiers.

## Supported Platforms

| Platform | Free Tier | Postgres | Status |
|----------|-----------|----------|---------|
| [Fly.io](./fly/README.md) | $5 credits | Built-in | ✅ Complete |
| [Railway](./railway/README.md) | 512MB RAM, 1GB disk | Managed | ✅ Complete |
| [Render](./render/README.md) | 750h/month | Managed | ✅ Complete |

## Architecture

The application consists of:
- **API Server** (FastAPI) - Main backend
- **Worker** (RQ) - Background job processing
- **Frontend** (React) - User interface
- **Database** - PostgreSQL for data storage
- **Cache** - Redis for caching
- **Vector DB** - ChromaDB for embeddings

## Quick Deploy

Choose your platform and follow the step-by-step guide.

## Environment Variables

All platforms require these environment variables (see each platform's `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://...

# Redis (for caching)
REDIS_URL=redis://...

# Vector Database (ChromaDB)
CHROMA_URL=http://...

# JWT Security
SECURITY_SECRET_KEY=your-secret-key
SECURITY_ADMIN_USERNAME=admin
SECURITY_ADMIN_PASSWORD=admin123
SECURITY_VIEWER_USERNAME=viewer
SECURITY_VIEWER_PASSWORD=viewer123

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Cost Comparison

| Platform | Free Limits | Paid Upgrade |
|----------|-------------|--------------|
| Fly.io | $5 credits (~2 apps) | $1.94/GB RAM/month |
| Railway | 512MB RAM, 1GB disk | $5/month for 1GB RAM |
| Render | 750h/month (~31 days) | $7/month for persistent apps |

## Post-Deployment

After deployment, you can:
1. Access the frontend at the provided URL
2. Use the API at `/docs` for documentation
3. Admin login: `admin` / `admin123`
4. Viewer login: `viewer` / `viewer123`

## Troubleshooting

- Check application logs in each platform's dashboard
- Verify environment variables are set correctly
- Ensure database is accessible from the app
- Check that ports are properly configured
