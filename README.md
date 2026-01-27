# Shalabi Verse Financial Management System

نظام إدارة مالية شامل لمشروع شلبي فيرس - Comprehensive financial management system for Shalabi Verse project

## Features (المميزات)

### Core Features
- **Dashboard (لوحة التحكم)**: Real-time financial metrics with customizable date filters
- **Accounts (الحسابات)**: Manage multiple accounts (Cash, Bank, Wallet)
- **Income Tracking (الدخل)**: Record and categorize income from various sources
- **Expense Tracking (المصروفات)**: Track expenses across different categories
- **Debt Management (الديون)**: Monitor debts owed to and by the business
- **Employee Management (الموظفين)**: Manage employees and salary payments
- **Reports (التقارير)**:
  - Profit & Loss statements
  - Income/Expense summaries
  - Project Equity reports

### Key Calculations
- Automatic profit/loss calculation
- Account balance tracking
- Project equity (Assets - Liabilities)
- Salary calculations (Base - Deductions + Bonus + Commission)
- Debt payment tracking

## Technology Stack

- **Backend**: Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 RTL (Arabic support)
- **Deployment**: PythonAnywhere ready

## Installation

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Database Initialization

The database is automatically created with default data on first run:
- Account types: كاش (Cash), بنك (Bank), محفظة (Wallet)
- Income categories: كورس (Course), خدمة (Service), محتوى (Content)
- Expense categories: رواتب (Salaries), أدوات (Tools), تسويق (Marketing), تشغيل (Operations), أخرى (Other)

## Project Structure

```
abdelhamed/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── models.py            # SQLAlchemy models
│   ├── config.py            # Configuration
│   ├── utils.py             # Helper functions
│   ├── blueprints/          # Route blueprints
│   │   ├── main/            # Dashboard
│   │   ├── accounts/        # Account management
│   │   ├── income/          # Income tracking
│   │   ├── expenses/        # Expense tracking
│   │   ├── debts/           # Debt management
│   │   ├── employees/       # Employee management
│   │   └── reports/         # Financial reports
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS files
├── instance/
│   └── shalabi_verse.db     # SQLite database
├── requirements.txt
├── run.py                   # Development server
├── wsgi.py                  # PythonAnywhere entry point
└── README.md
```

## Usage

### Adding a New Account
1. Navigate to "الحسابات" (Accounts)
2. Click "إضافة حساب جديد" (Add New Account)
3. Enter account name, type, and initial balance
4. Click "حفظ" (Save)

### Recording Income
1. Navigate to "المعاملات" > "الدخل" (Transactions > Income)
2. Click "إضافة دخل" (Add Income)
3. Select account, category, enter amount and date
4. Click "حفظ" (Save)

### Recording Expenses
1. Navigate to "المعاملات" > "المصروفات" (Transactions > Expenses)
2. Click "إضافة مصروف" (Add Expense)
3. Select account, category, enter amount and date
4. Click "حفظ" (Save)

### Managing Debts
1. Navigate to "الديون" (Debts)
2. Click "إضافة دين" (Add Debt)
3. Select debt type (owed to us/by us), person name, amount, and due date
4. To record a payment, click "دفع" (Pay) on the debt

### Paying Salaries
1. Navigate to "الموظفين" (Employees)
2. Click "دفع راتب" (Pay Salary) for the desired employee
3. Enter base salary, deductions, bonuses, and commissions
4. Select the account to pay from
5. Click "دفع الراتب" (Pay Salary)

## Deployment on PythonAnywhere

1. Upload all project files to PythonAnywhere
2. Create a virtual environment:
```bash
mkvirtualenv --python=/usr/bin/python3.10 shalabi-env
pip install -r requirements.txt
```

3. Update `wsgi.py` with your PythonAnywhere username
4. Configure the web app in PythonAnywhere dashboard:
   - Set WSGI file path
   - Set static files mapping: `/static/` -> `/home/yourusername/abdelhamed/app/static/`
5. Reload the web app

## Future Enhancements

- Advanced KPIs (ROI, Break-even Point, Gross Margin)
- Budgeting and forecasting
- Cash flow projections
- PDF/Excel export functionality
- Charts and visualizations
- Multi-currency support
- Recurring transactions

## License

MIT License

## Support

For issues or questions, please contact the development team.

---

تم التطوير بواسطة Claude Code
Developed with Claude Code
