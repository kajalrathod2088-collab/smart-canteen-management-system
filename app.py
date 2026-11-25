import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "canteen.db")

app = Flask(__name__)
app.secret_key = "smart-canteen-secret-key-2026-viva-ready"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        wallet_balance REAL NOT NULL DEFAULT 350.0,
        department TEXT DEFAULT 'Computer Science'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        is_veg INTEGER NOT NULL DEFAULT 1,
        is_available INTEGER NOT NULL DEFAULT 1,
        prep_time INTEGER DEFAULT 5,
        image_url TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_no TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Received',
        payment_method TEXT NOT NULL DEFAULT 'Wallet',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(item_id) REFERENCES menu_items(id)
    )
    """)

    # Seed Admin User if not exists
    cursor.execute("SELECT id FROM users WHERE roll_no = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (roll_no, name, password, role, wallet_balance, department)
        VALUES ('admin', 'Canteen Admin / Chef', 'admin123', 'admin', 0.0, 'Staff')
        """)

    # Seed Demo Student if not exists
    cursor.execute("SELECT id FROM users WHERE roll_no = 'CS202601'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (roll_no, name, password, role, wallet_balance, department)
        VALUES ('CS202601', 'Aarav Sharma', 'student123', 'student', 450.0, 'CSE - 3rd Year')
        """)

    # Seed Initial Menu Items if empty
    cursor.execute("SELECT COUNT(*) as count FROM menu_items")
    if cursor.fetchone()["count"] == 0:
        sample_items = [
            ("Crispy Samosa (2 pcs)", "Snacks", 20.0, "Fresh potato stuffed triangular pastries served with green mint chutney", 1, 1, 3, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500"),
            ("Masala Dosa", "Breakfast", 60.0, "South Indian fermented crepe with spiced potato filling, sambar & coconut chutney", 1, 1, 8, "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=500"),
            ("Chole Bhature", "Meals", 75.0, "Spiced chickpea curry paired with 2 fluffy deep-fried bhaturas & pickled onions", 1, 1, 10, "https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=500"),
            ("Veg Cheese Burger", "Fast Food", 55.0, "Crispy veggie patty with molten cheddar slice, crisp lettuce and spicy mayo", 1, 1, 7, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"),
            ("Cheese Butter Maggi", "Snacks", 45.0, "College classic 2-minute noodles tossed with butter, veggies & grated cheese", 1, 1, 5, "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=500"),
            ("Paneer Tikka Roll", "Fast Food", 70.0, "Charcoal grilled paneer cubes wrapped in whole-wheat paratha with mint spread", 1, 1, 7, "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500"),
            ("Special Veg Thali", "Meals", 95.0, "Dal Makhani, Paneer Butter Masala, 3 Butter Rotis, Jeera Rice, Salad & Gulab Jamun", 1, 1, 12, "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500"),
            ("Chilled Cold Coffee", "Beverages", 40.0, "Frothy blended espresso with cold milk and chocolate drizzle on top", 1, 1, 3, "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=500"),
            ("Cutting Masala Chai", "Beverages", 15.0, "Freshly brewed ginger and cardamom milk tea to power through college lectures", 1, 1, 2, "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500"),
            ("Chicken Crisp Burger", "Fast Food", 80.0, "Golden fried spiced chicken patty topped with caramelized onions and peri-peri sauce", 0, 1, 8, "https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500"),
            ("Warm Gulab Jamun (2 pcs)", "Desserts", 30.0, "Melt-in-mouth soft cottage cheese dumplings soaked in saffron sugar syrup", 1, 1, 2, "/static/images/gulab_jamun.jpg"),
            ("Fresh Lime Soda", "Beverages", 25.0, "Refreshing fizz with fresh lime, mint sprig, black salt and chilled soda", 1, 1, 2, "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500")
        ]
        cursor.executemany("""
        INSERT INTO menu_items (name, category, price, description, is_veg, is_available, prep_time, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_items)

    conn.commit()
    conn.close()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Access denied. Admin portal only.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_cart_and_user():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    current_user = None
    if "user_id" in session:
        conn = get_db()
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        conn.close()
        if user_row:
            current_user = dict(user_row)
            session["wallet_balance"] = current_user["wallet_balance"]
    return dict(cart_count=cart_count, current_user=current_user)

# Routes
@app.route("/")
def index():
    category = request.args.get("category", "All")
    search = request.args.get("search", "").strip()
    diet = request.args.get("diet", "all")

    conn = get_db()
    query = "SELECT * FROM menu_items WHERE 1=1"
    params = []

    if category != "All":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if diet == "veg":
        query += " AND is_veg = 1"
    elif diet == "nonveg":
        query += " AND is_veg = 0"

    items = conn.execute(query, params).fetchall()

    categories = [row["category"] for row in conn.execute("SELECT DISTINCT category FROM menu_items").fetchall()]
    conn.close()

    return render_template("index.html", items=items, categories=categories, selected_cat=category, search=search, diet=diet)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE roll_no = ?", (roll_no,)).fetchone()
        conn.close()

        if user and user["password"] == password:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["roll_no"] = user["roll_no"]
            session["role"] = user["role"]
            session["wallet_balance"] = user["wallet_balance"]
            flash(f"Welcome back, {user['name']}! 👋", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("index"))
        else:
            flash("Invalid Student Roll Number or Password.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip().upper()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        dept = request.form.get("department", "Engineering").strip()

        if not roll_no or not name or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        try:
            # New registered students get a welcome ₹250 wallet balance
            conn.execute("""
            INSERT INTO users (roll_no, name, password, role, wallet_balance, department)
            VALUES (?, ?, ?, 'student', 250.0, ?)
            """, (roll_no, name, password, dept))
            conn.commit()
            flash("Account registered successfully! ₹250 added to your Smart Wallet. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Student Roll Number already registered. Please log in.", "warning")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))

# Cart APIs
@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    if not cart:
        return render_template("cart.html", cart_items=[], subtotal=0, tax=0, grand_total=0)

    conn = get_db()
    item_ids = list(cart.keys())
    placeholders = ",".join("?" for _ in item_ids)
    rows = conn.execute(f"SELECT * FROM menu_items WHERE id IN ({placeholders})", item_ids).fetchall()
    conn.close()

    cart_items = []
    subtotal = 0
    for r in rows:
        qty = cart.get(str(r["id"]), 0)
        if qty > 0:
            total_item_price = r["price"] * qty
            subtotal += total_item_price
            cart_items.append({
                "id": r["id"],
                "name": r["name"],
                "price": r["price"],
                "is_veg": r["is_veg"],
                "image_url": r["image_url"],
                "prep_time": r["prep_time"],
                "quantity": qty,
                "total_price": total_item_price
            })

    grand_total = subtotal
    return render_template("cart.html", cart_items=cart_items, subtotal=subtotal, grand_total=grand_total)

@app.route("/add-to-cart/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    cart = session.get("cart", {})
    str_id = str(item_id)
    cart[str_id] = cart.get(str_id, 0) + 1
    session["cart"] = cart
    session.modified = True
    flash("Item added to tray! 🍔", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/update-cart/<int:item_id>/<action>")
def update_cart(item_id, action):
    cart = session.get("cart", {})
    str_id = str(item_id)
    if str_id in cart:
        if action == "increase":
            cart[str_id] += 1
        elif action == "decrease":
            cart[str_id] -= 1
            if cart[str_id] <= 0:
                del cart[str_id]
        elif action == "remove":
            del cart[str_id]
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("view_cart"))

@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared.", "info")
    return redirect(url_for("view_cart"))

@app.route("/recharge-wallet", methods=["POST"])
@login_required
def recharge_wallet():
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0

    if amount < 10:
        flash("Minimum recharge amount is ₹10.", "danger")
        return redirect(request.referrer or url_for("index"))

    conn = get_db()
    conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?", (amount, session["user_id"]))
    conn.commit()
    conn.close()

    flash(f"₹{amount:.2f} credited to Smart Canteen Wallet! 🎉", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your food cart is empty!", "warning")
        return redirect(url_for("index"))

    payment_method = request.form.get("payment_method", "Wallet")

    conn = get_db()
    cursor = conn.cursor()

    # Calculate current total and verify stock
    item_ids = list(cart.keys())
    placeholders = ",".join("?" for _ in item_ids)
    rows = cursor.execute(f"SELECT * FROM menu_items WHERE id IN ({placeholders})", item_ids).fetchall()

    subtotal = 0
    items_to_save = []
    for r in rows:
        qty = cart.get(str(r["id"]), 0)
        if not r["is_available"]:
            conn.close()
            flash(f"Sorry, {r['name']} is currently out of stock. Please remove it to proceed.", "danger")
            return redirect(url_for("view_cart"))
        line_total = r["price"] * qty
        subtotal += line_total
        items_to_save.append((r["id"], r["name"], r["price"], qty))

    # Check student balance if paying via wallet
    user = cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if payment_method == "Wallet":
        if user["wallet_balance"] < subtotal:
            conn.close()
            flash(f"Insufficient Wallet Balance! Available: ₹{user['wallet_balance']:.2f}, Required: ₹{subtotal:.2f}. Please recharge your wallet.", "danger")
            return redirect(url_for("view_cart"))
        # Deduct wallet balance
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance - ? WHERE id = ?", (subtotal, session["user_id"]))

    # Generate sequential Token Number for today
    today_prefix = datetime.now().strftime("%d")
    count_today = cursor.execute("SELECT COUNT(*) as cnt FROM orders").fetchone()["cnt"] + 1
    token_no = f"TK-{today_prefix}{count_today:03d}"

    # Insert Order
    cursor.execute("""
    INSERT INTO orders (token_no, user_id, total_amount, status, payment_method)
    VALUES (?, ?, ?, 'Received', ?)
    """, (token_no, session["user_id"], subtotal, payment_method))
    order_id = cursor.lastrowid

    # Insert items
    for item_id, item_name, price, qty in items_to_save:
        cursor.execute("""
        INSERT INTO order_items (order_id, item_id, item_name, price, quantity)
        VALUES (?, ?, ?, ?, ?)
        """, (order_id, item_id, item_name, price, qty))

    conn.commit()
    conn.close()

    # Clear Cart
    session.pop("cart", None)
    return redirect(url_for("order_success", order_id=order_id))

@app.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, session["user_id"])).fetchone()
    if not order:
        conn.close()
        flash("Order not found.", "danger")
        return redirect(url_for("index"))

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    return render_template("order_success.html", order=order, items=items)

@app.route("/my-orders")
@login_required
def my_orders():
    conn = get_db()
    orders = conn.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    detailed_orders = []
    for o in orders:
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
        detailed_orders.append({
            "order": o,
            "order_items": items
        })
    conn.close()
    return render_template("my_orders.html", detailed_orders=detailed_orders)

@app.route("/token-board")
def token_board():
    """Live public kitchen display board for cafeteria monitors"""
    conn = get_db()
    preparing = conn.execute("SELECT token_no, created_at FROM orders WHERE status = 'Preparing' ORDER BY id ASC LIMIT 8").fetchall()
    ready = conn.execute("SELECT token_no, created_at FROM orders WHERE status = 'Ready' ORDER BY id DESC LIMIT 8").fetchall()
    conn.close()
    return render_template("token_display.html", preparing=preparing, ready=ready)

@app.route("/api/live-tokens")
def api_live_tokens():
    """Endpoint for auto-refreshing public token TV screen"""
    conn = get_db()
    preparing = [r["token_no"] for r in conn.execute("SELECT token_no FROM orders WHERE status = 'Preparing' ORDER BY id ASC").fetchall()]
    ready = [r["token_no"] for r in conn.execute("SELECT token_no FROM orders WHERE status = 'Ready' ORDER BY id DESC").fetchall()]
    conn.close()
    return jsonify({"preparing": preparing, "ready": ready})

@app.route("/api/order-status/<int:order_id>")
def api_order_status(order_id):
    conn = get_db()
    row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if row:
        return jsonify({"status": row["status"]})
    return jsonify({"status": "Unknown"}), 404

# Admin / Kitchen Staff Routes
@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()

    total_revenue = conn.execute("SELECT SUM(total_amount) as rev FROM orders WHERE status != 'Cancelled'").fetchone()["rev"] or 0
    total_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders").fetchone()["cnt"]
    active_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE status IN ('Received', 'Preparing', 'Ready')").fetchone()["cnt"]

    # Recent orders
    orders_raw = conn.execute("""
        SELECT o.*, u.name as student_name, u.roll_no as student_roll
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.id DESC
    """).fetchall()

    orders_list = []
    for o in orders_raw:
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
        orders_list.append({
            "order": o,
            "order_items": items
        })

    menu_items = conn.execute("SELECT * FROM menu_items ORDER BY category, name").fetchall()
    conn.close()

    return render_template("admin.html",
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           active_orders=active_orders,
                           orders=orders_list,
                           menu_items=menu_items)

@app.route("/admin/update-order-status", methods=["POST"])
@admin_required
def update_order_status():
    order_id = request.form.get("order_id")
    new_status = request.form.get("status")

    if new_status in ["Received", "Preparing", "Ready", "Completed", "Cancelled"]:
        conn = get_db()
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        flash(f"Order #{order_id} marked as '{new_status}'!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/toggle-stock/<int:item_id>")
@admin_required
def toggle_stock(item_id):
    conn = get_db()
    conn.execute("UPDATE menu_items SET is_available = CASE WHEN is_available = 1 THEN 0 ELSE 1 END WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item stock availability updated.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add-menu-item", methods=["POST"])
@admin_required
def add_menu_item():
    name = request.form.get("name")
    category = request.form.get("category")
    price = float(request.form.get("price", 0))
    description = request.form.get("description", "")
    is_veg = 1 if request.form.get("is_veg") == "1" else 0
    prep_time = int(request.form.get("prep_time", 5))
    image_url = request.form.get("image_url", "").strip()
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500"

    conn = get_db()
    conn.execute("""
    INSERT INTO menu_items (name, category, price, description, is_veg, is_available, prep_time, image_url)
    VALUES (?, ?, ?, ?, ?, 1, ?, ?)
    """, (name, category, price, description, is_veg, prep_time, image_url))
    conn.commit()
    conn.close()

    flash(f"Added {name} to Canteen Menu! 🍲", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete-item/<int:item_id>")
@admin_required
def delete_menu_item(item_id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Menu item removed.", "warning")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    init_db()
    print("\n" + "="*50)
    print("🚀 SMART CANTEEN MANAGEMENT SYSTEM IS RUNNING!")
    print("👉 Automatically opening browser at: http://127.0.0.1:5000")
    print("👉 Student Login: Roll No: CS202601 | Password: student123")
    print("👉 Admin / Kitchen: Roll No: admin    | Password: admin123")
    print("="*50 + "\n")
    
    # Automatically open the browser directly from terminal
    import webbrowser, threading
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    
    app.run(debug=True, host="127.0.0.1", port=5000)
