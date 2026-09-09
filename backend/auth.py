import secrets
from urllib.parse import urlsplit

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, abort, current_app, g, jsonify, redirect, request, session
from sqlalchemy.exc import IntegrityError

from .models import User, db

auth = Blueprint("auth", __name__)


def configure_oauth(app):
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile", "timeout": 15},
    )
    app.extensions["google_oauth"] = oauth


def role_for(email):
    if email == current_app.config["ADMIN_EMAIL"]:
        return "admin"
    domain = email.rsplit("@", 1)[-1]
    if domain == "cuatrovientos.org":
        return "teacher"
    if domain == "gmail.com":
        return "student"
    abort(400, "Solo se admiten cuentas gmail.com y cuatrovientos.org.")


def user_from_identity(info):
    email = str(info.get("email", "")).strip().lower()
    if info.get("email_verified") is not True or not info.get("sub"):
        abort(403, "Google debe verificar tu dirección de correo.")
    inferred_role = role_for(email)
    user = db.session.execute(
        db.select(User).filter_by(google_sub=info["sub"])
    ).scalar_one_or_none()
    if user and user.email != email:
        abort(403, "Tu dirección de Google ha cambiado. Contacta con el administrador.")
    if user is None:
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if user and (not user.active or user.google_sub not in (None, info["sub"])):
        abort(403, "Cuenta desactivada o identidad no autorizada.")
    if user is None:
        user = User(email=email, name=str(info.get("name") or email)[:120], role=inferred_role)
        db.session.add(user)
    if user.google_sub is None:
        user.name = str(info.get("name") or user.name)[:120]
    user.google_sub = info["sub"]
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "El registro ya está en curso. Vuelve a iniciar sesión.")
    return user


@auth.get("/auth/google")
def login():
    if not current_app.config["GOOGLE_CLIENT_ID"] or not current_app.config["GOOGLE_CLIENT_SECRET"]:
        return redirect("/?auth_error=configuration")
    target = request.args.get("next", "/")
    parsed = urlsplit(target)
    session["after_login"] = (
        target
        if target.startswith("/evaluar/")
        and not parsed.netloc
        and not parsed.scheme
        and "\\" not in target
        else "/"
    )
    callback = current_app.config["BASE_URL"] + "/auth/google/callback"
    return current_app.extensions["google_oauth"].google.authorize_redirect(callback)


@auth.get("/auth/google/callback")
def callback():
    try:
        token = current_app.extensions["google_oauth"].google.authorize_access_token()
        user = user_from_identity(token["userinfo"])
    except Exception:
        # No se registran tokens, datos personales ni secretos de Google.
        current_app.logger.warning(
            "Inicio de sesión rechazado por el proveedor o la política de acceso."
        )
        session.clear()
        return redirect("/?auth_error=access")
    target = session.get("after_login", "/")
    session.clear()
    session["user_id"] = user.id
    session["auth_version"] = user.auth_version
    session["csrf"] = secrets.token_urlsafe(32)
    session.permanent = True
    return redirect(target)


@auth.get("/api/session")
def current_session():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return jsonify(user=g.user.public() if g.user else None, csrf=session["csrf"])


@auth.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)
