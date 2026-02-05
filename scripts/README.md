# MindLift Automatic Training Scripts

This directory contains scripts for automatic model training on your Google Cloud VM.

## 📁 Files

### `setup_cron.sh`
**Purpose**: One-time setup script to configure automatic training

**What it does**:
- Creates training script (`run_auto_training.sh`)
- Configures cron job (daily at 3 AM)
- Tests the setup
- Shows log locations

**Usage**:
```bash
bash /home/mindlift/mindlift/scripts/setup_cron.sh
```

---

### `check_training_status.sh`
**Purpose**: Check status of automatic training system

**What it shows**:
- Cron schedule
- Recent training activity
- Trained model files
- Training data statistics

**Usage**:
```bash
bash /home/mindlift/mindlift/scripts/check_training_status.sh
```

---

### `run_auto_training.sh`
**Purpose**: Training script executed by cron

**What it does**:
- Activates virtual environment
- Runs `auto_train_models` command
- Logs output to `logs/auto_training.log`

**Note**: This file is created automatically by `setup_cron.sh`

---

### `quick_setup.sh`
**Purpose**: Quick setup wrapper for easy deployment

**Usage**:
```bash
bash /home/mindlift/mindlift/scripts/quick_setup.sh
```

---

## 🚀 Quick Start

### 1. Upload scripts to your VM

**From your local machine**:
```bash
gcloud compute scp scripts/*.sh mindlift-production:/home/mindlift/mindlift/scripts/ --zone=us-central1-a
```

### 2. SSH into VM and run setup

```bash
# SSH into VM
gcloud compute ssh mindlift-production --zone=us-central1-a

# Switch to mindlift user
sudo su - mindlift

# Run setup
bash /home/mindlift/mindlift/scripts/setup_cron.sh
```

### 3. Verify

```bash
bash /home/mindlift/mindlift/scripts/check_training_status.sh
```

---

## 📋 Management Commands

### Django Management Commands

Located in: `webapp/chatbot/management/commands/`

#### `auto_train_models.py`
**Purpose**: Intelligent automatic training with data checks

**Usage**:
```bash
cd /home/mindlift/mindlift/webapp
source ../venv/bin/activate

# Check if training should run
python manage.py auto_train_models

# Force training
python manage.py auto_train_models --force

# Custom thresholds
python manage.py auto_train_models --min-messages 30

# Use recent data only
python manage.py auto_train_models --days 30

# Quiet mode (for cron)
python manage.py auto_train_models --quiet
```

**Options**:
- `--days N`: Use N days of data (default: 90)
- `--force`: Train even without sufficient data
- `--min-messages N`: Minimum messages required (default: 50)
- `--quiet`: Suppress output for cron jobs

---

#### `train_adaptive_models.py`
**Purpose**: Original training command (still available)

**Usage**:
```bash
python manage.py train_adaptive_models
python manage.py train_adaptive_models --days 90
python manage.py train_adaptive_models --force
python manage.py train_adaptive_models --stats-only
```

---

## 📊 Training Schedule

### Default Schedule
```
0 3 * * * /home/mindlift/mindlift/scripts/run_auto_training.sh
```
**Meaning**: Runs daily at 3:00 AM

### Customize Schedule

Edit crontab:
```bash
crontab -e
```

**Common schedules**:
```bash
# Every 6 hours
0 */6 * * *

# Twice daily (3 AM and 3 PM)
0 3,15 * * *

# Every 12 hours
0 */12 * * *

# Weekly (Sunday 2 AM)
0 2 * * 0

# Hourly
0 * * * *
```

---

## 📁 Directory Structure

```
/home/mindlift/mindlift/
├── scripts/
│   ├── setup_cron.sh              # Setup script (run once)
│   ├── check_training_status.sh   # Status checker
│   ├── run_auto_training.sh       # Cron training script (auto-created)
│   └── quick_setup.sh             # Quick deployment
├── logs/
│   └── auto_training.log          # Training logs
├── webapp/
│   ├── ml_models/                 # Trained model files
│   │   ├── sentiment_classifier.pkl
│   │   ├── theme_extractor.pkl
│   │   └── distortion_detector.pkl
│   └── chatbot/management/commands/
│       ├── auto_train_models.py   # Smart training command
│       └── train_adaptive_models.py # Original command
└── venv/                          # Virtual environment
```

---

## 🔍 Monitoring

### View Logs

```bash
# Real-time monitoring
tail -f /home/mindlift/mindlift/logs/auto_training.log

# Last 50 lines
tail -n 50 /home/mindlift/mindlift/logs/auto_training.log

# Search for errors
grep -i error /home/mindlift/mindlift/logs/auto_training.log
```

### Check Cron

```bash
# List cron jobs
crontab -l

# System cron logs
grep CRON /var/log/syslog | tail -20
```

### Check Models

```bash
ls -lh /home/mindlift/mindlift/webapp/ml_models/
```

---

## 🐛 Troubleshooting

### Training Not Running

**Check cron**:
```bash
crontab -l | grep training
sudo systemctl status cron
```

**Check logs**:
```bash
tail -f /home/mindlift/mindlift/logs/auto_training.log
```

**Test manually**:
```bash
cd /home/mindlift/mindlift/webapp
source ../venv/bin/activate
python manage.py auto_train_models --force
```

### Insufficient Data

**Check statistics**:
```bash
python manage.py auto_train_models
```

**Lower threshold**:
```bash
python manage.py auto_train_models --min-messages 20 --force
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R mindlift:mindlift /home/mindlift/mindlift

# Fix script permissions
chmod +x /home/mindlift/mindlift/scripts/*.sh
```

---

## 📈 Training Requirements

| Model | Min Messages | Purpose |
|-------|--------------|---------|
| Sentiment Classifier | 50 | Learn sentiment from feedback |
| Theme Extractor | 30 | Detect mental health themes |
| Distortion Detector | 20 | Identify cognitive distortions |

**Data Sources**:
- User messages with sentiment analysis
- User feedback corrections
- PHQ-9 depression assessments
- GAD-7 anxiety assessments
- Semantic analysis results

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ `crontab -l` shows training schedule
2. ✅ Logs show training attempts in `auto_training.log`
3. ✅ Model files exist in `ml_models/` directory
4. ✅ Training statistics show sufficient data
5. ✅ Accuracy metrics appear in logs

---

## 📚 Documentation

- **VM_SETUP_COMMANDS.md** - Step-by-step VM setup
- **AUTO_TRAINING_GUIDE.md** - Detailed training guide
- **DEPLOYMENT_GUIDE.md** - Full deployment (Section 12)

---

## 🎯 Quick Reference

```bash
# Setup (run once)
bash scripts/setup_cron.sh

# Check status
bash scripts/check_training_status.sh

# Manual training
cd webapp && source ../venv/bin/activate && python manage.py auto_train_models

# View logs
tail -f logs/auto_training.log

# Edit schedule
crontab -e
```

---

**Questions?** Check the documentation files or review the deployment guide.
