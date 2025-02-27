from flask import Flask, render_template, request, jsonify 
from datetime import datetime
import uuid

app = Flask(__name__)

# Hardcoded user data for now
login_database = {
    "user1": {"username": "user1", "password": "password123"},
    "user2": {"username": "user2", "password": "mypassword"}
}

# sample equipment data
equipment_database = [
    {'id': str(uuid.uuid4()),'type': 'computer1', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '10'},
    {'id': str(uuid.uuid4()),'type': 'computer2', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '9'},
    {'id': str(uuid.uuid4()),'type': 'computer3', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '8'},
]

# sample equipment history data
equipment_history = {
    "computer1": [
        {"user": "Alice", "date": "2024-01-10", "status": "Checked Out"},
        {"user": "Bob", "date": "2024-02-05", "status": "Reserved"}
    ],
    "computer2": [
        {"user": "Charlie", "date": "2024-01-15", "status": "Checked Out"},
        {"user": "David", "date": "2024-02-10", "status": "Reserved"}
    ],
    "computer3": [
        {"user": "Eve", "date": "2024-01-20", "status": "Checked Out"},
        {"user": "Frank", "date": "2024-02-15", "status": "Reserved"}
    ]
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in login_database:
            return render_template('register.html', error='Username already exists')
        else:
            login_database[username] = {"username": username, "password": password}
            return render_template('register.html', success='User registered successfully')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = login_database.get(username)
        if user and user['password'] == password:
            return render_template('dashboard.html', username=username, equipment=equipment_database)
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', equipment=equipment_database)

@app.route('/add_equipment', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        new_equipment = {
            'id': str(uuid.uuid4()),
            'type': request.form.get('type'),
            'description': request.form.get('description'),
            'availability': request.form.get('availability'),
            'quality': request.form.get('quality')
        }
        equipment_database.append(new_equipment)  # Add to the database
        return render_template('dashboard.html', equipment=equipment_database, success="Equipment added successfully!")
    return render_template('add_equipment.html')

@app.route('/remove_equipment', methods=['GET', 'POST'])
def remove_equipment():
    if request.method == 'POST':
        id_to_remove = request.form.get('id')
        global equipment_database
        equipment_database = [item for item in equipment_database if item['id'] != id_to_remove]
        return render_template('dashboard.html', equipment=equipment_database, success="Equipment removed successfully!")

    selected_id = request.args.get('id')  # Get selected ID from the link
    return render_template('remove_equipment.html', equipment=equipment_database, selected_id=selected_id)    

@app.route('/equipment_history/<equipment_type>')
def equipment_detail(equipment_type):
    # Find the equipment details
    equipment_info = next((item for item in equipment_database if item["type"] == equipment_type), None)

    # Get the history of checkouts and reservations
    history = equipment_history.get(equipment_type, [])

    if not equipment_info:
        return "Equipment not found", 404

    return render_template('equipment.html', equipment=equipment_info, history=history)

@app.route('/reservations')
def reservations():
    return render_template('reservations.html', current_year=datetime.now().year, current_month=datetime.now().month)

if __name__ == '__main__':
    app.run(debug=True)