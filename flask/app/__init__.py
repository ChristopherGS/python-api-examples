from config import Config

from flask import Flask, request, current_app

app = Flask(__name__)
app.config.from_object(Config)

from app.api import routes