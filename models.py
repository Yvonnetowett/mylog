from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///item.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'supersecretkey'

# Initialize SQLAlchemy
db = SQLAlchemy()

migrate = Migrate(app, db)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'user' or 'admin'


    def __init__(self, fullname, email, password, role='user'):
        self.fullname = fullname
        self.email = email
        self.password = password
        self.role = role
    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        """Hash the password and store it."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password, password)

# Item Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'breakfast', 'lunch', etc.
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)  # Path to the uploaded image
    
    
    def __init__(self, category, name, price, description, image):
        self.category = category
        self.name = name
        self.price = price
        self.description = description
        self.image = image
        
    def __repr__(self):
        return f'<Item {self.name}>'