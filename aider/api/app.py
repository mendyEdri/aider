from flask import Flask
from aider.api.routes2 import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api/v2')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
