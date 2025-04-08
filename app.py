from flask import Flask, request, jsonify, session, abort
import os
import logging
from flask_cors import CORS
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configure CORS (Allow all origins temporarily for debugging)
CORS(app, supports_credentials=True, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# Secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Database Configuration
db_url = os.environ.get('DATABASE_URL', 'postgresql://backend_db_flask_user_vmia_user:pVpy47XSEhOaro9AinYSzphKMumM8Aug@dpg-cve54nan91rc73bedsu0-a/backend_db_flask_user_vmia')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

# Import Models
from models import User, Task

# Enable Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create tables within the application context
with app.app_context():
    db.create_all()

@app.route('/test_db', methods=['GET'])
def test_db():
    """Check database connection."""
    try:
        user_count = User.query.count()
        return jsonify({'message': f'Database connected, {user_count} users found.'}), 200
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        return jsonify({'message': 'Database connection failed'}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    """Add a new task."""
    try:
        data = request.get_json()
        logging.info(f"Received Task Data: {data}")

        # Validate request data
        if not data or 'task' not in data or 'user_id' not in data:
            logging.warning("Invalid task data received")
            return jsonify({'error': 'Invalid request data'}), 400

        # Ensure user exists
        user = User.query.get(data['user_id'])
        if not user:
            logging.warning(f"User with ID {data['user_id']} not found")
            return jsonify({'error': 'User not found'}), 404

        # Create the new task
        new_task = Task(
            task=data['task'],
            description=data.get('description', ''),
            priority=data.get('priority', 'low'),
            status=data.get('status', True),
            task_date=data.get('task_date', ''),
            user_id=data['user_id']
        )

        db.session.add(new_task)
        db.session.commit()

        logging.info(f"Task '{new_task.task}' added successfully for User {data['user_id']}")
        return jsonify({'message': 'Task added successfully', 'task_id': new_task.id}), 201

    except Exception as e:
        logging.error(f"Error adding task: {e}")
        db.session.rollback()
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
            'priority': t.priority,
            'status': t.status,
            'task_date': t.task_date,
            'user_id': t.user_id
        } for t in tasks]

        return jsonify(task_list), 200
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task."""
    try:
        task = Task.query.get(task_id)
        if not task:
            logging.warning(f"Task {task_id} not found")
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        task.task = data.get('task', task.task)
        task.description = data.get('description', task.description)
        task.priority = data.get('priority', task.priority)
        task.status = data.get('status', task.status)

        db.session.commit()

        logging.info(f"Task {task_id} updated successfully")
        return jsonify({'message': 'Task updated successfully'}), 200

    except Exception as e:
        logging.error(f"Error updating task {task_id}: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    try:
        task = Task.query.get(task_id)
        if not task:
            logging.warning(f"Task {task_id} not found")
            return jsonify({'error': 'Task not found'}), 404

        db.session.delete(task)
        db.session.commit()

        logging.info(f"Task {task_id} deleted successfully")
        return jsonify({'message': 'Task deleted successfully'}), 200

    except Exception as e:
        logging.error(f"Error deleting task {task_id}: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
