#!/bin/bash
# Quick deployment script for automatic training
# Run this on your Google Cloud VM after initial deployment

echo "=========================================="
echo "🚀 MindLift Auto-Training Quick Setup"
echo "=========================================="

# Check if running as mindlift user
if [ "$USER" != "mindlift" ]; then
    echo "⚠️  Please run as mindlift user"
    echo "Run: sudo su - mindlift"
    echo "Then: bash /home/mindlift/mindlift/scripts/quick_setup.sh"
    exit 1
fi

PROJECT_DIR="/home/mindlift/mindlift"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
WEBAPP_DIR="$PROJECT_DIR/webapp"
VENV_DIR="$PROJECT_DIR/venv"

# Verify project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$PROJECT_DIR/logs"

# Check if setup_cron.sh exists
if [ ! -f "$SCRIPTS_DIR/setup_cron.sh" ]; then
    echo "⚠️  setup_cron.sh not found in $SCRIPTS_DIR"
    echo ""
    echo "Please upload the scripts from your local machine:"
    echo "  1. scripts/setup_cron.sh"
    echo "  2. scripts/check_training_status.sh"
    echo ""
    echo "Using gcloud:"
    echo "  gcloud compute scp scripts/setup_cron.sh $(hostname):/home/mindlift/mindlift/scripts/"
    echo "  gcloud compute scp scripts/check_training_status.sh $(hostname):/home/mindlift/mindlift/scripts/"
    echo ""
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$SCRIPTS_DIR"/*.sh

# Run the setup
echo ""
echo "Running automatic training setup..."
bash "$SCRIPTS_DIR/setup_cron.sh"

# Show next steps
echo ""
echo "=========================================="
echo "✅ Quick Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check status: bash $SCRIPTS_DIR/check_training_status.sh"
echo "  2. View logs: tail -f $PROJECT_DIR/logs/auto_training.log"
echo "  3. Manual training: cd $WEBAPP_DIR && source $VENV_DIR/bin/activate && python manage.py auto_train_models"
echo ""
