from app import app, db, User  # import your Flask app, database, and User model
from werkzeug.security import generate_password_hash

def create_default_admin():
    # Must run inside app context
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username="admin").first()
        if admin:
            print("Admin user already exists.")
            return

        # Create default admin
        default_admin = User(
            username="admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password=generate_password_hash("Admin123!"),  # change password if you like
            is_admin=True
        )
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin user created successfully!")

if __name__ == "__main__":
    create_default_admin()
