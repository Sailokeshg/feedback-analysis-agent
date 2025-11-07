#!/bin/bash

# 🚀 Universal Deployment Script for Feedback Analysis Agent
# Supports Fly.io, Railway, and Render deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if required tools are installed
check_dependencies() {
    print_info "Checking dependencies..."

    if [[ "$PLATFORM" == "fly" ]]; then
        if ! command -v fly &> /dev/null; then
            print_error "Fly CLI not found. Install from: https://fly.io/docs/getting-started/installing-flyctl/"
            exit 1
        fi
    elif [[ "$PLATFORM" == "railway" ]]; then
        if ! command -v railway &> /dev/null; then
            print_warning "Railway CLI not found. Installing..."
            npm install -g @railway/cli
        fi
    fi

    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL not found. Please install it."
        exit 1
    fi

    print_success "Dependencies OK"
}

# Generate secure secrets
generate_secrets() {
    print_info "Generating secure secrets..."

    JWT_SECRET=$(openssl rand -hex 32)
    ADMIN_PASS="admin123"  # Change in production
    VIEWER_PASS="viewer123"  # Change in production

    print_success "Secrets generated"
}

# Fly.io deployment
deploy_fly() {
    print_info "Deploying to Fly.io..."

    # Create apps
    print_info "Creating Fly apps..."
    fly launch --name "$APP_NAME-api" --region lax --no-deploy
    fly postgres create --name "$APP_NAME-db" --region lax

    # Get database URL
    DB_URL=$(fly postgres connect --app "$APP_NAME-db" --quiet)

    # Set secrets
    print_info "Setting environment variables..."
    fly secrets set DATABASE_URL="$DB_URL" --app "$APP_NAME-api"
    fly secrets set REDIS_URL="$REDIS_URL" --app "$APP_NAME-api"
    fly secrets set SECURITY_SECRET_KEY="$JWT_SECRET" --app "$APP_NAME-api"
    fly secrets set API_HOST="0.0.0.0" --app "$APP_NAME-api"
    fly secrets set API_PORT="8080" --app "$APP_NAME-api"
    fly secrets set SECURITY_ADMIN_USERNAME="admin" --app "$APP_NAME-api"
    fly secrets set SECURITY_ADMIN_PASSWORD="$ADMIN_PASS" --app "$APP_NAME-api"
    fly secrets set SECURITY_VIEWER_USERNAME="viewer" --app "$APP_NAME-api"
    fly secrets set SECURITY_VIEWER_PASSWORD="$VIEWER_PASS" --app "$APP_NAME-api"

    # Copy fly.toml
    cp deploy/fly/fly.toml .

    # Deploy
    print_info "Deploying API..."
    fly deploy --app "$APP_NAME-api"

    # Attach database
    fly postgres attach "$APP_NAME-db" --app "$APP_NAME-api"

    # Deploy frontend
    print_info "Deploying frontend..."
    fly launch --name "$APP_NAME-web" --region lax --no-deploy
    cp deploy/fly/fly-frontend.toml fly.toml
    fly deploy --app "$APP_NAME-web"

    print_success "Fly.io deployment complete!"
    print_info "API: https://$APP_NAME-api.fly.dev"
    print_info "Frontend: https://$APP_NAME-web.fly.dev"
}

# Railway deployment
deploy_railway() {
    print_info "Deploying to Railway..."

    # Initialize project
    railway init "$APP_NAME"
    cd "$APP_NAME"

    # Add services
    railway add postgresql

    # Set environment variables
    print_info "Setting environment variables..."
    railway variables set DATABASE_URL="\$(railway variables get DATABASE_URL)"
    railway variables set REDIS_URL="$REDIS_URL"
    railway variables set CHROMA_URL="http://localhost:8000"
    railway variables set SECURITY_SECRET_KEY="$JWT_SECRET"
    railway variables set API_HOST="0.0.0.0"
    railway variables set API_PORT="8080"
    railway variables set SECURITY_ADMIN_USERNAME="admin"
    railway variables set SECURITY_ADMIN_PASSWORD="$ADMIN_PASS"
    railway variables set SECURITY_VIEWER_USERNAME="viewer"
    railway variables set SECURITY_VIEWER_PASSWORD="$VIEWER_PASS"

    # Deploy
    print_info "Deploying..."
    railway up --detach

    # Add frontend service
    railway service add --name frontend

    print_success "Railway deployment complete!"
    print_info "Check Railway dashboard for URLs"
}

# Render deployment
deploy_render() {
    print_info "Deploying to Render..."
    print_warning "Render deployment requires manual setup via dashboard"
    print_info "Follow the steps in deploy/render/README.md"
    print_info "Repository: $REPO_URL"
}

# Main deployment function
main() {
    echo "🚀 Feedback Analysis Agent Deployment"
    echo "===================================="

    # Get user input
    read -p "Enter platform (fly/railway/render): " PLATFORM
    read -p "Enter app name (e.g., feedback-agent): " APP_NAME
    read -p "Enter Redis URL (from Upstash): " REDIS_URL
    read -p "Enter GitHub repo URL (for Render): " REPO_URL

    # Validate platform
    if [[ "$PLATFORM" != "fly" && "$PLATFORM" != "railway" && "$PLATFORM" != "render" ]]; then
        print_error "Invalid platform. Choose: fly, railway, or render"
        exit 1
    fi

    # Check dependencies
    check_dependencies

    # Generate secrets
    generate_secrets

    # Deploy based on platform
    case $PLATFORM in
        fly)
            deploy_fly
            ;;
        railway)
            deploy_railway
            ;;
        render)
            deploy_render
            ;;
    esac

    # Post-deployment instructions
    echo ""
    print_success "Deployment complete!"
    echo ""
    print_info "Next steps:"
    echo "1. Run database migrations (check platform-specific docs)"
    echo "2. Access admin panel: admin / $ADMIN_PASS"
    echo "3. Access viewer panel: viewer / $VIEWER_PASS"
    echo "4. Update CORS settings for your frontend URL"
    echo ""
    print_warning "Remember to change default passwords in production!"
}

# Run main function
main "$@"
