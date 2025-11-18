#!/bin/bash

# NewsCatcher Quick Start Script
# This script helps you set up and start NewsCatcher

set -e

echo "======================================"
echo "   NewsCatcher Setup & Start Script"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: You need to add your OpenAI API key!"
        echo ""
        echo "1. Get your API key from: https://platform.openai.com/api-keys"
        echo "2. Edit the .env file and replace 'your_openai_api_key_here' with your actual key"
        echo ""
        read -p "Press Enter after you've added your API key..."
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

# Verify OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo ""
    echo "❌ OpenAI API key not set in .env file!"
    echo "Please edit .env and add your API key, then run this script again."
    exit 1
fi

echo "✅ Environment configuration found"
echo ""

# Build images
echo "🔨 Building Docker images..."
echo "This may take a few minutes on first run..."
echo ""
docker compose build

echo ""
echo "✅ Images built successfully"
echo ""

# Start services
echo "🚀 Starting services..."

# Try to start services
if ! docker compose up -d 2>&1 | tee /tmp/docker-start.log; then
    echo ""
    echo "❌ Failed to start services!"
    
    # Check if it's a credentials error
    if grep -q "error getting credentials" /tmp/docker-start.log; then
        echo ""
        echo "🔧 Docker credentials issue detected!"
        echo ""
        echo "This is a common macOS Docker Desktop issue."
        echo ""
        echo "Quick Fix: Run this command:"
        echo ""
        echo "  ./fix-docker-credentials.sh"
        echo ""
        echo "Then run ./start.sh again"
        echo ""
        exit 1
    fi
    
    echo "Please check the logs above for details."
    exit 1
fi

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "======================================"
echo "   ✅ NewsCatcher is Ready!"
echo "======================================"
echo ""
echo "🌐 Access the application:"
echo ""
echo "   Frontend (UI):    http://localhost:8501"
echo "   Backend (API):    http://localhost:8000"
echo "   API Docs:         http://localhost:8000/docs"
echo ""
echo "📖 Next Steps:"
echo ""
echo "   1. Open http://localhost:8501 in your browser"
echo "   2. Go to 'Manage URLs' tab and add a website"
echo "   3. Go to 'Manage Criteria' tab and create search criteria"
echo "   4. Click the 'UPDATE' button in the sidebar to start scraping"
echo "   5. View discovered articles in the 'News Feed' tab"
echo ""
echo "📝 Useful Commands:"
echo ""
echo "   View logs:         docker-compose logs -f"
echo "   Stop services:     docker-compose down"
echo "   Restart:           docker-compose restart"
echo "   Run tests:         docker-compose exec backend pytest"
echo ""
echo "📚 Documentation:"
echo ""
echo "   README.md         - Full documentation"
echo "   SETUP.md          - Detailed setup guide"
echo "   ARCHITECTURE.md   - Technical architecture"
echo ""
echo "======================================"

