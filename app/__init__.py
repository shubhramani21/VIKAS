import os 
from flask import Flask
from config import Config
from app.models import load_model
from app.utils.helper import resource_path

def create_app():
    """Application factory - Create and configures the flask app""" 

    # 1. Creates flask app with correct paths
    app = Flask(__name__,
                template_folder=resource_path('app/templates'),
                static_folder=resource_path('app/static')
            )
    
    app.secret_key = os.urandom(24)  # Secure key for sessions and flash messages


    # 2. Load configuration
    config = Config()
    app.config.from_object(config)


    # 3. Load ML Model ONCE
    app.model = load_model(app.config)

    if app.model is None:
        print("Error: Model could not be loaded.")
    
    # 4. Register Blueprints

    from app.routes.static_routes import static_bp
    from app.routes.coordinate_routes import coordinate_bp
    from app.routes.predictions_routes import prediction_bp

    app.register_blueprint(static_bp)
    app.register_blueprint(coordinate_bp)
    app.register_blueprint(prediction_bp)

    # 5. Return app
    return app

    

