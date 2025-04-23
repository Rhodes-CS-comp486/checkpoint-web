from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import uuid
import requests
import secrets


app = Flask(__name__)

API_BASE_URL = "http://localhost:8000"
#API_BASE_URL = "http://10.20.47.145:8000/" #connection to Jules computer
app.secret_key = secrets.token_hex(32)


def get_all_users():
    headers = {
        "Authorization": f"Bearer {session['token']}"
    }
    res = requests.get(f"{API_BASE_URL}/users/all", headers=headers)
    print("[DEBUG] /users/all response:", res.status_code)
    return res.json() if res.status_code == 200 else []

def get_current_user():
    headers = {
        "Authorization": f"Bearer {session['token']}"
    }

    res = requests.get(f"{API_BASE_URL}/users/me", headers=headers)
    print("[DEBUG] /users/me response:", res.status_code, res.text)

    return res.json() if res.status_code == 200 else None

def get_equipment():
    headers = {
        "Authorization": f"Bearer {session['token']}"
    }
    res = requests.get(f"{API_BASE_URL}/items/filter", headers=headers)
    print("[DEBUG] Equipment response:", res.status_code, res.text)
    return res.json() if res.status_code == 200 else []

def get_all_borrows():
    headers = {
        "Authorization": f"Bearer {session['token']}"
    }
    res = requests.get(f"{API_BASE_URL}/users/all/borrows", headers=headers)
    print("[DEBUG] /users/all/borrows response:", res.status_code)
    return res.json() if res.status_code == 200 else []

def get_equipment_by_id(item_id):
    headers = {"Authorization": f"Bearer {session['token']}"}
    res = requests.get(f"{API_BASE_URL}/items/{item_id}", headers=headers)
    print("[DEBUG] Equipment details:", res.status_code)
    return res.json() if res.status_code == 200 else None

def get_equipment_history(equipment_type):
    res = requests.get(f"{API_BASE_URL}/equipment_history/{equipment_type}")
    return res.json() if res.status_code == 200 else []

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

            if not token:
                return render_template('login.html', error="Invalid credentials")

            # Store token in session
            session["token"] = token

            # Get current user info from /users/me
            user = get_current_user()

            if not user:
                return render_template('login.html', error="Failed to fetch user data")

            user_id = user.get("user_id")  # Adjust this if your API uses 'id' instead
            session["user_id"] = user_id

            return redirect(url_for('dashboard', user_id=user_id))

        except requests.exceptions.RequestException as e:
            return render_template('login.html', error=f"Login failed: {str(e)}")

    return render_template('login.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    # Get user info
    user = get_current_user()
    if not user:
        return "User not found or not authenticated", 404

    username = user.get("username")
    is_admin = user.get("is_admin") or user.get("admin") or False  # use correct key from /users/me

    # Get available equipment
    equipment = get_equipment()

    # TODO: Get reservation info if needed
    # For now, we'll assume all equipment is available unless the API tracks reservations

    return render_template(
        'dashboard.html',
        username=username,
        user_id=user_id,
        equipment=equipment,
        is_admin=is_admin
    )

@app.route('/admin/<user_id>', methods=['GET', 'POST'])
def admin_panel(user_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    if request.method == 'POST':
        target_username = request.form.get('username')
        action = request.form.get('action')

        if action in ["promote", "demote"]:
            headers = {"Authorization": f"Bearer {session['token']}"}
            elevate_url = f"{API_BASE_URL}/users/{target_username}/elevate"
            
            # Elevate or demote based on action
            if action == "promote":
                res = requests.put(elevate_url, headers=headers)
            elif action == "demote":
                # Assuming your API supports this — if not, you'd need a demotion endpoint
                res = requests.put(elevate_url, headers=headers, json={"demote": True})
            
            print(f"[DEBUG] {action.capitalize()} {target_username}: {res.status_code} {res.text}")

    users = get_all_users()
    borrows = get_all_borrows()

    # Format combined log if needed
    combined_log = []
    for record in borrows:
        combined_log.append({
            "user": record.get("username"),
            "equipment": record.get("item_id") or record.get("item_name", "Unknown"),
            "date": record.get("date_borrowed", "N/A"),
            "status": "Borrowed" if not record.get("returned") else "Returned"
        })

    combined_log.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "admin.html",
        user_id=user_id,
        users=users,
        log=combined_log
    )

@app.route('/admin/user_details/<admin_id>/<target_user_id>')
def admin_user_details(admin_id, target_user_id):
    # Make sure the current user is an admin
    current_user = get_current_user()
    if not current_user or not current_user.get("admin"):
        return "Unauthorized", 403

    # Get all users to find the target user
    users = get_all_users()
    target_user = next((u for u in users if u["user_id"] == target_user_id), None)
    
    if not target_user:
        return "User not found", 404

    # Get full borrow history and filter by user
    all_borrows = get_all_borrows()
    user_history = [
        {
            "equipment": borrow.get("item_id", "Unknown"),
            "date": borrow.get("date_borrowed", "N/A"),
            "status": "Returned" if borrow.get("returned") else "Borrowed"
        }
        for borrow in all_borrows
        if borrow.get("user_id") == target_user_id
    ]

    user_history.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        'admin_user_details.html',
        admin_id=admin_id,
        username=target_user.get("username"),
        is_admin=target_user.get("admin"),
        history=user_history
    )

@app.route('/admin/generate_pdf/<user_id>', methods=['POST'])
def generate_pdf(user_id):
    current_user = get_current_user()
    if not current_user or not current_user.get("admin"):
        return "Unauthorized", 403

    report_type = request.form.get('report_type')
    selected_value = request.form.get('selected_value', '').strip()

    borrows = get_all_borrows()
    report_data = []

    if report_type == "user":
        report_data = [
            (b["username"], b["item_id"], b["date_borrowed"], "Returned" if b.get("returned") else "Borrowed")
            for b in borrows if b.get("username", "").lower() == selected_value.lower()
        ]
    elif report_type == "equipment":
        report_data = [
            (b["username"], b["item_id"], b["date_borrowed"], "Returned" if b.get("returned") else "Borrowed")
            for b in borrows if b.get("item_id", "").lower() == selected_value.lower()
        ]
    elif report_type == "all_users":
        report_data = [
            (b["username"], b["item_id"], b["date_borrowed"], "Returned" if b.get("returned") else "Borrowed")
            for b in borrows
        ]

    # Generate PDF
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

    for user, equipment, date, status in report_data:
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, user)
        pdf.drawString(150, y, equipment)
        pdf.drawString(300, y, date)
        pdf.drawString(400, y, status)
        y -= 15

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="usage_report.pdf", mimetype='application/pdf')

@app.route('/add_equipment/<user_id>', methods=['GET', 'POST'])
def add_equipment(user_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    if request.method == 'POST':
        name = request.form.get('type')
        description = request.form.get('description')
        model = request.form.get('model')
        location = request.form.get('location')
        availability_str = request.form.get('availability', 'true')
        availability = availability_str.lower() == 'true'
        quality = request.form.get('quality')  # Optional
        borrow_period_days = "P7D"  # Default
        status = "Available"
        damage = ""

        if not name or not description or not model or not location:
            return render_template('add_equipment.html', user_id=user_id, error="All fields are required.")

        item_id = str(uuid.uuid4())

        new_equipment = {
            "id": item_id,
            "name": name,
            "description": description,
            "model": model,
            "location": location,
            "availability": availability,
            "borrow_period_days": borrow_period_days,
            "status": status,
            "damage": damage
        }

        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.put(f"{API_BASE_URL}/items/add/{item_id}", json=new_equipment, headers=headers)

        print("[DEBUG] Payload sent:", new_equipment)
        print("[DEBUG] Response:", response.status_code, response.text)

        if response.status_code == 200:
            return redirect(url_for('dashboard', user_id=user_id))
        else:
            return render_template('add_equipment.html', user_id=user_id, error="Failed to add equipment.")

    return render_template('add_equipment.html', user_id=user_id)

@app.route('/remove_equipment/<user_id>', methods=['GET', 'POST'])
def remove_equipment(user_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    equipment_list = get_equipment()

    if request.method == 'POST':
        item_id = request.form.get('item_id')

        if not item_id:
            return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_list, error="No item selected.")

        headers = {"Authorization": f"Bearer {session['token']}"}
        res = requests.delete(f"{API_BASE_URL}/items/delete/{item_id}", headers=headers)

        if res.status_code == 200:
            return redirect(url_for('dashboard', user_id=user_id))
        else:
            return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_list, error="Failed to remove equipment.")

    return render_template('remove_equipment.html', user_id=user_id, equipment=equipment_list)

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

    if is_admin:
        table_reservations = reservations_database
    else:
        table_reservations = {}
        for date, res_list in reservations_database.items():
            user_res = [r for r in res_list if r["user"] == user_id]
            if user_res:
                table_reservations[date] = user_res

    return render_template(
        'reservations.html',
        user_id=user_id,
        is_admin=is_admin,
        equipment=equipment_database,
        reservations=table_reservations,
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
    date = request.form.get('date')
    equipment_type = request.form.get('equipment')

    if not date or not equipment_type:
        return "Missing required fields", 400

    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user:
        return "User not found", 404
    is_admin = user["admin"]

    if date in reservations_database:
        if is_admin:
            # Admin can remove any reservation for that equipment/date
            reservations_database[date] = [
                res for res in reservations_database[date]
                if res["equipment"] != equipment_type
            ]
        else:
            # Regular user can only remove their own
            reservations_database[date] = [
                res for res in reservations_database[date]
                if not (res["equipment"] == equipment_type and res["user"] == user_id)
            ]

        if not reservations_database[date]:
            del reservations_database[date]

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


@app.route('/checkin/<user_id>/<equipment_type>', methods=['POST'])
def checkin_equipment(user_id, equipment_type):
    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user:
        return "User not found", 404
    username = user["username"]

    today = datetime.today().date()
    returned_any = False

    for i in range(7):
        check_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        res_list = reservations_database.get(check_date, [])

        new_res_list = []
        for res in res_list:
            if res["equipment"] == equipment_type and res["user"] == user_id:
                returned_any = True
                # Add return record
                if equipment_type not in equipment_history:
                    equipment_history[equipment_type] = []
                equipment_history[equipment_type].append({
                    "user": username,
                    "date": check_date,
                    "status": "Returned to Inventory"
                })
            else:
                new_res_list.append(res)

        if new_res_list:
            reservations_database[check_date] = new_res_list
        else:
            reservations_database.pop(check_date, None)

    if returned_any:
        return redirect(url_for('dashboard', user_id=user_id))
    else:
        return "You cannot check in this equipment — it is not checked out under your account.", 403


if __name__ == '__main__':
    app.run(debug=True)