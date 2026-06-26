# MEN AND WOMEN OF PASSION AND PURPOSE

A modern full-stack ministry web application built with Flask, TailwindCSS, and JavaScript.

## Features

- Modular Flask architecture with Blueprints
- Authentication (register/login/logout) with Flask-Login
- Secure forms with Flask-WTF + CSRF protection
- SQLAlchemy models for users, sermons, prayers, classes, assignments, submissions, donations, applications
- Admin dashboard with role-based protection
- Sermon search and category filter
- Prayer request submission
- Ministry school classes and assignments flow
- Online giving flow (Paystack-ready service integration)
- Member dashboard and profile update
- Responsive modern UI with smooth animations
- Custom error pages (404, 500)

## Project Structure

\`\`\`
ministry_project/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── forms.py
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── database/
├── config.py
├── run.py
├── requirements.txt
└── README.md
\`\`\`

## Setup (VS Code)

1. Open \`ministry_project\` in VS Code terminal.
2. Create virtual environment:
   \`\`\`bash
   python -m venv .venv
   \`\`\`
3. Activate virtual environment (Windows):
   \`\`\`bash
   .venv\Scripts\activate
   \`\`\`
4. Install dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`
5. Run app:
   \`\`\`bash
   python run.py
   \`\`\`
6. Visit:
   \`http://127.0.0.1:5000\`

## REST API (Flutter Mobile Integration)

Base URL: `http://127.0.0.1:5000/api/v1`

All responses follow: `{ "success": true|false, "message": "...", "data": ... }`

### Public Endpoints (GET)

| Endpoint | Description |
|---|---|
| `/api/v1/health` | API health check |
| `/api/v1/ministry` | Ministry info, mission, vision, contact, app download links |
| `/api/v1/sermons` | List sermons (`?q=`, `?category=`, `?limit=`) |
| `/api/v1/sermons/<id>` | Single sermon |
| `/api/v1/leaders` | List all leaders |
| `/api/v1/leaders/<id>` | Single leader |
| `/api/v1/gallery` | Gallery images (`?category=`, `?featured=1`, `?limit=`) |
| `/api/v1/gallery/<id>` | Single gallery image |
| `/api/v1/courses` | Ministry school courses |

### Write Endpoints (POST, optional API key)

Set `API_KEY` env var and pass header `X-API-Key: <your-key>`.

| Endpoint | Body (JSON) |
|---|---|
| `/api/v1/prayer-requests` | `{ "name", "email", "request" }` |
| `/api/v1/contact` | `{ "name", "email", "message" }` |

CORS is enabled for all `/api/*` routes.

## Environment Variables (Optional)

- \`SECRET_KEY\`
- \`DATABASE_URL\`
- \`MAIL_SERVER\`
- \`MAIL_PORT\`
- \`MAIL_USERNAME\`
- \`MAIL_PASSWORD\`
- \`MAIL_DEFAULT_SENDER\`
- \`PAYSTACK_SECRET_KEY\`
- \`PAYSTACK_PUBLIC_KEY\`
- \`FLUTTERWAVE_SECRET_KEY\`
- \`APP_STORE_URL\`
- \`PLAY_STORE_URL\`
- \`MINISTRY_EMAIL\`
- \`MINISTRY_PHONE\`
- \`MINISTRY_ADDRESS\`
- \`API_KEY\`

## Logging

- Persistent application logs are written to:
  - `ministry_project/logs/app.log`
- Log rotation is enabled:
  - Max size per file: 1 MB
  - Backup files kept: 5
- Logged events include:
  - User registration attempts and success
  - Login success/failure
  - Logout events
  - Admin page access and key admin actions (create/delete sermon, promote user)

## Notes

- SQLite is used for development.
- Payment callback verification should be expanded for production.
- File uploads are scaffolded and can be connected to persistent storage.
