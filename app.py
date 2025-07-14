import os
import subprocess
from flask import Flask
import logging

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start bot process
try:
    logger.info("🚀 Starting bot process...")
    bot_process = subprocess.Popen(["/bin/bash", "run.sh"])
    logger.info(f"🤖 Bot started with PID: {bot_process.pid}")
except Exception as e:
    logger.error(f"🔥 Failed to start bot: {str(e)}")

@app.route('/')
def health_check():
    return "🤖 Bot is running in web service mode! 🚀"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    logger.info(f"🌐 Starting web service on port {port}")
    app.run(host='0.0.0.0', port=port)
