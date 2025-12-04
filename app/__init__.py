import os 
from flask import Flask, request
from config import Config
from ml.loader import load_model
from app.utils.helper import resource_path

import logging
from logging.handlers import RotatingFileHandler


def create_app():
    """Application factory - Create and configures the flask app""" 

    # 1. Creates flask app with correct paths
    app = Flask(__name__,
                template_folder=resource_path('app/templates'),
                static_folder=resource_path('app/static')
            )
    
    # Simple Logging Middleware
    if not os.path.exists("logs"):
        os.mkdir("logs")

    handler = RotatingFileHandler('logs/app.log', maxBytes=100000, backupCount=3)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)


    @app.before_request
    def log_request():
        app.logger.info(
            f"REQUEST: {request.method} {request.path} | IP={request.remote_addr}"
        )

    @app.after_request
    def log_response(response):
        app.logger.info(
            f"RESPONSE: {response.status} for {request.method} {request.path}"
        )
        return response

    app.secret_key = os.urandom(24)  # Secure key for sessions and flash messages


    # 2. Load configuration
    config = Config()
    app.config["APP_CONFIG"] = config 


    # 3. Load ML Model ONCE
    app.model = load_model(config)

    if app.model is None:
        print("Error: Model could not be loaded.")
    
    # 4. Register Blueprints

    from app.routes.page_routes import static_bp
    from app.routes.coordinate_routes import coordinate_bp
    from app.routes.predictions_routes import prediction_bp

    app.register_blueprint(static_bp)
    app.register_blueprint(coordinate_bp)
    app.register_blueprint(prediction_bp)

    # 5. Return app
    return app

    

