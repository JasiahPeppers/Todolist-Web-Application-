from flask import Flask, request, jsonify, session
import os
import logging
from flask_cors import CORS
from extensions import db  # Import db from extensions.py
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# CORS Configuration
# Allow requests from the specific frontend domain
CORS(app, origins=["https://todolistapp.infy.uk"])  # Allow the frontend domain  # Allow the frontend domain

# Set a secret key for session management (using the one you generated)
app.secret_key = os.environ.get('SECRET_KEY', 'b07d3858c42f80893b1176555d8cb7b1b96c03949018bc724eca0afc9ce7456c')  # Replace with your actual secret key in production

# PostgreSQL URL for your Render database
db_url = os.environ.get('DATABASE_URL', 'postgresql://backend_db_flask_user_vmia_user:pVpy47XSEhOaro9AinYSzphKMumM8Aug@dpg-cve54nan91rc73bedsu0-a/backend_db_flask_user_vmia')

# Setting up the database URI (PostgreSQL in production, SQLite for local testing)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

from models import User, Task

# More Logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

with app.app_context():
    db.create_all()

# Test DB route
@app.route('/test_db', methods=['GET'])
def test_db():
    try:
        user_count = User.query.count()
        return jsonify({'message': f'Database is connected, {user_count} users found.'}), 200
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        return jsonify({'message': 'Database connection failed'}), 500

# Registration route 
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            logging.error("Invalid request")
            return jsonify({'message': 'Invalid request data'}), 400

        username = data['username']
        password = data['password']

        if User.query.filter_by(username=username).first():
            logging.warning(f"Username '{username}' already exists")
            return jsonify({'message': 'Username already exists'}), 400

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        logging.info(f"User '{username}' registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        logging.error(f"Error during registration: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500

# Login route (with added logging)
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            logging.error("Invalid login")
            return jsonify({'message': 'Invalid request data'}), 400

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if user:
            logging.info(f"User '{username}' found, checking password...")
            if user.check_password(password):
                session['username'] = username
                logging.info(f"User '{username}' logged in successfully")
                return jsonify({'message': 'Logged in successfully'}), 200
            else:
                logging.warning(f"Incorrect password for '{username}'")
                return jsonify({'message': 'Invalid username or password'}), 401
        else:
            logging.warning(f"User '{username}' not found")
            return jsonify({'message': 'Invalid username or password'}), 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'message': 'Internal server error'}), 500
@app.route('/users', methods=['GET'])
def get_users():
    """Retrieve all users in the database."""
    try:
        users = User.query.all()
        user_list = [{'id': u.id, 'username': u.username} for u in users]

        logging.info(f"Fetched {len(user_list)} users successfully")
        return jsonify(user_list), 200  # Returns list of users in JSON format

    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    """Add a new task with user ID validation."""
    try:
        data = request.get_json()
        logging.info(f"Received Task Data: {data}")

        # Validate request data
        if not data or 'task' not in data or 'user_id' not in data:
            logging.warning("Invalid task data received")
            return jsonify({'error': 'Invalid request data'}), 400
        
        # Ensure `user_id` is properly extracted and not None
        user_id = data.get('user_id')
        if user_id is None:
            logging.warning("User ID is missing or null")
            return jsonify({'error': 'User ID is required'}), 400

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            logging.warning(f"User ID {user_id} not found in the database")
            return jsonify({'error': 'User not found'}), 404

        # Create and commit task
        new_task = Task(
            task=data['task'],
            description=data.get('description', ''),
            priority=data.get('priority', 'low'),
            status=data.get('status', True),  
            task_date=data.get('task_date', ''),
            user_id=user_id  # Ensure `user_id` is set correctly
        )

        db.session.add(new_task)
        db.session.commit()

        logging.info(f"Task '{new_task.task}' added successfully for User {user_id}")
        return jsonify({'message': 'Task added successfully', 'task_id': new_task.id}), 201

    except Exception as e:
        logging.error(f"Error adding task: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


        # Create task
        new_task = Task(
            task=data['task'],
            description=data.get('description', ''),
            priority=data.get('priority', 'low'),
            status=True,  
            task_date=data.get('task_date', ''),
            user_id=data['user_id']
        )

        db.session.add(new_task)
        db.session.commit()

        logging.info(f"Task '{new_task.task}' added for User {data['user_id']}")
        return jsonify({'message': 'Task added successfully', 'task_id': new_task.id}), 201

    except Exception as e:
        logging.error(f"Error adding task: {e}")
        db.session.rollback()  # Prevent corruption on failure
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Retrieve all tasks."""
    try:
        tasks = Task.query.all()
        task_list = [{
            'id': t.id,
            'task': t.task,
            'description': t.description,
            'priority': t.priority if t.priority else 'low',
            'status': t.status,
            'task_date': t.task_date,
            'user_id': t.user_id
        } for t in tasks]

        logging.info(f"Fetched {len(task_list)} tasks successfully")
        return jsonify(task_list), 200  # Returns list of tasks in JSON format

    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

# Run the app with debug enabled
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
