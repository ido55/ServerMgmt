from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


db = SQLAlchemy()
def create_app():
    app = Flask(__name__,template_folder='templates')
    os.makedirs(app.instance_path,exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'testDb.db')
    db.init_app(app)

    #imports here to avoid circular imports
    from routes import register_routes
    register_routes(app,db)

    migrate = Migrate(app,db)
    return app