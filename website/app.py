from flask import Flask, render_template, request, jsonify 
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

if __name__ == '__main__':
    app.run(debug=True)