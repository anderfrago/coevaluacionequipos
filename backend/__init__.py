import os
import secrets
from datetime import timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request, send_from_directory, session
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException

from .models import User, db


@event.listens_for(Engine, "connect")
def enable_foreign_keys(connection, _):
    if connection.__class__.__module__.startswith("sqlite3"):
        connection.execute("PRAGMA foreign_keys=ON")


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///coevaluacion.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        BASE_URL=os.getenv("BASE_URL", "http://localhost:5000").rstrip("/"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "true").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=128 * 1024,
        ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", "ander_frago@cuatrovientos.org").lower(),
        TEACHER_DOMAIN=os.getenv("TEACHER_DOMAIN", "cuatrovientos.org").strip().lower(),
        STUDENT_DOMAINS={
            domain.strip().lower()
            for domain in os.getenv("STUDENT_DOMAINS", "cuatrovientos.org,gmail.com").split(",")
            if domain.strip()
        },
        RETENTION_DAYS=os.getenv("RETENTION_DAYS", ""),
        PRIVACY_CONTROLLER=os.getenv("PRIVACY_CONTROLLER", ""),
        PRIVACY_CONTACT=os.getenv("PRIVACY_CONTACT", ""),
        PRIVACY_LEGAL_BASIS=os.getenv("PRIVACY_LEGAL_BASIS", ""),
        PRIVACY_RETENTION=os.getenv("PRIVACY_RETENTION", ""),
        PRIVACY_PROVIDERS=os.getenv("PRIVACY_PROVIDERS", ""),
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID", ""),
        GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        SMTP_HOST=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", ""),
    )
    if test_config:
        app.config.update(test_config)
    if app.config["BASE_URL"].startswith("https://") and not app.config["SESSION_COOKIE_SECURE"]:
        raise RuntimeError("Con HTTPS debes configurar COOKIE_SECURE=true.")
    if (
        not app.config["SECRET_KEY"]
        or len(app.config["SECRET_KEY"]) < 32
        or app.config["SECRET_KEY"].startswith("replace-with-")
    ):
        raise RuntimeError("Configura SECRET_KEY con al menos 32 caracteres en .env.")
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    from .auth import auth, configure_oauth, role_allowed
    from .retention import register_commands
    from .routes import api

    configure_oauth(app)
    app.register_blueprint(auth)
    app.register_blueprint(api, url_prefix="/api")
    register_commands(app)

    @app.before_request
    def security():
        g.user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
        if g.user and (
            not g.user.active
            or session.get("auth_version") != g.user.auth_version
            or not role_allowed(g.user.email, g.user.role)
        ):
            session.clear()
            g.user = None
        if request.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
            expected = session.get("csrf", "")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not expected or not secrets.compare_digest(expected, supplied):
                return jsonify(error="Sesión caducada. Recarga la página."), 403

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if request.path.startswith(("/api/", "/auth/")):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return jsonify(error="No se pudo completar la operación. Inténtalo de nuevo."), 500

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path=""):
        if path.startswith(("api/", "auth/")):
            return jsonify(error="Recurso no encontrado."), 404
        folder = Path(app.root_path).parent / "frontend" / "dist" / "coevaluacion" / "browser"
        if path and (folder / path).is_file():
            return send_from_directory(folder, path)
        if not (folder / "index.html").exists():
            return jsonify(error="Compila el frontend con npm run build en frontend/."), 503
        if path and "." in path:
            return jsonify(error="Archivo no encontrado."), 404
        return send_from_directory(folder, "index.html")

    @app.get("/privacidad")
    def privacy():
        return render_template("privacy.html")

    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas iniciales sin borrar datos existentes."""
        db.create_all()
        click.echo("Base de datos inicializada.")

    return app
