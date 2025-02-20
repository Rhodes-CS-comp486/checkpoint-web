from flask import Flask, render_template, request, jsonify 

app = Flask(__name__)

# Hardcoded user data for now
login_database = {
    "user1": {"username": "user1", "password": "password123"},
    "user2": {"username": "user2", "password": "mypassword"}
}

# sample equipment data
equipment_database = [
    {'type': 'computer1', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '10'},
    {'type': 'computer2', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '9'},
    {'type': 'computer3', 'description': 'Dell Latitude 7400', 'availability': 'available', 'quality': '8'},
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
    
if __name__ == '__main__':
    app.run(debug=True)