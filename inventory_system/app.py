from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from functools import wraps
import os
import json
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "inventory.db")

os.makedirs(INSTANCE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
KEY: SECRET_KEY
VALUE: any-long-random-string-123456


# Default admin credentials
DEFAULT_ADMIN_USERNAME = 'ADMIN'
DEFAULT_ADMIN_PASSWORD = '1111'

db = SQLAlchemy(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database Models
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
    
    sales = db.relationship('SaleItem', backref='product', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')
    upi_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').upper().strip()
        password = request.form.get('password', '')
        
        if username == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Welcome to BOLT BILLINGs!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    total_products = Product.query.count()
    total_sales = Sale.query.count()
    today_sales = Sale.query.filter(
        db.func.date(Sale.created_at) == date.today()
    ).count()
    low_stock = Product.query.filter(Product.stock <= Product.min_stock).count()
    
    # Calculate today's revenue
    today_revenue = db.session.query(db.func.sum(Sale.total_amount)).filter(
        db.func.date(Sale.created_at) == date.today()
    ).scalar() or 0
    
    # Calculate today's revenue with GST (18%)
    today_revenue_with_gst = today_revenue * 1.18
    
    # Calculate total revenue with GST (18%)
    total_revenue_with_gst = total_revenue * 1.18
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
    
    # Get recent sales
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_products=total_products,
                         total_sales=total_sales,
                         today_sales=today_sales,
                         low_stock=low_stock,
                         today_revenue=today_revenue,
                         total_revenue=total_revenue,
                         today_revenue_with_gst=today_revenue_with_gst,
                         total_revenue_with_gst=total_revenue_with_gst,
                         recent_sales=recent_sales)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get sales data for chart
    sales_data = db.session.query(
        db.func.date(Sale.created_at).label('date'),
        db.func.sum(Sale.total_amount).label('total')
    ).group_by(db.func.date(Sale.created_at)
    ).order_by(db.func.date(Sale.created_at)
    ).limit(30).all()
    
    dates = [str(s.date) for s in sales_data]
    amounts = [float(s.total) for s in sales_data]
    
    # Get top selling products
    top_products = db.session.query(
        Product.name,
        db.func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).group_by(Product.id
    ).order_by(db.func.sum(SaleItem.quantity).desc()
    ).limit(10).all()
    
    product_names = [p.name for p in top_products]
    quantities = [p.total_sold for p in top_products]
    
    # Get products in demand (high sales rate)
    demand_products = db.session.query(
        Product.name,
        Product.stock,
        db.func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).filter(
        SaleItem.sale_id.in_(
            db.session.query(Sale.id).filter(
                Sale.created_at >= datetime.now().replace(day=1)
            )
        )
    ).group_by(Product.id
    ).order_by(db.func.sum(SaleItem.quantity).desc()
    ).limit(10).all()
    
    return render_template('dashboard.html',
                         dates=dates,
                         amounts=amounts,
                         product_names=product_names,
                         quantities=quantities,
                         demand_products=demand_products)

@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            sku=request.form['sku'],
            category=request.form['category'],
            description=request.form.get('description', ''),
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            min_stock=int(request.form.get('min_stock', 10))
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.sku = request.form['sku']
        product.category = request.form['category']
        product.description = request.form.get('description', '')
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.min_stock = int(request.form.get('min_stock', 10))
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    if request.method == 'POST':
        # Create sale
        items = request.form.getlist('items[]')
        quantities = request.form.getlist('quantities[]')
        
        if not items or not any(items):
            flash('Please add items to the bill', 'error')
            return redirect(url_for('billing'))
        
        # Generate invoice number
        invoice_num = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        total_amount = 0
        sale = Sale(
            invoice_number=invoice_num,
            customer_name=request.form.get('customer_name', ''),
            payment_method=request.form.get('payment_method', 'cash'),
            total_amount=0
        )
        
        # Add UPI ID if provided
        if request.form.get('payment_method') == 'upi':
            sale.upi_id = request.form.get('upi_id', '')
        
        db.session.add(sale)
        db.session.flush()
        
        for item_id, qty in zip(items, quantities):
            if item_id and qty:
                product = Product.query.get(int(item_id))
                if product and int(qty) > 0:
                    unit_price = product.price
                    subtotal = unit_price * int(qty)
                    total_amount += subtotal
                    
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=int(qty),
                        unit_price=unit_price,
                        subtotal=subtotal
                    )
                    db.session.add(sale_item)
                    
                    # Update stock
                    product.stock -= int(qty)
        
        sale.total_amount = total_amount
        db.session.commit()
        flash(f'Sale completed! Invoice: {invoice_num}', 'success')
        return redirect(url_for('billing'))
    
    products = Product.query.filter(Product.stock > 0).all()
    return render_template('billing.html', products=products)

@app.route('/sales')
@login_required
def sales():
    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    return render_template('sales.html', sales=sales)

@app.route('/sales/<int:id>')
@login_required
def sale_details(id):
    sale = Sale.query.get_or_404(id)
    return render_template('sale_details.html', sale=sale)

@app.route('/stock')
@login_required
def stock():
    products = Product.query.order_by(Product.stock.asc()).all()
    return render_template('stock.html', products=products)

@app.route('/api/products')
@login_required
def api_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'stock': p.stock
    } for p in products])

@app.route('/api/product/<sku_or_id>')
@login_required
def api_product_lookup(sku_or_id):
    """API endpoint for barcode scanner - lookup product by SKU or ID"""
    # Try to find by SKU first
    product = Product.query.filter_by(sku=sku_or_id).first()
    
    # If not found, try by ID
    if not product and sku_or_id.isdigit():
        product = Product.query.get(int(sku_or_id))
    
    if product:
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': product.price,
                'stock': product.stock,
                'category': product.category
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Product not found'
        }), 404

@app.route('/api/ai-suggestions')
@login_required
def api_ai_suggestions():
    """AI-based product suggestions based on sales history"""
    # Get top selling products
    top_products = db.session.query(
        Product.id,
        Product.name,
        Product.price,
        Product.stock,
        db.func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).group_by(Product.id
    ).order_by(db.func.sum(SaleItem.quantity).desc()
    ).limit(5).all()
    
    # Get products in demand (low stock but high sales)
    demand_products = Product.query.filter(
        Product.stock > 0,
        Product.stock <= Product.min_stock * 2
    ).order_by(Product.stock.asc()).limit(5).all()
    
    # Get recently added products
    recent_products = Product.query.order_by(
        Product.created_at.desc()
    ).limit(5).all()
    
    suggestions = {
        'top_selling': [
            {
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'stock': p.stock,
                'total_sold': p.total_sold
            } for p in top_products
        ],
        'in_demand': [
            {
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'stock': p.stock
            } for p in demand_products
        ],
        'recent': [
            {
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'stock': p.stock
            } for p in recent_products
        ]
    }
    
    return jsonify(suggestions)

# Initialize database
with app.app_context():
    db.create_all()

# Flask app is imported by Vercel from api/index.py
