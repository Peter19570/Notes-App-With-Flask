# Simple Notes App with user authentication
from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "peter_simple_notes_app"
DB_NAME = "notes.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    notes = db.relationship("Note", backref="author", lazy=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(2000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    date_created = db.Column(db.DateTime, default=datetime.now())


@login_manager.user_loader
def check_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["POST", "GET"])
@login_required
def home():
    if request.method == "POST":
        text = request.form["text"]
        new_note = Note(text=text, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        return redirect("/")
    return render_template("note.html", user=current_user)


@app.route("/sign-up", methods=["POST", "GET"])
def sign_up():
    if request.method == "POST":
        fullname = request.form["fullname"]
        username = request.form["username"].lower().strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            print("User already exists !")
            return redirect("/sign-up")

        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect("/")
    return render_template("sign_up.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        info = request.form["info"].lower().strip()
        password = request.form["password"].strip()
        user = User.query.filter((User.username == info) | (User.email == info)).first()
        if not user:
            print("Use does not exist !")
            return redirect("/login")
        if not check_password_hash(user.password, password):
            print("Incorrect Password !")
            return redirect("/login")
        login_user(user)
        return redirect("/")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/delete-note/<int:note_id>")
@login_required
def delete_note(note_id):
    note = Note.query.get(int(note_id))
    if not note.user_id == current_user.id:
        print("Not Allowed")
        return redirect("/")
    db.session.delete(note)
    db.session.commit()
    return redirect("/")


@app.route("/update-note/<int:note_id>")
@login_required
def update_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        print("Not Allowed")
        return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
