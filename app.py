from flask import Flask
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

# Import Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.main import main_bp

def create_app():
    app = Flask(__name__)
    
    # Configurations
    app.secret_key = 'ethic_super_secret_key_2026'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ethic_v3.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Database Extension
    db.init_app(app)

    # Register Blueprints (Connecting the modular files)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    # Database Tables Creation & Default Admin Setup
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@ethic.com').first():
            hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(name='Super Admin', email='admin@ethic.com', password=hashed_pw, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
