import csv
import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from io import StringIO

from flask import (
    Flask,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "finanzas.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "cambia-esta-clave-en-produccion")
app.config["INVITE_CODE"] = os.getenv("APP_INVITE_CODE", "finanzas-privadas")
app.config["DEBUG"] = os.getenv("APP_DEBUG", "false").lower() == "true"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
            note TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    db.close()


def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)


def validate_csrf_token():
    token = request.form.get("csrf_token", "")
    if not token or token != session.get("csrf_token"):
        flash("Token de seguridad inválido. Recarga la página e intenta de nuevo.")
        return False
    return True


@app.before_request
def bootstrap_request_context():
    init_db()
    ensure_csrf_token()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Inicia sesión para continuar.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("register.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        invite_code = request.form.get("invite_code", "")

        if len(username) < 3:
            flash("El usuario debe tener al menos 3 caracteres.")
            return render_template("register.html")
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.")
            return render_template("register.html")
        if invite_code != app.config["INVITE_CODE"]:
            flash("Código de invitación inválido.")
            return render_template("register.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), datetime.utcnow().isoformat()),
            )
            db.commit()
            flash("Cuenta creada. Ahora inicia sesión.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Ese usuario ya existe.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            ensure_csrf_token()
            return redirect(url_for("dashboard"))

        flash("Credenciales inválidas.")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    if not validate_csrf_token():
        return redirect(url_for("dashboard"))

    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, date, category, amount, kind, note
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        """,
        (session["user_id"],),
    ).fetchall()

    income_total = sum(r["amount"] for r in rows if r["kind"] == "income")
    expense_total = sum(r["amount"] for r in rows if r["kind"] == "expense")
    balance = income_total - expense_total

    by_category = {}
    for r in rows:
        sign = 1 if r["kind"] == "income" else -1
        by_category[r["category"]] = by_category.get(r["category"], 0) + (sign * r["amount"])

    return render_template(
        "dashboard.html",
        rows=rows,
        income_total=income_total,
        expense_total=expense_total,
        balance=balance,
        by_category=sorted(by_category.items(), key=lambda x: abs(x[1]), reverse=True),
    )


@app.route("/transactions/new", methods=["POST"])
@login_required
def new_transaction():
    if not validate_csrf_token():
        return redirect(url_for("dashboard"))

    date = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    kind = request.form.get("kind", "").strip()
    note = request.form.get("note", "").strip()

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("El monto debe ser un número positivo.")
        return redirect(url_for("dashboard"))

    if kind not in {"income", "expense"}:
        flash("Tipo de movimiento inválido.")
        return redirect(url_for("dashboard"))

    if not date:
        date = datetime.now().date().isoformat()

    db = get_db()
    db.execute(
        """
        INSERT INTO transactions (user_id, date, category, amount, kind, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session["user_id"], date, category or "Sin categoría", amount, kind, note),
    )
    db.commit()

    flash("Movimiento guardado.")
    return redirect(url_for("dashboard"))


@app.route("/transactions/<int:tx_id>/delete", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    if not validate_csrf_token():
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, session["user_id"]))
    db.commit()
    flash("Movimiento eliminado.")
    return redirect(url_for("dashboard"))


@app.route("/transactions/export.csv")
@login_required
def export_transactions_csv():
    db = get_db()
    rows = db.execute(
        """
        SELECT date, category, amount, kind, note
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        """,
        (session["user_id"],),
    ).fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha", "categoria", "monto", "tipo", "nota"])
    for row in rows:
        writer.writerow([row["date"], row["category"], f"{row['amount']:.2f}", row["kind"], row["note"] or ""])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=movimientos.csv"
    return response


if __name__ == "__main__":
    init_db()
    app.run(debug=app.config["DEBUG"])
