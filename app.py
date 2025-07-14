# app.py
import os
import threading
from flask import Flask
import subprocess

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

def run_bot():
    """Run the bot using the existing run.sh script"""
    subprocess.run(["./run.sh"], check=True)

@app.route('/')
def health_check():
    """Health check endpoint for Render"""
    return "🤖 Bot is running in web service mode! 🚀"

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=port)
