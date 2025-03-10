from models import app, db

# Drop all tables and recreate them
with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create tables based on the models
    print("Database initialized successfully!")