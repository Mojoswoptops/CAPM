from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'your_secret_key'
    
    # Use an absolute path for the database file in the 'website' folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{path.join(path.dirname(__file__), DB_NAME)}'
    
    db.init_app(app)
    
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    create_database(app)  # Call the function to create the database
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to the login page if not logged in
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        from .models import User  # Import User here to avoid circular imports
        return User.query.get(int(id))   
    
    return app


def create_database(app):
    with app.app_context():  # Push the application context
        from .models import User, Job, CostItem  # Import models here to avoid circular imports
        db.create_all()
