from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:cloudy19@localhost:5432/Assignment'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app, resources={r"*": {"origins": "http://localhost:3000"}})

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = db.Column(db.Date)
    entity_name = db.Column(db.String(255))
    task_type = db.Column(db.String(255))
    time = db.Column(db.Time)
    contact_person = db.Column(db.String(255))
    notes = db.Column(db.Text,nullable=True)
    status = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TaskAssignment(db.Model):
    __tablename__ = 'taskassignments'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())

# Initialize the database
with app.app_context():
    db.create_all()

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Task Management API"})

@app.route('/tasks/<uuid:taskId>', methods=['PUT'])
def update_task_notes(taskId):
    data = request.get_json()
    notes = data.get('notes')

    # Find the task by taskId
    task = Task.query.get_or_404(taskId)

    # Update the notes field if provided in the request
    if notes is not None:
        task.notes = notes

    db.session.commit()

    return jsonify({"message": "Task notes updated successfully"}), 200

# User Endpoints
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/users/<uuid:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

# Task Endpoints
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    # Convert date and time from string to date and time objects
    date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
    time = datetime.datetime.strptime(data['time'], '%H:%M').time()  # Adjust format to %H:%M
    # Create new task instance
    new_task = Task(
        entity_name=data['entity_name'],
        status=data['status'],
        date=date,
        time=time,
        contact_person=data['contact_person'],
        notes=data['notes'],
        task_type=data['task_type']
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks/<uuid:id>', methods=['GET'])
def get_task(id):
    task = Task.query.get_or_404(id)
    return jsonify(task.to_dict())

@app.route('/tasks/<uuid:id>', methods=['PUT'])
def update_task(id):
    data = request.get_json()
    task = Task.query.get_or_404(id)
    task.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
    task.entity_name = data['entity_name']
    task.task_type = data['task_type']
    task.time = datetime.datetime.strptime(data['time'], '%H:%M').time()
    task.contact_person = data['contact_person']
    task.notes = data.get('notes')
    task.status = data['status']
    db.session.commit()
    return jsonify({"message": "Task updated"})

@app.route('/tasks/<uuid:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"})

@app.route('/tasks/<uuid:id>/assign', methods=['POST'])
def assign_task_to_user(id):
    data = request.get_json()
    task = Task.query.get_or_404(id)
    user = User.query.get_or_404(data['user_id'])
    assignment = TaskAssignment(task_id=task.id, user_id=user.id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"message": "Task assigned to user"}), 201

@app.route('/tasks/<uuid:id>/assign/<uuid:user_id>', methods=['DELETE'])
def remove_user_from_task(id, user_id):
    assignment = TaskAssignment.query.filter_by(task_id=id, user_id=user_id).first_or_404()
    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "User removed from task"})

# Helper to convert model object to dictionary
def model_to_dict(self):
    def convert_value(value):
        if isinstance(value, (datetime.date, datetime.time)):
            return value.isoformat()
        return value

    return {column.name: convert_value(getattr(self, column.name)) for column in self.__table__.columns}

User.to_dict = model_to_dict
Task.to_dict = model_to_dict
TaskAssignment.to_dict = model_to_dict

if __name__ == '__main__':
    app.run(debug=True)
