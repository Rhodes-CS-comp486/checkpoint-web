from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import uuid

app = Flask(__name__)

# Hardcoded user data for now
login_database = {
    "user1": {"id": str(uuid.uuid4()), "username": "user1", "password": "password123"},
    "user2": {"id": str(uuid.uuid4()), "username": "user2", "password": "mypassword"},
    "user3": {"id": str(uuid.uuid4()), "username": "user3", "password": "12345"}
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
        {"user": "user1", "date": "2024-01-15", "status": "Checked Out"},
        {"user": "user1", "date": "2024-01-20", "status": "Returned to Inventory"},
        {"user": "user2", "date": "2024-02-10", "status": "Checked Out"},
        {"user": "user2", "date": "2024-02-15", "status": "Returned to Inventory"},
        {"user": "user3", "date": "2024-03-20", "status": "Checked Out"},
        {"user": "user3", "date": "2024-03-25", "status": "Returned to Inventory"}
    ],
    "computer2": [
        {"user": "user1", "date": "2024-01-15", "status": "Checked Out"},
        {"user": "user1", "date": "2024-01-20", "status": "Returned to Inventory"},
        {"user": "user2", "date": "2024-02-10", "status": "Checked Out"},
        {"user": "user2", "date": "2024-02-15", "status": "Returned to Inventory"},
        {"user": "user3", "date": "2024-03-20", "status": "Checked Out"},
        {"user": "user3", "date": "2024-03-25", "status": "Returned to Inventory"}
    ],
    "computer3": [
        {"user": "user1", "date": "2024-01-15", "status": "Checked Out"},
        {"user": "user1", "date": "2024-01-20", "status": "Returned to Inventory"},
        {"user": "user2", "date": "2024-02-10", "status": "Checked Out"},
        {"user": "user2", "date": "2024-02-15", "status": "Returned to Inventory"},
        {"user": "user3", "date": "2024-03-20", "status": "Checked Out"},
        {"user": "user3", "date": "2024-03-25", "status": "Returned to Inventory"}
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
            # Redirect to dashboard with user_id in the URL
            return redirect(url_for('dashboard', user_id=user['id']))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    # Find the username using user_id
    username = next((user["username"] for user in login_database.values() if user["id"] == user_id), None)

    if not username:
        return "User not found", 404

    return render_template('dashboard.html', username=username, user_id=user_id, equipment=equipment_database)

@app.route('/add_equipment/<user_id>', methods=['GET', 'POST'])
def add_equipment(user_id):
    # Validate user_id exists
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        equipment_type = request.form.get('type')
        description = request.form.get('description')
        availability = request.form.get('availability')
        quality = request.form.get('quality')

        # Validate inputs
        if not equipment_type or not description or not availability or not quality:
            return render_template('add_equipment.html', user_id=user_id, error="All fields are required.")

        new_equipment = {
            'id': str(uuid.uuid4()),
            'type': equipment_type,
            'description': description,
            'availability': availability,
            'quality': quality
        }
        equipment_database.append(new_equipment)

        return redirect(url_for('dashboard', user_id=user_id))

    return render_template('add_equipment.html', user_id=user_id)

@app.route('/remove_equipment/<user_id>', methods=['GET', 'POST'])
def remove_equipment(user_id):
    # Validate user_id exists
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        id_to_remove = request.form.get('id')

        # Check if the ID exists
        global equipment_database
        if not any(item['id'] == id_to_remove for item in equipment_database):
            return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, error="Equipment not found.")

        # Remove the equipment
        equipment_database = [item for item in equipment_database if item['id'] != id_to_remove]

        return redirect(url_for('dashboard', user_id=user_id))

    selected_id = request.args.get('id')
    return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, selected_id=selected_id)

@app.route('/equipment_history/<user_id>/<equipment_type>')
def equipment_detail(user_id, equipment_type):
    # Validate user_id exists
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    # Get equipment details
    equipment_info = next((item for item in equipment_database if item["type"] == equipment_type), None)

    # Get the history of checkouts and reservations
    history = equipment_history.get(equipment_type, [])

    if not equipment_info:
        return "Equipment not found", 404

    return render_template('equipment.html', user_id=user_id, equipment=equipment_info, history=history)

@app.route('/reservations/<user_id>')
def reservations(user_id):
    return render_template('reservations.html', user_id=user_id)

@app.route('/user_history/<user_id>')
def user_history(user_id):
    # Validate user_id exists
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404
    
    username = user["username"]
    user_transactions = []

    for equipment_type, records in equipment_history.items():
        for record in records:
            if record["user"] == username:
                equipment_info = next((item for item in equipment_database if item["type"] == equipment_type), None)
                availability = equipment_info["availability"] if equipment_info else "Unknown"

                user_transactions.append({
                    "equipment_type": equipment_type,
                    "date": record["date"],
                    "status": record["status"],
                    "availability": availability
                })

    return render_template('user_history.html', username=username, user_id=user_id, history=user_transactions)

if __name__ == '__main__':
    app.run(debug=True)