from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    children = db.relationship('Child', backref='parent', lazy=True)
    stories = db.relationship('Story', backref='author', lazy=True)

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    native_place = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=True, default='Any')

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    moral = db.Column(db.String(100), nullable=True)
    audio_data = db.Column(db.Text, nullable=True)
    
    # 🚀 NAYA: Image URL save karne ke liye
    image_url = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class RegionalStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(100), nullable=False)
    moral = db.Column(db.String(100), nullable=False)
    core_story = db.Column(db.Text, nullable=False)
    target_gender = db.Column(db.String(50), nullable=True, default='Any')
    theme = db.Column(db.String(100), nullable=True, default='General')
    min_age = db.Column(db.Integer, nullable=True, default=3)
    max_age = db.Column(db.Integer, nullable=True, default=10)
