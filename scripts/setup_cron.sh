#!/bin/bash
# Setup automatic model training on Google Cloud VM
# This script configures a cron job to train models automatically

set -e

echo "=========================================="
echo "MindLift - Automatic Training Setup"
echo "=========================================="

# Configuration
PROJECT_DIR="/home/mindlift/mindlift"
VENV_DIR="$PROJECT_DIR/venv"
WEBAPP_DIR="$PROJECT_DIR/webapp"
LOG_DIR="$PROJECT_DIR/logs"
CRON_LOG="$LOG_DIR/auto_training.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory
echo -e "${YELLOW}Creating logs directory...${NC}"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Create the training script
echo -e "${YELLOW}Creating training script...${NC}"
cat > "$PROJECT_DIR/scripts/run_auto_training.sh" << 'EOF'
#!/bin/bash
# Automatic training script - runs via cron

# Load environment
PROJECT_DIR="/home/mindlift/mindlift"
VENV_DIR="$PROJECT_DIR/venv"
WEBAPP_DIR="$PROJECT_DIR/webapp"
LOG_DIR="$PROJECT_DIR/logs"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Change to webapp directory
cd "$WEBAPP_DIR"

# Run training (quiet mode for cron)
python manage.py auto_train_models --quiet --min-messages 50 >> "$LOG_DIR/auto_training.log" 2>&1

# Log completion
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-training check completed" >> "$LOG_DIR/auto_training.log"
EOF

chmod +x "$PROJECT_DIR/scripts/run_auto_training.sh"
echo -e "${GREEN}✅ Training script created${NC}"

# Setup cron job
echo -e "${YELLOW}Setting up cron job...${NC}"

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Remove old MindLift training entries (if any)
sed -i '/MindLift Auto-Training/d' "$TEMP_CRON"
sed -i '/run_auto_training.sh/d' "$TEMP_CRON"

# Add new cron job - runs daily at 3 AM
echo "" >> "$TEMP_CRON"
echo "# MindLift Auto-Training - Runs daily at 3 AM" >> "$TEMP_CRON"
echo "0 3 * * * $PROJECT_DIR/scripts/run_auto_training.sh" >> "$TEMP_CRON"

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo -e "${GREEN}✅ Cron job configured${NC}"

# Display current crontab
echo -e "\n${YELLOW}Current cron schedule:${NC}"
crontab -l | grep -A1 "MindLift"

# Test the training script
echo -e "\n${YELLOW}Testing training script...${NC}"
bash "$PROJECT_DIR/scripts/run_auto_training.sh"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test successful!${NC}"
else
    echo -e "${RED}❌ Test failed - check logs${NC}"
fi

# Display log location
echo -e "\n${YELLOW}Training logs:${NC} $CRON_LOG"
echo -e "${YELLOW}View logs:${NC} tail -f $CRON_LOG"

echo ""
echo "=========================================="
echo "✅ Automatic Training Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  • Training runs daily at 3:00 AM"
echo "  • Minimum 50 messages required"
echo "  • Logs: $CRON_LOG"
echo ""
echo "Manual Commands:"
echo "  • Run now:  cd $WEBAPP_DIR && python manage.py auto_train_models"
echo "  • Check logs: tail -f $CRON_LOG"
echo "  • Edit cron: crontab -e"
echo ""
echo "To change the schedule, run: crontab -e"
echo "Cron format: minute hour day month weekday"
echo "Examples:"
echo "  • Every 6 hours: 0 */6 * * *"
echo "  • Twice daily (3 AM, 3 PM): 0 3,15 * * *"
echo "  • Weekly (Sunday 2 AM): 0 2 * * 0"
echo ""
