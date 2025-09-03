#!/bin/bash

# ============================
# SCRIPT CONFIGURATION
# ============================
SCRIPT_NAME="python main.py"
REPO_DIR="/volume1/Shared/Repos/BCN-Transit-Bot"
VENV_DIR="_venv"

echo "🚀 Starting bot deployment..."

# ============================
# STOP THE BOT IF IT'S RUNNING
# ============================
echo "🔹 Stopping the current bot process..."

pkill -f "$SCRIPT_NAME"

# Wait until the process is fully stopped
while ps aux | grep "$SCRIPT_NAME" | grep -v grep > /dev/null; do
    echo "   ⏳ Bot process is still running, waiting..."
    sleep 1
done

echo "✅ Bot process '$SCRIPT_NAME' has been stopped."

# ============================
# UPDATE REPOSITORY
# ============================
echo "🔹 Updating repository..."
cd "$REPO_DIR" || {
    echo "❌ Error: Could not access repository directory $REPO_DIR"
    exit 1
}

git reset --hard
git pull

# ============================
# ACTIVATE OR CREATE VIRTUAL ENVIRONMENT
# ============================
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️ Virtual environment not found, creating one..."
    python3 -m venv "$VENV_DIR"
fi

echo "🔹 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# ============================
# INSTALL DEPENDENCIES
# ============================
echo "🔹 Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# ============================
# START THE BOT
# ============================
echo "🔹 Starting the bot..."
nohup python main.py > bot.log 2>&1 &

echo "✅ Deployment completed successfully."
echo "📜 Check logs at: $REPO_DIR/bot.log"
