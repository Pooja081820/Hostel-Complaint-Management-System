# FULL ADVANCED HOSTEL COMPLAINT MANAGEMENT SYSTEM — BEGINNER GUIDE

You selected **Option B**: keep the advanced project and its features, but learn it in simple language.

This folder contains the original project's Python, HTML, CSS, JavaScript and SQL files. The source is preserved so that the pages, routes and database continue to match. The guide explains the purpose of each part and how to run it.

> Accuracy note: the project has **17 Python files**, 27 HTML templates, one CSS file, one JavaScript file and six full-database SQL scripts plus one separate learning SQL script. The original `.env` file is intentionally not included because it may contain a private database password. Use `.env.example` to create your own `.env`.

---

## 1. What the application does

The system manages hostel maintenance complaints from start to finish:

1. A student registers and logs in.
2. The student submits a complaint, selects a category and can attach evidence.
3. The system creates a ticket number and saves the complaint in MySQL.
4. A warden reviews complaints for the hostel(s) assigned to them.
5. The warden assigns a technician and can set priority or add a response.
6. The technician views assigned work and updates progress.
7. The warden checks the completed work and resolves or rejects it.
8. The student can see the history and provide feedback.
9. Admin manages users, hostels, rooms, complaint categories and reports.

User roles:
- `student`
- `warden`
- `staff`
- `admin`

## 2. Understand the folders

| Folder/file | Simple meaning |
|---|---|
| `app.py` | Starts the Flask website and registers all route groups |
| `config.py` | Reads application and MySQL settings |
| `db.py` | Connects to MySQL and runs SQL queries safely |
| `init_db.py` | Runs the full database setup scripts |
| `routes/` | Receives browser requests and returns pages |
| `services/` | Contains the main complaint, assignment, admin and notification rules |
| `utils/` | Reusable login, role, security and form-validation helpers |
| `templates/` | HTML pages shown in the browser |
| `static/css/` | Website styling |
| `static/js/` | Browser-side JavaScript |
| `database/` | SQL tables, sample data, triggers, procedures and views |
| `tests/` | Automated checks for features |

## 3. Python files explained simply

### Main files

#### `app.py`
This is the entry point. The function `create_app()`:
- creates the Flask application;
- loads settings from `Config`;
- prepares the upload folder and database pool;
- registers route Blueprints for authentication, students, wardens, staff, admin and notifications;
- sets error pages;
- returns the Flask application.

Run this file to start the website:

```bash
python app.py
```

#### `config.py`
The `Config` class stores settings in one place. It reads values such as:
- MySQL host, port, username, password and database name;
- Flask secret key;
- upload folder and maximum upload size;
- allowed file types.

The `.env` file supplies private values. Do not upload or share it.

#### `db.py`
This file is the bridge between Python and MySQL.

Important functions:
- `init_db_pool()` — creates a pool of reusable MySQL connections.
- `get_pool()` — returns the pool.
- `get_db_connection()` — borrows a connection and returns it to the pool afterwards.
- `get_db_cursor()` — creates a cursor and handles commit/rollback.
- `query_one(sql, params)` — runs a SELECT and returns one row.
- `query_all(sql, params)` — runs a SELECT and returns many rows.
- `execute_dml(sql, params)` — runs INSERT, UPDATE or DELETE and returns affected rows and inserted ID.

Simple example of the idea:

```python
from db import query_one

student = query_one(
    "SELECT * FROM students WHERE student_id = %s",
    (1,)
)

print(student)
```

`%s` is a placeholder. The value is passed separately. This is safer than joining user text into SQL.

#### `init_db.py`
This runs the full database setup scripts in the correct order:
1. `schema.sql`
2. `triggers.sql`
3. `procedures.sql`
4. `views.sql`
5. `seed.sql`

**Warning:** `schema.sql` drops and recreates existing tables, and the seed script repopulates demo data. Use a fresh practice database or back up your database first. Do not run initialization on a database containing real records.

### Route files — browser pages and actions

A route is a Python function that runs when a browser visits a URL or submits a form.

#### `routes/auth.py`
Handles:
- login;
- student registration;
- retrieving rooms for a selected hostel;
- logout.

It checks submitted details, verifies the password hash and stores the user's login information in the Flask session.

#### `routes/student.py`
Handles the student area:
- dashboard and complaint totals;
- submitting a complaint;
- checking possible duplicate complaints;
- viewing the student's complaints and complaint details;
- cancelling or reopening a complaint when allowed;
- submitting feedback;
- viewing and marking notifications.

#### `routes/warden.py`
Handles the warden area:
- dashboard;
- complaint list and filters;
- checking that the warden is assigned to the hostel;
- assigning staff;
- changing priority;
- adding responses;
- resolving or rejecting complaints;
- reports and CSV export.

#### `routes/staff.py`
Handles the technician/staff area:
- assigned task dashboard;
- task detail;
- accepting a task;
- adding work notes;
- marking work complete and attaching proof;
- viewing work history.

#### `routes/admin.py`
Handles system administration:
- admin dashboard;
- user creation and activation/deactivation;
- hostel management;
- warden-to-hostel assignment;
- room management;
- complaint category and SLA management;
- all-complaint view;
- complaint responses and priority changes;
- audit logs;
- CSV export.

#### `routes/notifications.py`
Shows notifications, marks them read and provides notification polling.

### Service files — the business rules

A route should mostly handle the web request. A service performs the main application work.

#### `services/complaint_service.py`
The main complaint workflow:
- generates ticket numbers;
- checks for similar active complaints;
- creates a complaint and calculates its SLA deadline;
- records history and attachments;
- updates complaint state safely;
- checks ownership and permitted actions.

#### `services/assignment_service.py`
Handles assigning a complaint to a staff member and managing the assignment lifecycle.

#### `services/admin_service.py`
Contains reusable admin operations for users, hostels, rooms, categories and management data.

#### `services/notification_service.py`
Creates and retrieves notifications for users.

### Utility files — reusable helpers

#### `utils/decorators.py`
Contains decorators:
- `login_required` — only logged-in users may continue;
- `role_required` — only users with allowed roles may continue;
- `log_audit_event` — records important actions for auditing.

A decorator is a check placed above a route. For example, a warden-only route checks the user's role before running.

#### `utils/security.py`
Contains:
- password hashing;
- password verification;
- CSRF token creation and checking;
- allowed file extension checks;
- safe upload saving.

Passwords must be stored as hashes, not plain text.

#### `utils/validators.py`
Checks registration and complaint form values before saving them to the database.

### Test files

| Test file | What it checks |
|---|---|
| `tests/test_auth.py` | Login and registration |
| `tests/test_complaints.py` | Complaint workflow |
| `tests/test_database.py` | Database operations |
| `tests/test_permissions.py` | Login and role permissions |
| `tests/test_admin.py` | Admin operations |
| `tests/test_staff.py` | Staff operations |
| `tests/test_warden.py` | Warden operations |

Run tests from the project root:

```bash
python -m unittest discover tests -v
```

Tests may require a configured test database. Do not point tests at a database containing important real data.

---

## 4. HTML, CSS and JavaScript explained

### HTML templates

The `templates/` folder has 27 HTML files. Flask uses these templates to build the pages.

| File/folder | Purpose |
|---|---|
| `templates/base.html` | Shared page layout, navigation and common design |
| `templates/auth/login.html` | Login form |
| `templates/auth/register.html` | Registration form |
| `templates/student/` | Student dashboard, submit form, complaint list, detail and notifications |
| `templates/warden/` | Warden dashboard, complaints, detail and reports |
| `templates/staff/` | Staff dashboard, task details and history |
| `templates/admin/` | Admin dashboard, users, hostels, rooms, categories, complaints and audit logs |
| `templates/notifications.html` | Shared notifications page |
| `templates/errors/` | 403, 404 and 500 error pages |

Important Flask template symbols:
- `{{ variable }}` displays a value sent from Python.
- `{% if condition %}` shows content only when a condition is true.
- `{% for item in items %}` repeats HTML for each item.
- `{% extends "base.html" %}` reuses the shared page layout.
- `{% block content %}` marks a section filled in by a child template.
- `url_for(...)` creates a URL for a Flask route.

Example:

```html
<h2>Welcome, {{ user_name }}</h2>

{% for complaint in complaints %}
  <p>{{ complaint.title }} - {{ complaint.status }}</p>
{% endfor %}
```

### CSS

`static/css/style.css` controls:
- colours and fonts;
- page layout;
- cards and dashboard panels;
- buttons and forms;
- tables;
- responsive layout for smaller screens.

HTML describes the page content. CSS controls how it looks.

### JavaScript

`static/js/main.js` handles browser interactions such as menu behavior, confirmation prompts, notification polling or other client-side behavior. Python and MySQL still handle the important data and permissions.

**Do not open a Flask template directly by double-clicking it.** It contains Flask template tags. Start the Flask server and view the rendered page in your browser.

---

## 5. Full database: the correct database for Option B

Use the database named `hostel_complaint_db` and the full `database/schema.sql` file for the supplied advanced Flask application.

The full database contains 18 tables:

1. `users` — all login accounts and roles.
2. `hostels` — hostel blocks.
3. `rooms` — rooms inside hostels.
4. `students` — student profile and room details.
5. `wardens` — warden profile details.
6. `staff` — maintenance staff profile details.
7. `hostel_wardens` — which wardens manage which hostels.
8. `complaint_categories` — categories and default SLA/priority.
9. `complaints` — main complaint tickets and current status.
10. `complaint_affected_hostels` — hostels affected by general complaints.
11. `complaint_assignments` — technician work assignments.
12. `complaint_responses` — comments and official updates.
13. `complaint_history` — status change history.
14. `complaint_priority_history` — priority change reasons.
15. `complaint_attachments` — uploaded evidence and proof file details.
16. `notifications` — user notifications.
17. `complaint_feedback` — student rating and feedback.
18. `audit_logs` — records important system actions.

### Run the full database using MySQL Workbench

Recommended beginner method:

1. Start MySQL Server.
2. Open MySQL Workbench and connect to your local server.
3. Create a backup if you already have a database with data.
4. Open the project folder in VS Code and set your `.env` values.
5. Run the database initializer from the terminal:

```bash
python init_db.py
```

This initializer connects to the MySQL server and executes the five full SQL setup files in the correct order. It does not use the small learning database.

You can also open the SQL files individually in Workbench and execute them in this order:
1. `database/schema.sql`
2. `database/triggers.sql`
3. `database/procedures.sql`
4. `database/views.sql`
5. `database/seed.sql`

The `reports.sql` file is an additional reporting script, not part of the initializer's standard sequence. Read it before executing.

### Check that the full database was created

Run in Workbench:

```sql
USE hostel_complaint_db;
SHOW TABLES;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM complaints;
SELECT * FROM vw_complaint_full_details;
```

### About the simple learning database

`database/simple_learning_database.sql` creates a separate five-table practice database called `hostel_complaint_simple`.

It is useful for learning basic SQL, but **do not use it to run Option B**. The advanced Flask code expects the 18-table `hostel_complaint_db` schema and its exact column names.

---

## 6. Connect the Flask application to MySQL

### Step A — create your private `.env`

Copy `.env.example` to a new file named `.env` in the same folder as `app.py`.

Edit the values to match your MySQL installation. Example only:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=PUT_YOUR_MYSQL_PASSWORD_HERE
DB_NAME=hostel_complaint_db
SECRET_KEY=MAKE_A_LONG_RANDOM_SECRET
```

Use your own password. Do not paste your password into public messages or upload `.env` to GitHub.

### Step B — install Python packages

Windows PowerShell, from the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, you can use Command Prompt:

```bat
venv\Scripts\activate.bat
```

### Step C — initialize the full database

```bash
python init_db.py
```

Only do this with a new/test database or after a backup because setup scripts recreate tables and sample records.

### Step D — start the website

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 7. Simple MySQL examples for learning

See sample users:

```sql
USE hostel_complaint_db;

SELECT user_id, email, role
FROM users;
```

See complaints:

```sql
SELECT complaint_id, ticket_number, title, status, priority
FROM complaints;
```

Count complaints by status:

```sql
SELECT status, COUNT(*) AS total
FROM complaints
GROUP BY status;
```

See a student's complaints (replace `1` with a real student ID):

```sql
SELECT *
FROM complaints
WHERE student_id = 1;
```

Update a complaint status only as a database practice example. In the actual application, use the authorized Flask workflow so history and audit records are maintained:

```sql
UPDATE complaints
SET status = 'Under Review'
WHERE complaint_id = 1;
```

---

## 8. Beginner glossary

| Word | Easy meaning |
|---|---|
| Flask | Python tool used to build the website |
| Route | URL and Python function that handles it |
| Blueprint | A group of related routes |
| Template | HTML page that Flask fills with data |
| Session | Remembers which user is logged in |
| Database | Organized place to store information |
| Table | Data arranged in rows and columns |
| Primary key | Unique ID for a row |
| Foreign key | Link from one table to another |
| SQL query | Instruction sent to MySQL |
| Cursor | Object used to execute SQL |
| Commit | Save a database transaction |
| Rollback | Undo a transaction that failed |
| Service | Python code containing the main business rules |
| Decorator | A check that runs before a function |
| Validation | Checking that input is acceptable |
| Hashing | One-way transformation used to store passwords safely |
| CSRF token | A security value that helps protect form submissions |
| SLA | Target time allowed to resolve a complaint |

## 9. Recommended learning order

Do not try to memorize all files at once. Study in this order:

1. `config.py` — application settings.
2. `db.py` — how Python talks to MySQL.
3. `app.py` — how Flask starts and loads route groups.
4. `database/schema.sql` — how the tables connect.
5. `routes/auth.py` and `utils/security.py` — login and password safety.
6. `routes/student.py` — how students submit complaints.
7. `services/complaint_service.py` — how complaint records are created and updated.
8. `routes/warden.py` and `services/assignment_service.py` — assignment and resolution.
9. `routes/staff.py` — technician work.
10. `routes/admin.py` and `services/admin_service.py` — system administration.
11. HTML templates, CSS and JavaScript — how the pages are displayed.
12. Tests — how to check that the system behaves correctly.

## 10. Important project safety notes

- The original `.env` file is not included in this pack; create your own from `.env.example`.
- Change the default demo passwords and Flask secret key before real deployment.
- Do not run the database initializer against a database containing important data.
- Do not trust a hidden button as a security check; the Python route must check the user's role and ownership.
- Keep uploaded files restricted to allowed types and sizes.
- Use the existing service functions for complaint updates so status history, notifications and audit records are not bypassed.

This package preserves the supplied application source. It is a learning and setup guide, not a claim that every original Python function has already been rewritten into shorter code. A safe beginner-friendly rewrite should be done module by module and tested against the full 18-table schema.
