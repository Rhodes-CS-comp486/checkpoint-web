from flask import Flask, render_template, request
app = Flask(__name__)
# Hardcoded user data for now
database = {
    "user1": {"username": "user1", "password": "password123"},
    "user2": {"username": "user2", "password": "mypassword"}
}
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = database.get(username)
        if user and user['password'] == password:
            return render_template('dashboard.html', username=username)
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
if __name__ == '__main__':
    app.run(debug=True)