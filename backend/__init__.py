from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
app.config.from_pyfile('config.py')

mail = Mail(app)

# Import routes and other components
from app import routes
