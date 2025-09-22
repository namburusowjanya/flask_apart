                                                        Apartment Maintenance Management System — README
 Project Overview:
   A Python Flask web application to automate financial operations for a 40-flat apartment complex. It supports monthly billing, payments, expense logging, financial reporting (balance sheet, cash flow), and
   defaulter tracking. Designed for treasurer workflows with month-end closing and reports.
   
 Features:
   • Configure and generate monthly maintenance bills for 40 flats
   • Record payments (Cash / Online)
   • Real-time balance updates 
   • Daily expense logging with vendor, category, date
   • Categorize expenses (electricity, repairs, taxes, security, plumbing, etc.)
   • Monthly financial reports: Balance Sheet, Cash Flow
   • Month-end closing with automatic report generation
   
 Tech Stack
   • Backend: Flask (Python)
   • Database: MySQL
   • Frontend: HTML, CSS, JavaScript
   • UI Framework: Bootstrap 5
   
 Database Schema:
   Tables: flats, maintenance_bills, payments, expenses, financial_reports. Supports foreign key relationships for bills, payments, and reports.
   
 Month-End Closing:
   Locks previous month's data, computes closing balance using: Closing Balance = Opening Balance + Total Maintenance Collected - Total Expenses. 
   Generates Balance Sheet and Cash Flow Statement automatically.
   
 Setup Instructions:
  1 Clone the repository into your system:
    git clone [<repo-url>](https://github.com/namburusowjanya/flask_apart)
    
 2 Install required dependencies using pip:
    python -m venv .venv
    source .venv/bin/activate    # on Windows: .venv\Scripts\activate
    pip install -r requirements.txt

 3 Configure MySQL database and update DB URI in config:
   flask db upgrade
 
 4 Run migrations and seed data (optional)
 5 Start the Flask development server and access via browser:
   flask run (or) python run.py
   
 Usage:
 1. Generate monthly bills.
 2. Record payments as they come in.
 3. Log expenses daily
 4. At month end, perform closing and generate reports. 
