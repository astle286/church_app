from flask import Flask
from config import Config
from .models import db, User
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login = LoginManager(app)
    login.login_view = 'login'

    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)
    
    return app

from flask import Flask
from app.models import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.cli.command("init-db")
def init_db():
    from app.models import db
    with app.app_context():
        db.create_all()
        print("✅ Database initialized.")

