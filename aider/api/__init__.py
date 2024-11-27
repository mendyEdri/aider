from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    from .routes2 import api_bp as api_bp2
    app.register_blueprint(api_bp2, url_prefix='/api/v2')
    
    return app
