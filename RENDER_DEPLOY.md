# Deploying the Python Email System on Render

This repository now includes a small Flask application that can run the Python Email System online.

## Files added

- `app.py`: Flask backend with the `Email`, `User` and `Inbox` classes.
- `templates/email_system.html`: interactive browser UI.
- `requirements.txt`: Python dependencies.
- `render.yaml`: Render Blueprint configuration.

## Render deployment

1. Open Render.
2. Create a new Web Service or Blueprint from this GitHub repository.
3. Use the following settings if Render asks for them manually:

```text
Language: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Health Check Path: /healthz
```

The included `render.yaml` already defines these values.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5000
```

## Important note

This is a portfolio demo. Messages are stored in memory per browser session. They are not persisted in a database and will disappear when the Render service restarts.
