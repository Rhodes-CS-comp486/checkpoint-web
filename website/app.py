import qrcode
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
            return render_template('register.html', error=f"Error: Username already exists")

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

            # Save token and user info
            session["token"] = token

            # Now get user info
            user_info_response = requests.get(f"{API_BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            session["user_id"] = user_info["user_id"]
            session["username"] = user_info["username"]
            session["is_admin"] = user_info["admin"]

            # Check if they scanned a QR and need to finish checkout
            if 'pending_checkout_equipment_id' in session:
                equipment_id = session.pop('pending_checkout_equipment_id')
                return redirect(url_for('checkout_equipment', user_id=session['user_id'], equipment_id=equipment_id))

            # Normal dashboard redirect
            return redirect(url_for('dashboard', user_id=session['user_id']))

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

    return render_template(
        'dashboard.html',
        username=username,
        user_id=user_id,
        equipment=equipment,
        is_admin=is_admin
    )


@app.route('/toggle_availability/<user_id>', methods=['POST'])
def toggle_availability(user_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    item_id = request.form.get('item_id')
    current_availability = request.form.get('current_availability') == 'True'

    headers = {"Authorization": f"Bearer {session['token']}"}
    update_data = {
        "availability": not current_availability
    }

    response = requests.put(f"{API_BASE_URL}/items/{item_id}", headers=headers, json=update_data)
    print("[DEBUG] Toggle availability:", response.status_code, response.text)

    return redirect(url_for('dashboard', user_id=user_id))


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

            if action == "promote":
                url = f"{API_BASE_URL}/users/{target_username}/elevate"
            elif action == "demote":
                url = f"{API_BASE_URL}/users/{target_username}/demote"

            res = requests.put(url, headers=headers)
            print(f"[DEBUG] {action.capitalize()} {target_username}: {res.status_code} {res.text}")

    users = get_all_users()
    borrows = get_all_borrows()

    # Format combined log if needed
    combined_log = []
    for record in borrows:
        item_id = record.get("item_id")
        # Call get item API using item_id
        item = requests.get(f"{API_BASE_URL}/items/{item_id}").json() if item_id else {}

        equipment_name = item.get("name", "Unknown Equipment")
        combined_log.append({
            "user": record.get("username"),
            "equipment": equipment_name,
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
    admin = get_current_user()
    if not admin or not admin.get("admin"):
        return "Unauthorized", 403

    users = get_all_users()
    target_user = next((u for u in users if u["user_id"] == target_user_id), None)

    if not target_user:
        return "User not found", 404

    username = target_user.get("username")
    email = target_user.get("email")
    full_name = target_user.get("full_name")
    is_admin = target_user.get("admin")
    user_id = target_user.get("user_id")

    borrows = get_all_borrows()
    history = []

    for record in borrows:
        if record.get("user_id") == target_user_id or record.get("username") == username:
            item_id = record.get("item_id")
            # Call get item API using item_id
            item = requests.get(f"{API_BASE_URL}/items/{item_id}").json() if item_id else {}

            equipment_name = item.get("name", "Unknown Equipment")
            history.append({
                "equipment": equipment_name,
                "date": record.get("date_borrowed", "Unknown Date"),
                "status": "Borrowed" if not record.get("returned") else "Returned"
            })

    history.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        'admin_user_details.html',
        admin_id=admin_id,
        username=username,
        email=email,
        full_name=full_name,
        user_id=user_id,
        is_admin=is_admin,
        history=history
    )

@app.route('/admin/qrcode/<user_id>/<equipment_id>')
def generate_equipment_qrcode(user_id, equipment_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    equipment_info = get_equipment_by_id(equipment_id)
    if not equipment_info:
        return "Equipment not found", 404

    # Important: use "scan" instead of admin's ID
    checkout_url = url_for('checkout_equipment', user_id="scan", equipment_id=equipment_id, _external=True)

    img = qrcode.make(checkout_url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png', download_name=f"{equipment_info['name']}_qr.png")


@app.route('/admin/generate_qrcode_form/<user_id>', methods=['GET', 'POST'])
def generate_qrcode_form(user_id):
    user = get_current_user()
    if not user or not user.get("admin"):
        return "Unauthorized", 403

    equipment_list = get_equipment()

    if request.method == 'POST':
        selected_equipment_id = request.form.get('equipment_id')
        return redirect(url_for('generate_equipment_qrcode', user_id=user_id, equipment_id=selected_equipment_id))

    return render_template('generate_qrcode.html', user_id=user_id, equipment=equipment_list)


@app.route('/admin/generate_pdf/<user_id>', methods=['POST'])
def generate_pdf(user_id):
    current_user = get_current_user()
    if not current_user or not current_user.get("admin"):
        return "Unauthorized", 403

    report_type = request.form.get('report_type')
    selected_value = request.form.get('selected_value')
    report_data = []

    headers = {"Authorization": f"Bearer {session['token']}"}

    # Case 1: History for a specific user
    if report_type == "user":
        all_users = get_all_users()
        target_user = next((u for u in all_users if u["username"] == selected_value), None)
        if not target_user:
            return f"No such user: {selected_value}", 404
        user_id_lookup = target_user["user_id"]

        borrows = get_all_borrows()
        for record in borrows:
            if record.get("user_id") == user_id_lookup:
                item_id = record.get("item_id")
                item = requests.get(f"{API_BASE_URL}/items/{item_id}", headers=headers).json() if item_id else {}
                item_name = item.get("name", "Unknown Equipment")

                report_data.append((
                    target_user["username"],
                    item_name,
                    record.get("date_borrowed", "N/A"),
                    "Returned" if record.get("returned") else "Borrowed"
                ))

    # Case 2: History for a specific equipment item
    elif report_type == "equipment":
        print("[DEBUG] Looking up equipment:", selected_value)
        item_resp = requests.get(f"{API_BASE_URL}/items/filter", headers=headers, params={"name": selected_value})
        item_data = item_resp.json() if item_resp.status_code == 200 else []

        if not item_data:
            return f"No equipment found with name: {selected_value}", 404

        target_id = item_data[0].get("id")  # Assume exact match on name
        all_borrows = get_all_borrows()
        for record in all_borrows:
            if record.get("item_id") == target_id:
                report_data.append((
                    record.get("username", "Unknown"),
                    selected_value,
                    record.get("date_borrowed", "N/A"),
                    "Returned" if record.get("returned") else "Borrowed"
                ))

    # Case 3: All user transactions
    elif report_type == "all_users":
        all_borrows = get_all_borrows()
        for record in all_borrows:
            item_id = record.get("item_id")
            item = requests.get(f"{API_BASE_URL}/items/{item_id}", headers=headers).json() if item_id else {}
            item_name = item.get("name", "Unknown Equipment")

            report_data.append((
                record.get("username", "Unknown"),
                item_name,
                record.get("date_borrowed", "N/A"),
                "Returned" if record.get("returned") else "Borrowed"
            ))

    # Start PDF generation
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(200, height - 40, "Usage History Report")
    pdf.setFont("Helvetica", 10)

    y = height - 80
    pdf.drawString(50, y, "User")
    pdf.drawString(180, y, "Equipment")
    pdf.drawString(280, y, "Date")
    pdf.drawString(430, y, "Status")
    y -= 20

    if not report_data:
        pdf.drawString(50, y, "No data found for the selected report.")
    else:
        for user, equip, date, status in report_data:
            if y < 50:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, user)
            pdf.drawString(180, y, equip)
            pdf.drawString(280, y, date)
            pdf.drawString(430, y, status)
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

@app.route('/equipment_history/<user_id>/<equipment_id>')
def equipment_detail(user_id, equipment_id):
    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    equipment_info = get_equipment_by_id(equipment_id)
    if not equipment_info:
        return "Equipment not found", 404

    # Get all borrows and filter by equipment ID
    all_borrows = get_all_borrows()
    history = [
        {
            "user": b.get("username", "Unknown"),
            "date": b.get("date_borrowed", "N/A"),
            "status": "Returned" if b.get("returned") else "Borrowed"
        }
        for b in all_borrows if b.get("item_id") == equipment_id
    ]

    history.sort(key=lambda x: x["date"], reverse=True)

    return render_template('equipment.html', user_id=user_id, equipment=equipment_info, history=history)


@app.route('/reservations/<user_id>')
def reservations(user_id):
    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    equipment_list = get_equipment()
    borrows = get_all_borrows()

    is_admin = user.get("admin", False)

    events = []
    table_reservations = {}

    for b in borrows:
        event = {
            "title": f"{b.get('item_id')} ({b.get('username')})",
            "start": b.get('date_borrowed', "N/A")
        }
        events.append(event)

        # Admin sees all, user sees only own
        if is_admin or b.get('user_id') == user["user_id"]:
            date = b.get('date_borrowed', "N/A")
            if date not in table_reservations:
                table_reservations[date] = []
            table_reservations[date].append({
                "equipment": b.get('item_id'),
                "user": b.get('username'),
            })

    return render_template('reservations.html', user_id=user_id, is_admin=is_admin, equipment=equipment_list, reservations=table_reservations, calendar_events=events)


@app.route('/make_reservation/<user_id>', methods=['POST'])
def make_reservation(user_id):
    equipment_id = request.form.get('equipment')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not equipment_id or not start_date or not end_date:
        return "Missing required fields", 400

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format", 400

    if start > end:
        return "Start date must be before or equal to end date", 400

    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    headers = {"Authorization": f"Bearer {session['token']}"}
    current = start

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        reservation_data = {
            "item_id": equipment_id,
            "start_date": date_str
        }
        response = requests.put(f"{API_BASE_URL}/items/{equipment_id}/borrow", headers=headers, json=reservation_data)
        print(f"[DEBUG] Borrowing {equipment_id} on {date_str}: {response.status_code}")
        current += timedelta(days=1)

    return redirect(url_for('reservations', user_id=user_id))


@app.route('/remove_reservation/<user_id>', methods=['POST'])
def remove_reservation(user_id):
    item_id = request.form.get('equipment')
    date = request.form.get('date')

    if not item_id or not date:
        return "Missing required fields", 400

    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    headers = {"Authorization": f"Bearer {session['token']}"}

    # Call API to "return" the item (cancel the reservation/borrow)
    response = requests.put(f"{API_BASE_URL}/items/{item_id}/return", headers=headers)

    print("[DEBUG] Remove reservation response:", response.status_code, response.text)

    if response.status_code == 200:
        return redirect(url_for('reservations', user_id=user_id))
    else:
        return f"Failed to remove reservation: {response.text}", 400


@app.route('/user_history/<user_id>')
def user_history(user_id):
    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    username = user.get("username")
    headers = {"Authorization": f"Bearer {session['token']}"}

    # Get only current user's borrows
    res = requests.get(f"{API_BASE_URL}/user/borrows", headers=headers)
    if res.status_code != 200:
        return "Failed to fetch user history", 400

    borrows = res.json()

    user_transactions = []

    for b in borrows:
        item_id = b.get("item_id")
        # Fetch item info to get the real name
        item = requests.get(f"{API_BASE_URL}/items/{item_id}", headers=headers).json() if item_id else {}
        equipment_name = item.get("name", "Unknown Equipment")

        user_transactions.append({
            "equipment": equipment_name,
            "item_id": item_id,
            "date": b.get("date_borrowed", "N/A"),
            "status": "Returned" if b.get("returned") else "Borrowed"
        })

    user_transactions.sort(key=lambda x: x["date"], reverse=True)

    return render_template('user_history.html', username=username, user_id=user_id, history=user_transactions)


@app.route('/checkout/<user_id>/<equipment_id>', methods=['GET', 'POST'])
def checkout_equipment(user_id, equipment_id):
    if user_id == "scan":
        # FORCE logout anyone who is already logged in
        session.clear()

        # Save the equipment_id they are trying to check out
        session['pending_checkout_equipment_id'] = equipment_id

        return redirect(url_for('login'))

    # Normal flow after login
    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    headers = {"Authorization": f"Bearer {session['token']}"}
    equipment_info = get_equipment_by_id(equipment_id)
    if not equipment_info:
        return "Equipment not found", 404

    equipment_name = equipment_info.get('name', 'Unknown Equipment')

    if not equipment_info.get('availability', True):
        return render_template("checkout.html", user_id=user_id, equipment_type=equipment_id,
                               equipment_name=equipment_name, max_days=0,
                               error="This item is currently not available for checkout.")

    today = datetime.today().date()
    max_days = 7

    if request.method == 'POST':
        start_date = today.strftime("%Y-%m-%d")
        checkout_data = {
            "item_id": equipment_id,
            "start_date": start_date
        }

        response = requests.put(f"{API_BASE_URL}/items/{equipment_id}/borrow", headers=headers, json=checkout_data)
        print("[DEBUG] Checkout response:", response.status_code, response.text)

        if response.status_code == 200:
            success_message = f"{equipment_name} successfully checked out."
            return render_template("checkout.html", user_id=user_id, equipment_type=equipment_id,
                                   equipment_name=equipment_name, max_days=0,
                                   success=success_message)
        elif response.status_code == 422:
            return render_template("checkout.html", user_id=user_id, equipment_type=equipment_id,
                                   equipment_name=equipment_name, max_days=max_days,
                                   error="Failed to check out equipment.")
        else:
            success_message = f"{equipment_name} successfully checked out."
            return render_template("checkout.html", user_id=user_id, equipment_type=equipment_id,
                                   equipment_name=equipment_name, max_days=0,
                                   success=success_message)

    return render_template("checkout.html", user_id=user_id, equipment_type=equipment_id,
                           equipment_name=equipment_name, max_days=max_days)


@app.route('/checkin/<user_id>/<equipment_id>', methods=['POST'])
def checkin_equipment(user_id, equipment_id):
    user = get_current_user()
    if not user:
        return "Unauthorized", 403

    headers = {"Authorization": f"Bearer {session['token']}"}

    response = requests.put(f"{API_BASE_URL}/items/{equipment_id}/return", headers=headers)

    print("[DEBUG] Checkin response:", response.status_code, response.text)

    if response.status_code == 200:
        return redirect(url_for('dashboard', user_id=user_id))
    else:
        return f"Failed to check in equipment: {response.text}", 400


if __name__ == '__main__':
    app.run(debug=True)