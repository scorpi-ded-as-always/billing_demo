from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from functools import wraps
import os

# -----------------------------
# Paths & App Setup
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "inventory.db")

os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# Default Admin
# -----------------------------
DEFAULT_ADMIN_USERNAME = "ADMIN"
DEFAULT_ADMIN_PASSWORD = "1111"

# -----------------------------
# Login Required Decorator
# -----------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------
# Database Models
# -----------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default="cash")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

# -----------------------------
# Auth Routes
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").upper().strip()
        password = request.form.get("password", "")

        if username == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Login successful", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -----------------------------
# Dashboard
# -----------------------------
@app.route("/")
@login_required
def index():
    total_products = Product.query.count()
    total_sales = Sale.query.count()

    today_sales = Sale.query.filter(
        db.func.date(Sale.created_at) == date.today()
    ).count()

    low_stock = Product.query.filter(
        Product.stock <= Product.min_stock
    ).count()

    total_revenue = db.session.query(
        db.func.sum(Sale.total_amount)
    ).scalar() or 0

    today_revenue = db.session.query(
        db.func.sum(Sale.total_amount)
    ).filter(
        db.func.date(Sale.created_at) == date.today()
    ).scalar() or 0

    return render_template(
        "index.html",
        total_products=total_products,
        total_sales=total_sales,
        today_sales=today_sales,
        low_stock=low_stock,
        total_revenue=total_revenue,
        today_revenue=today_revenue,
        today_revenue_with_gst=today_revenue * 1.18,
        total_revenue_with_gst=total_revenue * 1.18,
    )

# -----------------------------
# Products
# -----------------------------
@app.route("/products")
@login_required
def products():
    return render_template("products.html", products=Product.query.all())

@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        product = Product(
            name=request.form["name"],
            sku=request.form["sku"],
            category=request.form["category"],
            description=request.form.get("description", ""),
            price=float(request.form["price"]),
            stock=int(request.form["stock"]),
            min_stock=int(request.form.get("min_stock", 10)),
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("products"))

    return render_template("add_product.html")

# -----------------------------
# Billing
# -----------------------------
@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():
    products = Product.query.filter(Product.stock > 0).all()
    return render_template("billing.html", products=products)

# -----------------------------
# API
# -----------------------------
@app.route("/api/products")
@login_required
def api_products():
    return jsonify([
        {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock}
        for p in Product.query.all()
    ])

# -----------------------------
# Init DB
# -----------------------------
with app.app_context():
    db.create_all()

# NOTE:
# Do NOT add app.run()
# Vercel imports this app from api/index.py
