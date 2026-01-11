# Inventory Management System

A comprehensive Python-based inventory management system with billing, stock tracking, and data visualization capabilities.

## Features

- **Dashboard**: Real-time analytics with sales trends and product demand analysis
- **Product Management**: Add, edit, and delete products with SKU tracking
- **Billing/POS System**: Create sales invoices with automatic stock updates
- **Stock Tracking**: Monitor inventory levels with low stock alerts
- **Sales History**: View all transactions with detailed invoice information
- **Data Visualization**: Interactive charts showing highest sales and product demand
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

- **Backend**: Python 3.x with Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Icons**: Bootstrap Icons

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd inventory_system
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage Guide

### 1. Adding Products
- Navigate to "Products" → "Add Product"
- Fill in product details (name, SKU, category, price, stock)
- SKU must be unique for each product
- Set minimum stock level for low stock alerts

### 2. Creating Sales (Billing)
- Go to "Billing" section
- Select products from dropdown
- Enter quantity for each item
- Add items to the bill
- Enter customer name (optional)
- Select payment method
- Click "Complete Sale"

### 3. Viewing Dashboard
- Access "Dashboard" from navigation
- View sales trend chart (last 30 days)
- See top 10 products by sales volume
- Monitor products in high demand

### 4. Stock Management
- Navigate to "Stock" section
- View current inventory status
- Products are color-coded:
  - Red: Out of stock
  - Yellow: Low stock
  - Green: In stock
- Click "Update Stock" to adjust inventory levels

### 5. Sales History
- View all completed sales in "Sales" section
- Click "View" on any sale to see invoice details
- Print invoices from invoice details page

## Database Schema

### Products Table
- id: Integer (Primary Key)
- name: String
- sku: String (Unique)
- category: String
- description: Text
- price: Float
- stock: Integer
- min_stock: Integer
- created_at: DateTime

### Sales Table
- id: Integer (Primary Key)
- invoice_number: String (Unique)
- customer_name: String
- total_amount: Float
- payment_method: String
- created_at: DateTime

### SaleItems Table
- id: Integer (Primary Key)
- sale_id: Integer (Foreign Key)
- product_id: Integer (Foreign Key)
- quantity: Integer
- unit_price: Float
- subtotal: Float

## Deployment

### Deployment to Production

1. **Prepare for production:**
   ```bash
   # Install production web server (Gunicorn recommended)
   pip install gunicorn
   
   # Set environment variables
   export FLASK_ENV=production
   export SECRET_KEY='your-production-secret-key'
   ```

2. **Using Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Using systemd (Linux):**
   Create a service file `/etc/systemd/system/inventory.service`:
   ```ini
   [Unit]
   Description=Inventory Management System
   After=network.target
   
   [Service]
   User=www-data
   WorkingDirectory=/path/to/inventory_system
   Environment="PATH=/path/to/inventory_system/venv/bin"
   ExecStart=/path/to/inventory_system/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start the service:
   ```bash
   sudo systemctl enable inventory
   sudo systemctl start inventory
   ```

4. **Domain Configuration:**
   - Configure your domain's DNS to point to your server
   - Set up a reverse proxy (Nginx recommended)
   - Configure SSL certificate (Let's Encrypt recommended)

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Considerations

- Change the default `SECRET_KEY` in `app.py`
- Use environment variables for sensitive configuration
- Implement user authentication for production use
- Regular database backups
- Keep dependencies updated

## Backup and Restore

### Backup Database
```bash
cp instance/inventory.db backup/inventory_$(date +%Y%m%d).db
```

### Restore Database
```bash
cp backup/inventory_YYYYMMDD.db instance/inventory.db
```

## Troubleshooting

### Database Issues
- If database doesn't create: Delete `instance/inventory.db` and restart app
- Check file permissions on `instance/` directory

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
# Or run on different port
python app.py
# Then modify app.py to use different port
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Flask documentation
3. Check database schema integrity

## License

This project is provided as-is for educational and commercial use.

## Credits

Built with Flask, Bootstrap 5, and Chart.js