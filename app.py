from flask import Flask, request, jsonify, session, abort
import os
from flask_migrate import Migrate
import logging
from flask_cors import CORS
from extensions import db  # Import db from extensions.py
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # <-- Import datetime module here

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Set a secret key for session management (using the one you generated)
app.secret_key = os.environ.get('SECRET_KEY', 'b07d3858c42f80893b1176555d8cb7b1b96c03949018bc724eca0afc9ce7456c')  # Replace with your actual secret key in production

# PostgreSQL URL for your Render database
db_url = os.environ.get('DATABASE_URL', 'postgresql://backend_db_flask_user_vmia_user:pVpy47XSEhOaro9AinYSzphKMumM8Aug@dpg-cve54nan91rc73bedsu0-a/backend_db_flask_user_vmia')
print("Database URL:", db_url)  # This will print the database URL to verify it's correct

# Setting up the database URI (PostgreSQL in production, SQLite for local testing)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

from models import User, Task

# need logging?
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

with app.app_context():
    db.create_all()

# Test DB route (optional)
@app.route('/test_db', methods=['GET'])
def test_db():
    try:
        user_count = User.query.count()
        return jsonify({'message': f'Database is connected, {user_count} users found.'}), 200
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        return jsonify({'message': 'Database connection failed'}), 500

# Registration route (no change)
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

# Run the app with debug enabled
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
## THIS IS WHERE THE TASK ROUTES ARE LOCATED 
# GET /tasks route
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        username = session.get('username')
        if not username:
            return jsonify({'message': 'You must be logged in to fetch tasks'}), 403

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        tasks = Task.query.filter_by(user_id=user.id).all()
        
        # Debugging: Check if the tasks list is populated
        if not tasks:
            logging.info(f"No tasks found for user '{username}'")
        
        tasks_data = [{
            'id': task.id,
            'task': task.task,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'task_date': task.task_date,
            'user_id': task.user_id 
        } for task in tasks]

        return jsonify(tasks_data), 200
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return jsonify({'message': 'Internal server error'}), 500

# POST /tasks route (adding a new task)
@app.route('/tasks', methods=['POST'])
def add_task():
    try:
        username = session.get('username')
        if not username:
            return jsonify({'message': 'You must be logged in to add a task'}), 403
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        logging.info(f"Logged-in user: {user.username}, user_id: {user.id}")

        data = request.get_json()
        if not data or 'task' not in data or 'task_date' not in data:
            return jsonify({'message': 'Invalid request data, task and task_date are required'}), 400

        task_date = data['task_date']
        
        # Ensure task_date is in a valid format (simple validation)
        try:
            datetime.strptime(task_date, '%Y-%m-%d')  # Adjust format if necessary
        except ValueError:
            return jsonify({'message': 'Invalid task_date format. Use YYYY-MM-DD'}), 400

        task = Task(
            task=data['task'],
            description=data.get('description', ''),
            priority=data.get('priority', 'low'),
            status=True,
            task_date=task_date,
            user_id=user.id  # Ensure this is not None
        )
        
        # Debugging: Output the task being added
        logging.info(f"Adding task: {task.task} for user_id {user.id}")

        db.session.add(task)
        db.session.commit()

        return jsonify({
            'id': task.id,
            'task': task.task,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'task_date': task.task_date
        }), 201
    except Exception as e:
        logging.error(f"Error adding task: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500
        
@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()  # Query to fetch all users from the User table
        
        # Create a list of dictionaries to return only the required data (username and id)
        users_data = [{
            'id': user.id,
            'username': user.username
        } for user in users]

        return jsonify(users_data), 200
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({'message': 'Internal server error'}), 500
        
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        username = session.get('username')
        if not username:
            return jsonify({'message': 'You must be logged in to delete a task'}), 403
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
        
        if task.user_id != user.id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200

    except Exception as e:
        logging.error(f"Error deleting task: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500
        
 # PUT /tasks/<task_id> route (updating a task)
@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        username = session.get('username')
        if not username:
            return jsonify({'message': 'You must be logged in to update a task'}), 403
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
        
        if task.user_id != user.id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'status' in data:
            task.status = data['status']
        
        if 'priority' in data:
            task.priority = data['priority']
        
        if 'description' in data:
            task.description = data['description']
        
        db.session.commit()

        return jsonify({
            'id': task.id,
            'task': task.task,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'task_date': task.task_date
        }), 200

    except Exception as e:
        logging.error(f"Error updating task: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500
       

# Run the app with debug enabled
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
