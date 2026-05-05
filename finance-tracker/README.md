# 💰 Finance Tracker — Improved Fork

> **Original project:** [ARWA044/finance-tracker](https://github.com/ARWA044/finance-tracker)
> **Improvements by:** Course assignment fork — May 2026

A modern Django personal finance application. This fork adds two major improvements
on top of the original codebase:

---

## ✨ Improvements Added

### 💰 Financial Improvement — Budget Limits & Overspend Alerts
- New `BudgetLimit` model: set a monthly spending cap per category
- Dashboard shows colour-coded progress bars (🟢 ok / 🟡 warning at 80% / 🔴 danger at 100%+)
- Amber alert banner appears at the top of the dashboard when any category is overspent
- Full CRUD: `/budgets/` (list, add, edit, delete)

### ⚙️ Technical Improvement — Recurring Transactions Engine
- New `RecurringTransaction` model: store repeating rules (daily/weekly/monthly/yearly)
- Django management command `generate_recurring` creates Transaction records for all overdue rules
- Uses `python-dateutil` for correct month-end arithmetic (e.g. 31 Jan + 1 month → 28 Feb)
- Dashboard shows an **Upcoming (30 days)** panel listing approaching recurring items
- Full CRUD: `/recurring/` (list, add, edit, delete)
- **PythonAnywhere cron setup:**
  ```
  0 6 * * *  /home/<username>/.virtualenvs/<venv>/bin/python /home/<username>/finance-tracker/manage.py generate_recurring
  ```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, django-allauth, django-filter, django-import-export |
| Frontend | Tailwind CSS, DaisyUI, HTMX, Alpine.js, Plotly.js |
| Database | SQLite (dev) / PostgreSQL (production) |
| Config | python-decouple (`.env` secrets) |
| Testing | pytest |
| Hosting | PythonAnywhere |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone <this-repo-url>
cd finance-tracker

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env        # then edit SECRET_KEY etc.

# 5. Migrate (includes BudgetLimit + RecurringTransaction tables)
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run
python manage.py runserver
```

Visit http://127.0.0.1:8000/

---

## 📁 Project Structure

```
finance-tracker/
├── manage.py
├── requirements.txt          # Added python-dateutil
├── build.sh                  # PythonAnywhere deploy script
├── pytest.ini
├── monprojet/                # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── expenses/                 # Main application
    ├── models.py             # ★ BudgetLimit + RecurringTransaction added here
    ├── views.py              # ★ Budget & Recurring CRUD + Dashboard extensions
    ├── forms.py              # ★ BudgetLimitForm + RecurringTransactionForm
    ├── urls.py               # ★ /budgets/ and /recurring/ routes added
    ├── filters.py
    ├── admin.py              # ★ All 4 models registered with admin actions
    ├── resources.py          # CSV import/export
    ├── management/
    │   └── commands/
    │       └── generate_recurring.py  # ★ Recurring engine command
    ├── migrations/
    │   └── 0001_initial.py   # ★ All 4 models in one migration
    └── templates/expenses/
        ├── base.html
        ├── dashboard.html    # ★ Alert banner + budget bars + upcoming panel
        ├── budget_list.html  # ★ New
        ├── budget_form.html  # ★ New
        ├── recurring_list.html # ★ New
        ├── recurring_form.html # ★ New
        ├── transaction_list.html
        ├── transaction_form.html
        ├── category_list.html
        ├── category_form.html
        ├── charts.html
        └── confirm_delete.html
```

---

## 🧪 Running Tests

```bash
pytest
```

To test the recurring command manually:
```bash
python manage.py generate_recurring --dry-run   # preview
python manage.py generate_recurring             # execute
```

---

## 📄 Licence

MIT — see [LICENSE](LICENSE)
