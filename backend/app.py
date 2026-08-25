from flask import Flask, send_from_directory
from routes.chat_routes import chat_bp
import os

app = Flask(__name__)

app.register_blueprint(chat_bp, url_prefix="/api")


# Serve frontend
@app.route("/")
def home():
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
        "index.html"
    )


# Serve frontend CSS and JavaScript
@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
        filename
    )


if __name__ == "__main__":
    app.run(debug=True)