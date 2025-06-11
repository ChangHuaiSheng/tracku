from flask import Flask, render_template, jsonify, request, Response, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from flask_cors import CORS
from dataclasses import dataclass
import json

app = Flask(__name__)

# Configure a secret key for session management.
# IMPORTANT: In a real application, use a strong, randomly generated key
# and store it securely (e.g., environment variable).
app.config['SECRET_KEY'] = 'your_super_secret_key_here' # CHANGE THIS IN PRODUCTION!

# Configure the SQLite database file
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True) # Create instance folder if it doesn't exist
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "gps.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the GPS data model for user check-ins
class GpsData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<GpsData {self.user_email} - Lat: {self.latitude}, Lng: {self.longitude}>"

# Define the AdminUser model for dashboard login
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser {self.username}>"

# Define the User model for mobile app login
@dataclass
class User(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    email:str = db.Column(db.String(80), unique=True, nullable=False)
    name:str = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

# Function to create database tables and add data
def create_tables_and_data():
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'gps.db')
        
        # Always call db.create_all() to ensure all tables are created or updated
        # This is safe to call even if tables already exist.
        db.create_all() 
        print("Database tables checked/created.")

        # Check if AdminUser table has records
        admin_user_exists = AdminUser.query.first() is not None
        
        if not admin_user_exists:
            print("Adding initial admin user...")
            admin = AdminUser(username='admin')
            admin.set_password('password') # The password for the admin is 'password'
            db.session.add(admin)
            db.session.commit()
            print("Admin user 'admin' created with password 'password'.")
        else:
            print("Admin user already exists. Skipping insertion.")

        # Check if GpsData table has records
        # gps_data_exists = GpsData.query.first() is not None
        
        # if not gps_data_exists:
        #     print("Adding initial dummy GPS data...")
        #     dummy_gps_entries = [
        #         GpsData(user_email="userA@mail.com", latitude=3.141592, longitude=101.690123, timestamp=datetime.datetime.now() - datetime.timedelta(hours=2)),
        #         GpsData(user_email="userB@mail.com", latitude=3.138400, longitude=101.686900, timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30)),
        #         GpsData(user_email="userC", latitude=3.150000, longitude=101.700000, timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=15)),
        #         GpsData(user_email="userD", latitude=3.147000, longitude=101.692000, timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=10)),
        #         GpsData(user_email="userE", latitude=3.135000, longitude=101.685000, timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=3))
        #     ]
        #     db.session.add_all(dummy_gps_entries)
        #     db.session.commit()
        #     print("Dummy GPS data added.")
        # else:
        #     print("GPS data already exists. Skipping insertion.")
        
        print("Database setup complete.")


# Route for the admin login page
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = user.username
            # Flash success message only if coming from a fresh login
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return render_template('login.html', error='Invalid username or password')
    
    # When rendering login.html via GET request, clear any existing flash messages
    # This prevents old messages (like "Logged in successfully!") from reappearing.
    session.pop('_flashes', None) # Clear all flash messages
    return render_template('login.html')

# Route for logging out
@app.route('/logout_admin')
def logout_admin():
    session.pop('logged_in', None)
    session.pop('username', None)
    # Flash a message indicating successful logout
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_admin'))

# Route for the main dashboard page - now protected
@app.route('/')
def index():
    if not session.get('logged_in'):
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login_admin'))
    return render_template('index.html', username=session.get('username'))

# API endpoint to get GPS data - also protected
@app.route('/api/get_gps_data')
def get_gps_data():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    gps_entries = GpsData.query.order_by(GpsData.timestamp.desc()).all()
    data = []
    for entry in gps_entries:
        data.append({
            'id': entry.id,
            'user_email': entry.user_email,
            'latitude': entry.latitude,
            'longitude': entry.longitude,
            'timestamp': entry.timestamp.isoformat()
        })
    return jsonify(data)

# API endpoint to register new user
@app.route('/api/register_user/<email>/<name>/<password>', methods=['POST'])
def register_user(email, name, password):
    try:
        user_entry = User(email=email, name=name)
        user_entry.set_password(password)
        db.session.add(user_entry)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        print(error)
        return Response("{'status':'failed'}", status=403)
    print("User registered.")
    return Response("{'status':'success'}", status=200)

# API endpoint to login user
@app.route('/api/login_user/<email>/<password>', methods=['GET'])
def login_user(email, password):
    user_entry = db.session.execute(db.select(User).filter_by(email=email)).scalar_one()
    if user_entry.check_password(password):
        return jsonify(user_entry)
    else:
        return jsonify(User(id=0))

# API enpoint to insert GPS data
@app.route('/api/insert_gps_data/<user_email>/<latitude>/<longitude>/<timestamp>', methods=['POST'])
def insert_gps_data(user_email, latitude, longitude, timestamp):
    timestamp_obj = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    gps_entry = GpsData(user_email=user_email, latitude=latitude, longitude=longitude, timestamp=timestamp_obj)
    db.session.add(gps_entry)
    db.session.commit()
    print("GPS data added.")
    return "Insert success!"

if __name__ == '__main__':
    create_tables_and_data()
    app.run(debug=True)
