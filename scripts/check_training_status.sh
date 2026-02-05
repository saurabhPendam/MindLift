#!/bin/bash
# Check status of automatic model training

PROJECT_DIR="/home/mindlift/mindlift"
LOG_DIR="$PROJECT_DIR/logs"
WEBAPP_DIR="$PROJECT_DIR/webapp"
VENV_DIR="$PROJECT_DIR/venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "MindLift - Training Status Check"
echo "=========================================="

# Check if cron job exists
echo -e "\n${YELLOW}📅 Cron Schedule:${NC}"
if crontab -l 2>/dev/null | grep -q "run_auto_training.sh"; then
    crontab -l | grep -A1 "MindLift"
    echo -e "${GREEN}✅ Automatic training is scheduled${NC}"
else
    echo -e "${YELLOW}⚠️  No automatic training scheduled${NC}"
    echo "Run: bash $PROJECT_DIR/scripts/setup_cron.sh"
fi

# Check training logs
echo -e "\n${YELLOW}📋 Recent Training Activity:${NC}"
if [ -f "$LOG_DIR/auto_training.log" ]; then
    echo -e "${BLUE}Last 10 entries:${NC}"
    tail -n 10 "$LOG_DIR/auto_training.log"
else
    echo "No training logs found yet"
fi

# Check model files
echo -e "\n${YELLOW}🤖 Trained Models:${NC}"
MODEL_DIR="$WEBAPP_DIR/ml_models"
if [ -d "$MODEL_DIR" ]; then
    if [ "$(ls -A $MODEL_DIR)" ]; then
        ls -lh "$MODEL_DIR"
        echo -e "${GREEN}✅ Models found${NC}"
    else
        echo -e "${YELLOW}⚠️  No trained models yet${NC}"
    fi
else
    echo "Model directory not created yet"
fi

# Get training data statistics
echo -e "\n${YELLOW}📊 Training Data Statistics:${NC}"
source "$VENV_DIR/bin/activate"
cd "$WEBAPP_DIR"
python manage.py auto_train_models --days 90 2>&1 | grep -E "Total messages|Analyzed messages|feedback|PHQ-9|GAD-7|Insufficient|Sufficient"

echo ""
echo "=========================================="
echo "To manually trigger training:"
echo "cd $WEBAPP_DIR"
echo "source $VENV_DIR/bin/activate"
echo "python manage.py auto_train_models"
echo "=========================================="
