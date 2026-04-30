# Task Management System

Full-stack task management application built for the assignment criteria:

- React.js frontend
- Django + Django REST Framework backend
- PostgreSQL-ready database configuration
- Admin and intern roles
- Task assignment, status updates, progress tracking, comments, dashboards, smart alerts, activity logs, search, and filters

## Single-server setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For PostgreSQL, set these environment variables before running migrations:

```powershell
$env:DB_ENGINE="django.db.backends.postgresql"
$env:DB_NAME="taskmanager"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
```

If those variables are not set, the project falls back to SQLite for local development.

```powershell
python manage.py migrate
```

If the browser shows database errors such as `no such table: tasks_task`, stop the server, run `python manage.py migrate`, and start `python manage.py runserver` again.

Build React once, then run only the Django server:

```powershell
cd frontend
npm install
npm run build
cd ..
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Django serves both the React frontend and the `/api/` backend from the same server.

This workspace also includes a ready-to-use `.venv312` environment. You can start the merged app with:

```powershell
.\run_server.bat
```

## Optional separate frontend setup

For React-only development, you can still run:

```powershell
cd frontend
npm start
```

When React runs on port 3000, it expects the API at `http://localhost:8000/api`. Override it with:

```powershell
$env:REACT_APP_API_BASE="http://localhost:8000/api"
```

## Main API endpoints

- `POST /api/auth/signup/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `GET/POST /api/tasks/`
- `GET/PUT/DELETE /api/tasks/<id>/`
- `POST /api/tasks/<id>/comment/`
- `GET /api/dashboard/`
- `GET /api/alerts/`
- `GET /api/activity-logs/`
