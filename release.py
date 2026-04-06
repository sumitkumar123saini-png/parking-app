"""Railway release phase: create tables and apply lightweight schema patches."""
from app import app, db, ensure_schema

with app.app_context():
    db.create_all()
    ensure_schema()
    print("Database ready.")
