from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# Hardcoded user data
login_database = {
    "user1": {"id": str(uuid.uuid4()), "username": "user1", "password": "password123", "admin": False},
    "user2": {"id": str(uuid.uuid4()), "username": "user2", "password": "mypassword", "admin": False},
    "user3": {"id": str(uuid.uuid4()), "username": "user3", "password": "12345", "admin": False},
    "admin": {"id": str(uuid.uuid4()), "username": "admin", "password": "admin", "admin": True},
}

# Equipment data with boolean availability
equipment_database = [
    {'id': str(uuid.uuid4()), 'type': 'computer1', 'description': 'Dell Latitude 7400', 'availability': True, 'quality': '10'},
    {'id': str(uuid.uuid4()), 'type': 'computer2', 'description': 'Dell Latitude 7400', 'availability': True, 'quality': '9'},
    {'id': str(uuid.uuid4()), 'type': 'computer3', 'description': 'Dell Latitude 7400', 'availability': True, 'quality': '8'},
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

reservations_database = {}

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
            login_database[username] = {
                "id": str(uuid.uuid4()),
                "username": username,
                "password": password,
                "admin": False
            }
            return render_template('register.html', success='User registered successfully')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = login_database.get(username)

        if user and user['password'] == password:
            return redirect(url_for('dashboard', user_id=user['id']))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    username = next((user["username"] for user in login_database.values() if user["id"] == user_id), None)
    if not username:
        return "User not found", 404

    today_str = datetime.today().strftime("%Y-%m-%d")
    reserved_today = set(res["equipment"] for res in reservations_database.get(today_str, []))

    for item in equipment_database:
        item["availability"] = False if item["type"] in reserved_today else True

    return render_template('dashboard.html', username=username, user_id=user_id, equipment=equipment_database)

@app.route('/add_equipment/<user_id>', methods=['GET', 'POST'])
def add_equipment(user_id):
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        equipment_type = request.form.get('type')
        description = request.form.get('description')
        quality = request.form.get('quality')

        if not equipment_type or not description or not quality:
            return render_template('add_equipment.html', user_id=user_id, error="All fields are required.")

        new_equipment = {
            'id': str(uuid.uuid4()),
            'type': equipment_type,
            'description': description,
            'availability': True,  # default to available
            'quality': quality
        }
        equipment_database.append(new_equipment)
        return redirect(url_for('dashboard', user_id=user_id))

    return render_template('add_equipment.html', user_id=user_id)

@app.route('/remove_equipment/<user_id>', methods=['GET', 'POST'])
def remove_equipment(user_id):
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        id_to_remove = request.form.get('id')
        global equipment_database
        if not any(item['id'] == id_to_remove for item in equipment_database):
            return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, error="Equipment not found.")

        equipment_database = [item for item in equipment_database if item['id'] != id_to_remove]
        return redirect(url_for('dashboard', user_id=user_id))

    selected_id = request.args.get('id')
    return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, selected_id=selected_id)

@app.route('/equipment_history/<user_id>/<equipment_type>')
def equipment_detail(user_id, equipment_type):
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    equipment_info = next((item for item in equipment_database if item["type"] == equipment_type), None)
    history = equipment_history.get(equipment_type, [])

    if not equipment_info:
        return "Equipment not found", 404

    return render_template('equipment.html', user_id=user_id, equipment=equipment_info, history=history)

@app.route('/reservations/<user_id>', methods=['GET', 'POST'])
def reservations(user_id):
    user = next((user for user in login_database.values() if user["id"] == user_id), None)
    if not user:
        return "User not found", 404

    events = []
    for date_str, res_list in reservations_database.items():
        for res in res_list:
            events.append({
                "title": f"{res['equipment']} ({res['user']})",
                "start": date_str
            })

    return render_template(
        'reservations.html',
        user_id=user_id,
        equipment=equipment_database,
        reservations=reservations_database,
        calendar_events=events
    )

@app.route('/make_reservation/<user_id>', methods=['POST'])
def make_reservation(user_id):
    equipment_type = request.form.get('equipment')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not equipment_type or not start_date or not end_date:
        return "Missing required fields", 400

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format", 400

    if start > end:
        return "Start date must be before or equal to end date", 400

    # Check for overlapping reservations
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        for res in reservations_database.get(date_str, []):
            if res["equipment"] == equipment_type:
                return f"{equipment_type} is already reserved on {date_str}", 400
        current += timedelta(days=1)

    # Add reservation and history records
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        # Add to reservations
        if date_str not in reservations_database:
            reservations_database[date_str] = []
        reservations_database[date_str].append({
            "equipment": equipment_type,
            "user": user_id
        })

        # Get username and add to equipment history
        user = next((u for u in login_database.values() if u["id"] == user_id), None)
        if user:
            username = user["username"]
            if equipment_type not in equipment_history:
                equipment_history[equipment_type] = []
            equipment_history[equipment_type].append({
                "user": username,
                "date": date_str,
                "status": "Reserved"
            })

        current += timedelta(days=1)

    return redirect(url_for('reservations', user_id=user_id))

@app.route('/remove_reservation/<user_id>', methods=['POST'])
def remove_reservation(user_id):
    date = request.form.get('date')
    equipment_type = request.form.get('equipment')
    if not date or not equipment_type:
        return "Missing required fields", 400

    if date in reservations_database:
        reservations_database[date] = [res for res in reservations_database[date] if not (res["equipment"] == equipment_type and res["user"] == user_id)]
        if not reservations_database[date]:
            del reservations_database[date]

    return redirect(url_for('reservations', user_id=user_id))

@app.route('/user_history/<user_id>')
def user_history(user_id):
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