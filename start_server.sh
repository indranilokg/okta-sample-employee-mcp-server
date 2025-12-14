#!/bin/bash

# Standalone MCP Server Startup Script
# This script starts the Okta Employee MCP Server locally

set -e

echo "=========================================="
echo "Okta Sample Employee MCP Server"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp env.template .env
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env and set your Okta configuration:"
    echo "  - OKTA_DOMAIN"
    echo "  - OKTA_AUTHORIZATION_SERVER_ID"
    echo "  - OKTA_AUDIENCE"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "=========================================="
echo "Starting MCP Server..."
echo "=========================================="
echo ""
echo "Server will be available at:"
echo "  - HTTP: http://localhost:8001"
echo "  - Health: http://localhost:8001/health"
echo "  - Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
uvicorn mcp_server.main:app --reload --host 0.0.0.0 --port 8001
