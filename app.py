from flask import Flask, request, jsonify, session, abort
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
db_url = os.environ.get('DATABASE_URL', 'postgresql://backend_db_flask_user_vmia_user:pVpy47XSEhOaro9AinYSzphKMumM8Aug@dpg-cve54nan91rc73bedsu0-a.oregon-postgres.render.com/backend_db_flask_user_vmia')
print("Database URL:", db_url)  # This will print the database URL to verify it's correct

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
# TASKS ROUTES SECTION 
# This should GET all tasks routes 
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = Task.query.all()
        task_list = [{'id': t.id, 'task': t.task, 'description': t.description, 'priority': t.priority, 'status': t.status, 'task_date': t.task_date} for t in tasks]
        return jsonify(task_list), 200
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/updateOrder', methods=['POST'])
def update_task_order():
    try:
        data = request.get_json()
        if not data or 'newOrder' not in data:
            return jsonify({'message': 'Invalid request data'}), 400

        # Loop through the new task order and update each task position
        for index, task_id in enumerate(data['newOrder']):
            task = Task.query.get(task_id)
            if task:
                task.priority = index  # Assuming you want to store the order as priority level
                db.session.commit()

        return jsonify({'message': 'Task order updated successfully'}), 200
    except Exception as e:
        logging.error(f"Error updating task order: {e}")
        return jsonify({'message': 'Internal server error'}), 500
# Delete a task
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'}), 200

# Update a task
@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.get_json()
    task.task = data.get('task', task.task)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    task.status = data.get('status', task.status)

    db.session.commit()
    return jsonify({'message': 'Task updated successfully'}), 200
# Run the app with debug enabled
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
