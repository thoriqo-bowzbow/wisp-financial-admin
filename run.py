from app import app, db, bcrypt
from app.models import User
import click

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

@app.cli.command("create-user")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def create_user(username, email, password):
    """Membuat user admin baru."""
    if User.query.filter_by(email=email).first():
        print(f"Error: Email '{email}' sudah terdaftar.")
        return
    if User.query.filter_by(username=username).first():
        print(f"Error: Username '{username}' sudah terdaftar.")
        return

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    print(f"User '{username}' berhasil dibuat.")

if __name__ == '__main__':
    app.run(debug=True)
