import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from models import db, User, Item
import bcrypt
from sqlalchemy import inspect  # Import inspect for table inspection

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize db with the app
db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Debugging: Print database schema
with app.app_context():
    # Use inspect to get table names
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables in the database:", tables)

    # Print columns in the User table
    if 'user' in tables:
        columns = inspector.get_columns('user')
        print("Columns in the User table:", [column['name'] for column in columns])

    # Print columns in the Item table
    if 'item' in tables:
        columns = inspector.get_columns('item')
        print("Columns in the Item table:", [column['name'] for column in columns])

# Create the database tables
with app.app_context():
    db.create_all()

    # Create a default admin user if it doesn't exist
    admin_email = "admin@example.com"
    admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    admin_user = User.query.filter_by(email=admin_email, role='admin').first()
    if not admin_user:
        admin_user = User(fullname="Admin", email=admin_email, password=admin_password.decode('utf-8'), role='admin')
        db.session.add(admin_user)
        db.session.commit()

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, role='admin').first()
        print("Admin user:", user)  # Debug statement

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('admin_login'))

    return render_template('login1.html')

# User Login
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        print("User:", user)  # Debug statement

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('user_login'))

    return render_template('login2.html')

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())

        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please use a different email.", "error")
            return redirect(url_for('signup'))

        new_user = User(fullname=fullname, email=email, password=password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('user_login'))

    return render_template('signup.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html')

# User Dashboard
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('user_login'))

    return render_template('user_dashboard.html', user=user)

# View Users
@app.route('/view_users')
def view_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    users = User.query.all()
    print("Users:", users)  # Debug statement
    return render_template('view_users.html', users=users)

# Services Page
@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    return render_template('services.html')

# Service Pages
@app.route('/service/<service_name>')
def service(service_name):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    # Render a template for each service
    return render_template(f'service_{service_name}.html', service_name=service_name)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/addproducts', methods=['GET', 'POST'])
def addproducts():
    # Check if the user is an admin
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # Handle form submission
        category = request.form.get('category')
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        image = request.files.get('image')

        # Validate all fields
        if not category or not name or not price or not description or not image:
            flash("Please fill out all fields.", "error")
            return redirect(url_for('addproducts'))

        if not image.filename:
            flash("No file selected for upload.", "error")
            return redirect(url_for('addproducts'))

        if not allowed_file(image.filename):
            flash("Invalid file type. Only images are allowed.", "error")
            return redirect(url_for('addproducts'))

        # Save the uploaded image
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Add the item to the database
        new_item = Item(category=category, name=name, price=price, description=description, image=filename)
        db.session.add(new_item)
        db.session.commit()

        flash("Product added successfully.", "success")
        return redirect(url_for('addproducts'))

    # If the request method is GET, render the addproducts.html template
    items = Item.query.all()
    return render_template('addproducts.html', items=items)

# Modify System
@app.route('/modify_system', methods=['GET', 'POST'])
def modify_system():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        if not user_id or not action:
            flash("Please fill out all fields.", "error")
            return redirect(url_for('modify_system'))

        user = User.query.get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for('modify_system'))

        try:
            if action == 'delete':
                db.session.delete(user)
                flash(f"User {user.email} deleted successfully.", "success")
            elif action == 'promote':
                user.role = 'admin'
                flash(f"User {user.email} promoted to admin.", "success")
            elif action == 'demote':
                user.role = 'user'
                flash(f"User {user.email} demoted to user.", "success")
            else:
                flash("Invalid action.", "error")
                return redirect(url_for('modify_system'))
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(url_for('modify_system'))

    return render_template('modify_system.html')

if __name__ == '__main__':
    app.run(debug=True)