from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.main import main  # Import the main blueprint
    app.register_blueprint(main)  # Register the blueprint

    return app
