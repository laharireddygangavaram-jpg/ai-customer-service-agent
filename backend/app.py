import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask
from flask_cors import CORS
from routes.chat_routes import chat_bp
from routes.store_routes import store_bp

app = Flask(__name__)

CORS(app)

app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(store_bp, url_prefix="/api")

@app.route("/")
def home():
    return {
        "message": "AI Customer Support Agent is running",
        "status": "success"
    }


if __name__ == "__main__":
    app.run(debug=True)