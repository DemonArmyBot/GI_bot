from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Tech VJ'

if __name__ == "__main__":
    app.run(port=8000)  # Run on port 8000
