from flask import Flask, request, jsonify, session, abort
import os
import logging
from flask_cors import CORS
from extensions import db  # Import db from extensions.py
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Set a secret key for session management (using the one you generated)
app.secret_key = os.environ.get('SECRET_KEY', '78f781ecfb73f94c3494ff80d85cca53c4e6967376d89cad')  # Replace with your actual secret key in production

# PostgreSQL URL for your Render database
db_url = os.environ.get('DATABASE_URL', 'postgresql://task_b30z_user:YSEO8sT6RBjDLCClvedFcjhSB1htk2e8@dpg-cvjolq0gjchc73d6bkeg-a.oregon-postgres.render.com/task_b30z')

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

        # Hash the password before storing it
        new_user = User(username=username)
        new_user.set_password(password)  # Assuming the `set_password` method hashes the password
        db.session.add(new_user)
        db.session.commit()

        logging.info(f"User '{username}' registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        logging.error(f"Error during registration: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500


# Login route
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

        # Check if the user exists and the password matches
        if user and user.check_password(password):  # Assuming `check_password` compares the hashed password
            session['username'] = username  # Store the username in the session
            logging.info(f"User '{username}' logged in successfully")
            return jsonify({'message': 'Logged in successfully'}), 200
        else:
            logging.warning(f"Invalid login '{username}'")
            return jsonify({'message': 'Invalid username or password'}), 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'message': 'Internal server error'}), 500


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    logging.info("User logged out")
    return jsonify({'message': 'Successfully logged out'}), 200


# Tasks route (GET and POST)
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'username' not in session:
        logging.warning("Unauthorized access to tasks")
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        logging.error(f"User '{session['username']}' not found in the database")
        return jsonify({'message': 'User not found'}), 404

    try:
        if request.method == 'GET':
            tasks = Task.query.filter_by(user_id=user.id).all()
            logging.info(f"Tasks retrieved for user '{user.username}'")
            return jsonify([task.to_dictionary() for task in tasks])

        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'task' not in data:
                logging.error("Invalid task data")
                return jsonify({'message': 'Invalid task data'}), 400

            new_task = Task(
                task=data['task'],
                description=data.get('description', ''),
                priority=data.get('priority', ''),
                status=data.get('status', True),
                task_date=data.get('task_date', ''),
                user_id=user.id
            )
            db.session.add(new_task)
            db.session.commit()
            logging.info(f"Task created for user '{user.username}'")
            return jsonify(new_task.to_dictionary()), 201

    except Exception as e:
        logging.error(f"Error getting task: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500


# Task route for PUT and DELETE
@app.route('/tasks/<int:id>', methods=['PUT', 'DELETE'])
def task(id):
    if 'username' not in session:
        logging.warning("Unauthorized")
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        logging.error(f"User '{session['username']}' not found in the database")
        return jsonify({'message': 'User not found'}), 404

    task = Task.query.filter_by(id=id, user_id=user.id).first()
    if not task:
        logging.warning(f"Task with id '{id}' not found for user '{user.username}'")
        return jsonify({'message': 'Task not found'}), 404

    try:
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                logging.error("Invalid update task data")
                return jsonify({'message': 'Invalid update data'}), 400

            task.task = data.get('task', task.task)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            task.status = data.get('status', task.status)
            task.task_date = data.get('task_date', task.task_date)
            db.session.commit()
            logging.info(f"Task '{id}' updated for user '{user.username}'")
            return jsonify(task.to_dictionary())

        elif request.method == 'DELETE':
            db.session.delete(task)
            db.session.commit()
            logging.info(f"Task '{id}' deleted for user '{user.username}'")
            return '', 204

    except Exception as e:
        logging.error(f"Error in task modification: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500


# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
