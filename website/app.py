import qrcode
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import uuid


app = Flask(__name__)

# Hardcoded user data
login_database = {
    "jhall": {"id": str(uuid.uuid4()), "username": "jhall", "password": "123", "admin": False},
    "Demo": {"id": str(uuid.uuid4()), "username": "Demo", "password": "mypassword", "admin": False},
    "egantulga": {"id": str(uuid.uuid4()), "username": "egantulga", "password": "12345", "admin": False},
    "dzhanbyrshy": {"id": str(uuid.uuid4()), "username": "dzhanbyrshy", "password": "admin", "admin": True},
}

# Equipment data with boolean availability
equipment_database = [
    {'id': str(uuid.uuid4()), 'type': 'Whiteboard', 'description': 'Magnetic Whiteboard', 'availability': True, 'quality': '10'},
    {'id': str(uuid.uuid4()), 'type': 'Camera', 'description': '', 'availability': True, 'quality': '9'},
    {'id': str(uuid.uuid4()), 'type': 'robot', 'description': '', 'availability': True, 'quality': '8'},
]

# sample equipment history data
equipment_history = {
    "Whiteboard": [
        {"user": "dzhanbryshy", "date": "2025-05-01T02:58:06.703610", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-05-01T02:57:41.983013", "status": "Borrowed"},
        {"user": "Demo", "date": "2025-05-01T02:46:52.267379", "status": "Borrowed"},
        {"user": "Demo", "date": "2025-05-01T02:45:53.129008", "status": "Borrowed"},
        {"user": "Demo", "date": "2025-05-01T02:45:40.974901", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T22:05:02.738585", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T22:04:10.207562", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T21:43:31.719815", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T21:41:07.639958", "status": "Borrowed"}
    ],
    "Camera": [
        {"user": "dzhanbryshy", "date": "2025-04-29T18:25:06.445340", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T22:04:02.822120", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T21:41:15.529149", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-28T21:40:00.432554", "status": "Borrowed"}
    ],
    "robot": [
        {"user": "dzhanbryshy", "date": "2025-04-29T21:15:58.655656", "status": "Borrowed"},
        {"user": "dzhanbryshy", "date": "2025-04-29T02:01:37.288797", "status": "Borrowed"}
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
    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user:
        return "User not found", 404

    username = user["username"]
    is_admin = user["admin"]

    today_str = datetime.today().strftime("%Y-%m-%d")
    reserved_today = set(res["equipment"] for res in reservations_database.get(today_str, []))

    for item in equipment_database:
        item["availability"] = False if item["type"] in reserved_today else True

    return render_template('dashboard.html', username=username, user_id=user_id, equipment=equipment_database, is_admin=is_admin)


@app.route('/admin/<user_id>', methods=['GET', 'POST'])
def admin_panel(user_id):
    current_user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not current_user or not current_user["admin"]:
        return "Unauthorized", 403

    if request.method == 'POST':
        target_username = request.form.get('username')
        action = request.form.get('action')

        if target_username in login_database and target_username != current_user["username"]:
            login_database[target_username]["admin"] = (action == "promote")

    # Flatten equipment history
    history_log = []
    for equipment_type, logs in equipment_history.items():
        for record in logs:
            history_log.append({
                "user": record["user"],
                "equipment": equipment_type,
                "date": record["date"],
                "status": record["status"]
            })

    # Flatten reservation log
    reservation_log = []
    for date, reservations in reservations_database.items():
        for res in reservations:
            reservation_log.append({
                "user": res["user"],
                "equipment": res["equipment"],
                "date": date,
                "status": "Reserved"
            })

    # Combine and sort
    combined_log = history_log + reservation_log
    combined_log.sort(key=lambda x: x["date"], reverse=True)

    return render_template("admin.html", user_id=user_id, users=login_database, log=combined_log, equipment=equipment_database)


@app.route('/admin/user_details/<admin_id>/<target_user_id>')
def admin_user_details(admin_id, target_user_id):
    # Verify current user is admin
    admin = next((u for u in login_database.values() if u["id"] == admin_id), None)
    if not admin or not admin["admin"]:
        return "Unauthorized", 403

    # Get the target user
    target_user = next((u for u in login_database.values() if u["id"] == target_user_id), None)
    if not target_user:
        return "User not found", 404

    target_username = target_user["username"]
    target_password = target_user["password"]
    target_is_admin = target_user["admin"]

    # Compile history
    user_history = []

    # From equipment history
    for equipment_type, logs in equipment_history.items():
        for record in logs:
            if record["user"] == target_username:
                user_history.append({
                    "equipment": equipment_type,
                    "date": record["date"],
                    "status": record["status"]
                })

    # From reservations
    for date, reservations in reservations_database.items():
        for res in reservations:
            if res["user"] == target_user_id:
                user_history.append({
                    "equipment": res["equipment"],
                    "date": date,
                    "status": "Reserved"
                })

    # Sort by date
    user_history.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        'admin_user_details.html',
        admin_id=admin_id,
        username=target_username,
        password=target_password,
        is_admin=target_is_admin,
        history=user_history
    )


@app.route('/admin/qrcode/<user_id>/<equipment_type>')
def generate_equipment_qrcode(user_id, equipment_type):
    # Confirm admin access
    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user or not user["admin"]:
        return "Unauthorized", 403

    # Check if the equipment exists
    equipment = next((e for e in equipment_database if e["type"] == equipment_type), None)
    if not equipment:
        return "Equipment not found", 404

    # Generate checkout URL (external URL)
    checkout_url = url_for('checkout_equipment', user_id=user_id, equipment_type=equipment_type, _external=True)

    # Create QR code image
    img = qrcode.make(checkout_url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png', download_name=f"{equipment_type}_qr.png")


@app.route('/admin/generate_pdf/<user_id>', methods=['POST'])
def generate_pdf(user_id):
    current_user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not current_user or not current_user["admin"]:
        return "Unauthorized", 403

    report_type = request.form.get('report_type')
    selected_value = request.form.get('selected_value')

    report_data = []

    if report_type == "user":
        username = selected_value
        for equipment_type, records in equipment_history.items():
            for record in records:
                if record["user"] == username:
                    report_data.append((record["user"], equipment_type, record["date"], record["status"]))

    elif report_type == "equipment":
        equipment_type = selected_value
        for record in equipment_history.get(equipment_type, []):
            report_data.append((record["user"], equipment_type, record["date"], record["status"]))

    elif report_type == "all_users":
        for equipment_type, records in equipment_history.items():
            for record in records:
                report_data.append((record["user"], equipment_type, record["date"], record["status"]))

    # Generate PDF using ReportLab
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
        if y < 50:  # new page if not enough space
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
    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user:
        return "User not found", 404

    is_admin = user["admin"]

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


@app.route('/checkout/<user_id>/<equipment_type>', methods=['GET', 'POST'])
def checkout_equipment(user_id, equipment_type):
    user = next((u for u in login_database.values() if u["id"] == user_id), None)
    if not user:
        return "User not found", 404

    username = user["username"]
    today = datetime.today().date()
    max_days = 7

    # Check for reservation conflicts in the next 7 days
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

        # Proceed with checkout
        for i in range(days):
            checkout_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")

            # Add to reservations to block reservation system
            if checkout_date not in reservations_database:
                reservations_database[checkout_date] = []

            reservations_database[checkout_date].append({
                "equipment": equipment_type,
                "user": user_id
            })

            # Add to equipment history
            if equipment_type not in equipment_history:
                equipment_history[equipment_type] = []

            equipment_history[equipment_type].append({
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