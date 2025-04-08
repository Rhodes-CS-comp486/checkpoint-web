from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import uuid
import requests
import secrets


app = Flask(__name__)

#API_BASE_URL = "http://localhost:8000"
API_BASE_URL = "http://10.20.47.145:8000/" #connection to jewels computer
app.secret_key = secrets.token_hex(32)


def get_user(user_id):
    res = requests.get(f"{API_BASE_URL}/users/{user_id}")
    return res.json() if res.status_code == 200 else None

def get_users():
    res = requests.get(f"{API_BASE_URL}/users")
    return res.json() if res.status_code == 200 else []

def get_equipment():
    res = requests.get(f"{API_BASE_URL}/equipment")
    return res.json() if res.status_code == 200 else []

def get_reservations():
    res = requests.get(f"{API_BASE_URL}/reservations")
    return res.json() if res.status_code == 200 else {}

def get_equipment_history(equipment_type):
    res = requests.get(f"{API_BASE_URL}/equipment_history/{equipment_type}")
    return res.json() if res.status_code == 200 else []

"""
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

""" #Hardcoded equipment data

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        full_name = request.form.get('full_name')      

        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "user_id": str(uuid.uuid4()),
            "hashed_password": password,
            "admin": False
        }

        response = requests.put(f"{API_BASE_URL}/users/", json=user_data)

        if response.status_code == 200:
            return render_template('register.html', success="User registered successfully")
        elif response.status_code == 422:
            error_message = response.json().get('detail', 'Validation error')
            return render_template('register.html', error=error_message)
        else:
            return render_template('register.html', error=f"Error: {response.text}")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        data = {"username": username, "password": password}

        try:
            response = requests.post(f"{API_BASE_URL}/token", data=data)
            response.raise_for_status()

            response_data = response.json()
            token = response_data.get("access_token")
            user_id = response_data.get("user_id")

            #there is an issue with how the user_id is being returned from the API. 
            #I left the if only checking for the token and it worked but it couldn't find the user_id
            #we need to do something to get the user_id from the token i think this is an our end problem
            if token and user_id:
                session["token"] = token
                session["user_id"] = user_id

                user = get_user(user_id)
                if not user:
                    return render_template('login.html', error="User not found")

                return redirect(url_for('dashboard', user_id=user_id))
            else:
                return render_template('login.html', error="Invalid credentials")
        except requests.exceptions.RequestException as e:
            return render_template('login.html', error=f"Login failed: {str(e)}")

    return render_template('login.html')


@app.route('/admin/<user_id>', methods=['GET', 'POST'])
def admin_panel(user_id):
    current_user = get_user(user_id)
    if not current_user or not current_user["admin"]:
        return "Unauthorized", 403

    if request.method == 'POST':
        target_username = request.form.get('username')
        action = request.form.get('action')
        users = get_users()
        target_user = next((u for u in users if u["username"] == target_username), None)

        if target_user and target_user["username"] != current_user["username"]:
            target_user["admin"] = (action == "promote")
            requests.put(f"{API_BASE_URL}/users/{target_user['user_id']}", json=target_user)

    return render_template("admin.html", user_id=user_id, users=get_users())


@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    username = user["username"]
    is_admin = user["admin"]

    equipment_database = get_equipment()
    reservations_database = get_reservations()

    today_str = datetime.today().strftime("%Y-%m-%d")
    reserved_today = set(res["equipment"] for res in reservations_database.get(today_str, []))

    for item in equipment_database:
        item["availability"] = False if item["type"] in reserved_today else True

    return render_template('dashboard.html', username=username, user_id=user_id, equipment=equipment_database, is_admin=is_admin)


@app.route('/admin/generate_pdf/<user_id>', methods=['POST'])
def generate_pdf(user_id):
    current_user = get_user(user_id)
    if not current_user or not current_user["admin"]:
        return "Unauthorized", 403

    report_type = request.form.get('report_type')
    selected_value = request.form.get('selected_value')
    report_data = []

    if report_type == "user":
        users = get_users()
        username = selected_value
        for equipment in get_equipment():
            history = get_equipment_history(equipment["type"])
            for record in history:
                if record["user"] == username:
                    report_data.append((record["user"], equipment["type"], record["date"], record["status"]))

    elif report_type == "equipment":
        history = get_equipment_history(selected_value)
        for record in history:
            report_data.append((record["user"], selected_value, record["date"], record["status"]))

    elif report_type == "all_users":
        for equipment in get_equipment():
            history = get_equipment_history(equipment["type"])
            for record in history:
                report_data.append((record["user"], equipment["type"], record["date"], record["status"]))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(200, height - 40, "Usage History Report")
    pdf.setFont("Helvetica", 10)
    y = height - 80
    pdf.drawString(50, y, "User")
    pdf.drawString(150, y, "Equipment")
    pdf.drawString(300, y, "Date")
    pdf.drawString(400, y, "Status")
    y -= 20

    for user, equip, date, status in report_data:
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, user)
        pdf.drawString(150, y, equip)
        pdf.drawString(300, y, date)
        pdf.drawString(400, y, status)
        y -= 15

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="usage_report.pdf", mimetype='application/pdf')


@app.route('/add_equipment/<user_id>', methods=['GET', 'POST'])
def add_equipment(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        equipment_type = request.form.get('type')
        description = request.form.get('description')
        quality = request.form.get('quality')

        if not equipment_type or not description or not quality:
            return render_template('add_equipment.html', user_id=user_id, error="All fields are required.")

        new_equipment = {
            'type': equipment_type,
            'description': description,
            'quality': quality
        }
        requests.post(f"{API_BASE_URL}/equipment", json=new_equipment)
        return redirect(url_for('dashboard', user_id=user_id))

    return render_template('add_equipment.html', user_id=user_id)


@app.route('/remove_equipment/<user_id>', methods=['GET', 'POST'])
def remove_equipment(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    equipment_database = get_equipment()

    if request.method == 'POST':
        id_to_remove = request.form.get('id')
        if not any(item['id'] == id_to_remove for item in equipment_database):
            return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, error="Equipment not found.")

        requests.delete(f"{API_BASE_URL}/equipment/{id_to_remove}")
        return redirect(url_for('dashboard', user_id=user_id))

    selected_id = request.args.get('id')
    return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_database, selected_id=selected_id)


@app.route('/equipment_history/<user_id>/<equipment_type>')
def equipment_detail(user_id, equipment_type):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    equipment_database = get_equipment()
    equipment_info = next((item for item in equipment_database if item["type"] == equipment_type), None)
    history = get_equipment_history(equipment_type)

    if not equipment_info:
        return "Equipment not found", 404

    return render_template('equipment.html', user_id=user_id, equipment=equipment_info, history=history)


@app.route('/reservations/<user_id>')
def reservations(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    equipment_database = get_equipment()
    reservations_database = get_reservations()

    events = []
    for date_str, res_list in reservations_database.items():
        for res in res_list:
            events.append({
                "title": f"{res['equipment']} ({res['user']})",
                "start": date_str
            })

    return render_template('reservations.html', user_id=user_id, equipment=equipment_database, reservations=reservations_database, calendar_events=events)


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

    reservations_database = get_reservations()
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        for res in reservations_database.get(date_str, []):
            if res["equipment"] == equipment_type:
                return f"{equipment_type} is already reserved on {date_str}", 400
        current += timedelta(days=1)

    user = get_user(user_id)
    if not user:
        return "User not found", 404

    username = user["username"]
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        reservation_data = {
            "user_id": user_id,
            "equipment": equipment_type,
            "start_date": date_str,
            "end_date": date_str
        }
        history_data = {
            "equipment_type": equipment_type,
            "user": username,
            "date": date_str,
            "status": "Reserved"
        }

        requests.post(f"{API_BASE_URL}/reservations", json=reservation_data)
        requests.post(f"{API_BASE_URL}/equipment_history", json=history_data)

        current += timedelta(days=1)

    return redirect(url_for('reservations', user_id=user_id))



@app.route('/remove_reservation/<user_id>', methods=['POST'])
def remove_reservation(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    data = {
        "user_id": user_id,
        "equipment": request.form.get('equipment'),
        "date": request.form.get('date')
    }
    res = requests.delete(f"{API_BASE_URL}/reservations", json=data)
    if res.status_code != 200:
        return res.text, res.status_code
    return redirect(url_for('reservations', user_id=user_id))


@app.route('/user_history/<user_id>')
def user_history(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    username = user["username"]
    user_transactions = []
    equipment_database = get_equipment()

    for item in equipment_database:
        history = get_equipment_history(item["type"])
        for record in history:
            if record["user"] == username:
                user_transactions.append({
                    "equipment_type": item["type"],
                    "date": record["date"],
                    "status": record["status"],
                    "availability": item.get("availability", "Unknown")
                })

    return render_template('user_history.html', username=username, user_id=user_id, history=user_transactions)


@app.route('/checkout/<user_id>/<equipment_type>', methods=['GET', 'POST'])
def checkout_equipment(user_id, equipment_type):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    username = user["username"]
    today = datetime.today().date()
    max_days = 7

    reservations_database = get_reservations()

    for i in range(1, 8):
        check_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        for res in reservations_database.get(check_date, []):
            if res["equipment"] == equipment_type:
                max_days = i - 1
                break
        if max_days < i:
            break

    if max_days == 0:
        return render_template("checkout.html", user_id=user_id, equipment_type=equipment_type, max_days=0, error="This item cannot be checked out right now due to an upcoming reservation.")

    if request.method == 'POST':
        days = int(request.form.get('days'))

        if days < 1 or days > max_days:
            return render_template("checkout.html", user_id=user_id, equipment_type=equipment_type, max_days=max_days, error=f"You can only check out for up to {max_days} day(s) without interfering with existing reservations.")

        for i in range(days):
            checkout_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            requests.post(f"{API_BASE_URL}/reservations", json={
                "user_id": user_id,
                "equipment": equipment_type,
                "start_date": checkout_date,
                "end_date": checkout_date
            })
            requests.post(f"{API_BASE_URL}/equipment_history", json={
                "equipment_type": equipment_type,
                "user": username,
                "date": checkout_date,
                "status": "Checked Out"
            })

        success_message = f"{equipment_type} successfully checked out for {days} day(s)."
        return render_template("checkout.html", user_id=user_id, equipment_type=equipment_type, max_days=0, success=success_message)

    return render_template("checkout.html", user_id=user_id, equipment_type=equipment_type, max_days=max_days)


if __name__ == '__main__':
    app.run(debug=True)