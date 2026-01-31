#!/bin/bash

# MindLift Deployment Script for Google Cloud VM
# This script automates the deployment process
# Run as: sudo bash deploy.sh

set -e  # Exit on error

echo "=================================="
echo "MindLift Deployment Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/home/mindlift/mindlift"
WEBAPP_DIR="$PROJECT_DIR/webapp"
RASA_DIR="$PROJECT_DIR/rasa"
PYTHON_VERSION="3.10.9"
MYSQL_ROOT_PASSWORD=""
MYSQL_APP_PASSWORD=""
DB_NAME="mindlift_db"
DB_USER="mindlift_user"

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Step 1: Update system
echo ""
print_info "Step 1: Updating system packages..."
apt-get update -y
apt-get upgrade -y
print_success "System updated"

# Step 2: Install essential packages
echo ""
print_info "Step 2: Installing essential packages..."
apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    vim \
    screen \
    htop \
    software-properties-common \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    libbz2-dev \
    liblzma-dev \
    python3-dev \
    libmysqlclient-dev \
    pkg-config
print_success "Essential packages installed"

# Step 3: Install Python 3.10.9
echo ""
print_info "Step 3: Installing Python $PYTHON_VERSION..."
if [ ! -f "/usr/local/bin/python3.10" ]; then
    cd /tmp
    wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION
    ./configure --enable-optimizations --with-ensurepip=install
    make -j $(nproc)
    make altinstall
    ln -sf /usr/local/bin/python3.10 /usr/local/bin/python3
    ln -sf /usr/local/bin/pip3.10 /usr/local/bin/pip3
    print_success "Python $PYTHON_VERSION installed"
else
    print_success "Python $PYTHON_VERSION already installed"
fi

# Verify Python version
PYTHON_VER=$(python3.10 --version)
print_info "Python version: $PYTHON_VER"

# Step 4: Install MySQL
echo ""
print_info "Step 4: Installing MySQL Server..."
if ! command -v mysql &> /dev/null; then
    apt-get install -y mysql-server mysql-client
    print_success "MySQL installed"
    
    print_info "Please run 'sudo mysql_secure_installation' manually after this script"
else
    print_success "MySQL already installed"
fi

# Step 5: Create mindlift user
echo ""
print_info "Step 5: Creating mindlift user..."
if ! id "mindlift" &>/dev/null; then
    useradd -m -s /bin/bash mindlift
    print_success "User 'mindlift' created"
    print_info "Set password for mindlift user:"
    passwd mindlift
else
    print_success "User 'mindlift' already exists"
fi

# Step 6: Create project directory
echo ""
print_info "Step 6: Creating project directories..."
mkdir -p $PROJECT_DIR
chown -R mindlift:mindlift /home/mindlift
print_success "Project directories created"

# Step 7: Install Nginx
echo ""
print_info "Step 7: Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    systemctl enable nginx
    systemctl start nginx
    print_success "Nginx installed and started"
else
    print_success "Nginx already installed"
fi

# Step 8: Install Supervisor
echo ""
print_info "Step 8: Installing Supervisor..."
if ! command -v supervisorctl &> /dev/null; then
    apt-get install -y supervisor
    systemctl enable supervisor
    systemctl start supervisor
    print_success "Supervisor installed and started"
else
    print_success "Supervisor already installed"
fi

# Step 9: Configure firewall
echo ""
print_info "Step 9: Configuring UFW firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # HTTP
    ufw allow 443/tcp  # HTTPS
    ufw allow 8000/tcp # Django
    ufw allow 5005/tcp # RASA
    print_success "Firewall rules configured (run 'sudo ufw enable' to activate)"
else
    print_info "UFW not available, skipping firewall configuration"
fi

# Step 10: Create database
echo ""
print_info "Step 10: Database setup..."
print_info "Please create database manually with these commands:"
echo ""
echo "sudo mysql -u root -p"
echo "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';"
echo "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
echo "FLUSH PRIVILEGES;"
echo "EXIT;"
echo ""

# Step 11: Setup Python virtual environments
echo ""
print_info "Step 11: Virtual environments will be created when you upload project files"

echo ""
echo "=================================="
print_success "Initial setup completed!"
echo "=================================="
echo ""
print_info "Next steps:"
echo "1. Upload your project files to $PROJECT_DIR"
echo "2. Run the configuration script: sudo bash configure.sh"
echo "3. Create database using the SQL commands shown above"
echo ""
print_info "Switch to mindlift user: sudo su - mindlift"
