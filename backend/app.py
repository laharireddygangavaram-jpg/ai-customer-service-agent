
import sys
from pathlib import Path

# =========================================================
# PROJECT PATHS
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
BACKEND_DIR = ROOT_DIR / "backend"

# Add project directories to Python path

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# =========================================================
# FLASK
# =========================================================

from flask import Flask
from flask_cors import CORS

from routes.chat_routes import chat_bp
from routes.store_routes import store_bp


# =========================================================
# CREATE APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# REGISTER ROUTES
# =========================================================

app.register_blueprint(
    chat_bp,
    url_prefix="/api"
)

app.register_blueprint(
    store_bp,
    url_prefix="/api"
)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return {
        "message": "AI Customer Support Agent is running",
        "status": "success"
    }


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

