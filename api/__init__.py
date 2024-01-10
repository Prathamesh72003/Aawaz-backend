from flask import Flask
import firebase_admin
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate("api/key.json")
default_app = initialize_app(cred)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    
    
    from .userapi import userapi

    app.register_blueprint(userapi, url_prefix='/user')

    return app