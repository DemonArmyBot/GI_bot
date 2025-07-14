import os
import subprocess
from flask import Flask

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

# Start bot process when app loads
print("🚀 Starting bot in background...")
bot_process = subprocess.Popen(["/bin/bash", "run.sh"])

@app.route('/')
def health_check():
    return "🤖 Bot is running in web service mode! 🚀"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    print(f"🌐 Starting web service on port {port}")
    app.run(host='0.0.0.0', port=port)
