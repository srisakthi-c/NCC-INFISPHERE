from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from collections import defaultdict
from flask import abort
import os

# -------------------- APP CONFIG --------------------

app = Flask(__name__)
app.secret_key = "ncc_secret_key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ncc.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---- MODELS HERE ----

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

# ---- ROUTES START HERE ----

# -------------------- DATABASE MODELS --------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / cadet
    rank = db.Column(db.String(50), default="Recruit")
    achievements = db.Column(db.Text)
    attendance_section1 = db.Column(db.Integer, default=0)
    attendance_section2 = db.Column(db.Integer, default=0)
    profile_image = db.Column(db.String(200), default="default.png")


class Parade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    details = db.Column(db.String(200))


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    image_filename = db.Column(db.String(200))


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    details = db.Column(db.Text)
    image = db.Column(db.String(200))
    cadet_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    cadet_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    file = db.Column(db.String(200))


# -------------------- INITIALIZE DATABASE --------------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="srcasnccedu@gmail.com").first():
        db.session.add(User(
            name="Admin",
            email="srcasnccedu@gmail.com",
            password="Srcasncc@2024",
            role="admin",
            rank="Captain"
        ))

    if not User.query.filter_by(email="cadet@ncc.in").first():
        db.session.add(User(
            name="Test Cadet",
            email="cadet@ncc.in",
            password="cadet123",
            role="cadet",
            rank="Lance Corporal"
        ))

    db.session.commit()

# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = User.query.filter_by(email=email, role=role).first()

        if user and user.password == password:
            login_user(user)
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for(
                "admin_dashboard" if role == "admin" else "cadet_dashboard"
            ))
        else:
            flash("Invalid login details", "danger")

    return render_template("login.html")

# -------------------- LOGOUT --------------------
from flask_login import logout_user

@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))
# -------------------- HOME --------------------
@app.route("/")
def home():
    cadets = User.query.filter_by(role="cadet").all()
    events = Event.query.all()
    parades = Parade.query.all()
    achievements = Achievement.query.all()

    # 🔹 Rank-wise grouping (rank appears only once)
    rank_map = defaultdict(list)
    for cadet in cadets:
        if cadet.rank:
            rank_map[cadet.rank].append(cadet)

    return render_template(
        "home.html",
        college_name="Sri Ramakrishna College of Arts & Science",
        ncc_unit="Unit 6 Tamil Nadu Medical Company NCC",
        captain_info="Captain Vivek E",
        total_cadets=len(cadets),

        # existing data (NOT REMOVED)
        cadets=cadets,
        parades=parades,
        events=events,
        achievements=achievements,

        # ✅ NEW (for rank shown once with hover)
        rank_map=rank_map
    )

# -------------------- ADMIN DASHBOARD --------------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    admin = User.query.get(session["user_id"])   # ✅ ADD THIS
    cadets = User.query.filter_by(role="cadet").all()
    achievements = Achievement.query.all()
    events = Event.query.all()

    return render_template(
        "admin_dashboard.html",
        admin=admin,            # ✅ PASS IT
        cadets=cadets,
        achievements=achievements,
        events=events
    )

@app.route("/admin/add-parade", methods=["POST"])
def add_parade():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    parade = Parade(
        date=request.form.get("date"),
        details=request.form.get("details")
    )
    db.session.add(parade)
    db.session.commit()

    flash("Parade scheduled successfully", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add-cadet", methods=["POST"])
def add_cadet():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    db.session.add(User(
        name=request.form["name"],
        email=request.form["email"],
        password=request.form["password"],
        role="cadet"
    ))
    db.session.commit()

    flash("Cadet added successfully", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete-cadet/<int:cadet_id>")
def delete_cadet(cadet_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    cadet = User.query.get_or_404(cadet_id)

    # delete cadet documents
    Document.query.filter_by(cadet_id=cadet.id).delete()
    Achievement.query.filter_by(cadet_id=cadet.id).delete()

    db.session.delete(cadet)
    db.session.commit()

    flash("Cadet deleted successfully", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/assign-rank/<int:cadet_id>", methods=["POST"])
def assign_rank(cadet_id):
    cadet = User.query.get_or_404(cadet_id)
    cadet.rank = request.form["rank"]
    db.session.commit()
    flash("Rank updated", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/mark-attendance/<int:cadet_id>", methods=["POST"])
@login_required
def mark_attendance(cadet_id):
    # Allow only admin
    if session.get("role") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login"))

    cadet = User.query.get_or_404(cadet_id)

    # Safely read form values
    section1 = request.form.get("section1")
    section2 = request.form.get("section2")

    # Convert safely (handles empty strings)
    section1 = int(section1) if section1 and section1.isdigit() else 0
    section2 = int(section2) if section2 and section2.isdigit() else 0

    # Update attendance
    cadet.attendance_section1 += section1
    cadet.attendance_section2 += section2

    db.session.commit()

    flash("Attendance updated successfully", "success")
    return redirect(url_for("admin_dashboard"))


# -------------------- CADET ADD ACHIEVEMENT --------------------
@app.route("/admin/add-achievement/<int:cadet_id>", methods=["POST"])
@login_required
def admin_add_achievement(cadet_id):

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files.get("image")

    filename = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    achievement = Achievement(
        title=title,
        details=description,
        image=filename,
        cadet_id=cadet_id
    )

    db.session.add(achievement)
    db.session.commit()

    flash("Achievement added successfully", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-event", methods=["POST"])
@login_required
def add_event():
    if session.get("role") != "admin":
        abort(403)

    title = request.form.get("title")
    image = request.files.get("image")

    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        event = Event(title=title, image_filename=filename)
        db.session.add(event)
        db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete-event/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    if session.get("role") != "admin":
        abort(403)

    event = Event.query.get_or_404(event_id)

    image_path = os.path.join(app.config["UPLOAD_FOLDER"], event.image_filename)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(event)
    db.session.commit()

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-material", methods=["POST"])
@login_required
def add_material():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    title = request.form.get("title")
    pdf = request.files.get("file")

    if pdf and pdf.filename.endswith(".pdf"):
        filename = secure_filename(pdf.filename)
        pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        mat = StudyMaterial(title=title, file=filename)
        db.session.add(mat)
        db.session.commit()

    return redirect(url_for("admin_dashboard"))

# -------------------- CADET DASHBOARD --------------------
@app.route("/cadet/dashboard")
@login_required
def cadet_dashboard():
    if session.get("role") != "cadet":
        return redirect(url_for("login"))

    user = User.query.get_or_404(session["user_id"])
    documents = Document.query.filter_by(cadet_id=user.id).all()
    parades = Parade.query.all()
    materials = StudyMaterial.query.all()

    return render_template(
        "cadet_dashboard.html",
        user=user,
        documents=documents,
        parades=parades,
        materials=materials
    )

@app.route("/cadet/add-achievement", methods=["POST"])
@login_required
def cadet_add_achievement():
    if current_user.role != "cadet":
        return redirect(url_for("login"))

    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files.get("image")

    filename = None
    if image and image.filename != "":
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    achievement = Achievement(
        title=title,
        details=description,
        image=filename,
        cadet_id=current_user.id
    )

    db.session.add(achievement)
    db.session.commit()

    flash("Achievement added successfully", "success")
    return redirect(url_for("cadet_dashboard"))


# -------------------- UPDATE PROFILE --------------------
@app.route("/cadet/profile", methods=["GET", "POST"])
@login_required
def cadet_profile():
    if "user_id" in session:
        user = User.query.get(session["user_id"])

        if request.method == "POST":
            user.name = request.form.get("name")
            user.rank = request.form.get("rank")

            photo = request.files.get("photo")
            if photo and photo.filename != "":
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                user.profile_image = filename

            db.session.commit()
            flash("Profile updated successfully", "success")
            return redirect(url_for("cadet_profile"))

        return render_template("cadet_profile.html", user=user)

    return redirect(url_for("login"))




# -------------------- DOCUMENT UPLOAD --------------------
@app.route("/cadet/upload-document", methods=["POST"])
def upload_document():
    if session.get("role") != "cadet":
        return redirect(url_for("login"))

    file = request.files.get("document")
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.add(Document(
            cadet_id=session["user_id"],
            filename=filename
        ))
        db.session.commit()

    flash("Document uploaded successfully", "success")
    return redirect(url_for("cadet_dashboard"))

@app.route("/admin/documents")
@login_required
def admin_documents():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    documents = db.session.query(Document, User).join(User).all()
    return render_template("admin_documents.html", documents=documents)

# -------------------- RUN --------------------
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=10000)
