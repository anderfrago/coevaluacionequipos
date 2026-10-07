import secrets
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, abort, current_app, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from .auth import role_allowed
from .grading import results, warnings
from .models import (
    Classroom,
    Evaluation,
    Member,
    PublicationReview,
    Team,
    User,
    Work,
    WorkActivity,
    db,
    utcnow,
)

api = Blueprint("api", __name__)


def access(*roles):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                abort(401, "Inicia sesión para continuar.")
            if roles and g.user.role not in roles:
                abort(403, "No tienes permiso para esta acción.")
            return fn(*args, **kwargs)

        return wrapped

    return decorate


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Envía un objeto JSON válido.")
    return data


def text(data, key, limit=120, optional=False):
    value = data.get(key, "")
    if (
        not isinstance(value, str)
        or len(value.strip()) > limit
        or (not optional and not value.strip())
    ):
        abort(400, f"El campo {key} es obligatorio y admite hasta {limit} caracteres.")
    return value.strip()


def email_value(value):
    if not isinstance(value, str):
        abort(400, "Correo no válido.")
    value = value.strip().lower()
    if (
        len(value) > 254
        or value.count("@") != 1
        or not value.split("@")[0]
        or "." not in value.rsplit("@", 1)[-1]
        or any(c.isspace() for c in value)
    ):
        abort(400, "Correo no válido.")
    return value


def commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "Ya existe ese registro o tiene datos relacionados.")


def owned(model, item_id):
    obj = db.get_or_404(model, item_id)
    classroom = (
        obj
        if isinstance(obj, Classroom)
        else obj.classroom
        if isinstance(obj, Work)
        else obj.work.classroom
    )
    if g.user.role != "admin" and classroom.owner_id != g.user.id:
        abort(403, "Solo puedes gestionar tus propias clases.")
    return obj


def editable(work):
    if work.published:
        abort(409, "Retira la publicación antes de modificar el trabajo.")


def touch_work(work):
    if work.activity is None:
        work.activity = WorkActivity(changed_at=utcnow())
    else:
        work.activity.changed_at = utcnow()


def parse_deadline(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, AttributeError, TypeError):
        abort(400, "La fecha límite debe incluir zona horaria.")


def parse_grade(value):
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
        if not result.is_finite() or not 0 <= result <= 10 or result.as_tuple().exponent < -2:
            raise ValueError()
        return result
    except (InvalidOperation, ValueError):
        abort(400, "La nota grupal debe estar entre 0 y 10, con un máximo de dos decimales.")


def team_data(team, teacher=False):
    own = next((e for e in team.evaluations if e.evaluator_id == g.user.id), None)
    data = {
        "id": team.id,
        "name": team.name,
        "token": team.token,
        "grade": float(team.grade)
        if team.grade is not None and (teacher or team.work.published)
        else None,
        "members": [
            {"id": m.user_id, "name": m.user.name, **({"email": m.user.email} if teacher else {})}
            for m in team.members
        ],
        "budget": 3 * len(team.members),
        "own_evaluation": {
            "allocations": own.allocations,
            "comment": own.comment,
            "warnings": warnings(own.allocations),
        }
        if own
        else None,
    }
    if teacher:
        data.update(
            submitted=len(team.evaluations),
            results=results(team),
            link=f"{current_app.config['BASE_URL']}/evaluar/{team.token}",
            evaluations=[
                {
                    "evaluator_id": e.evaluator_id,
                    "allocations": e.allocations,
                    "comment": e.comment,
                    "warnings": warnings(e.allocations),
                    "updated_at": e.updated_at.isoformat() + "Z",
                }
                for e in team.evaluations
            ],
        )
    elif team.work.published:
        data["my_result"] = next(
            (r for r in results(team)["rows"] if r["user_id"] == g.user.id), None
        )
    return data


def work_data(work, teacher=False):
    teams = (
        work.teams
        if teacher
        else [t for t in work.teams if any(m.user_id == g.user.id for m in t.members)]
    )
    return {
        "id": work.id,
        "classroom_id": work.classroom_id,
        "classroom_name": work.classroom.name,
        "title": work.title,
        "description": work.description,
        "deadline": work.deadline.isoformat() + "Z",
        "closed": work.closed,
        "expired": utcnow() >= work.deadline,
        "published": work.published,
        "teams": [team_data(t, teacher) for t in teams],
    }


@api.get("/dashboard")
@access()
def dashboard():
    teacher = g.user.role in ("admin", "teacher")
    query = db.select(Classroom).order_by(Classroom.id.desc())
    if g.user.role == "teacher":
        query = query.filter_by(owner_id=g.user.id)
    classes = db.session.execute(query).scalars().all()
    works = [
        work_data(w, teacher)
        for c in classes
        for w in c.works
        if teacher or any(m.user_id == g.user.id for t in w.teams for m in t.members)
    ]
    return jsonify(
        classes=[{"id": c.id, "name": c.name} for c in classes] if teacher else [], works=works
    )


@api.post("/classes")
@access("teacher", "admin")
def create_class():
    classroom = Classroom(name=text(body(), "name"), owner_id=g.user.id)
    db.session.add(classroom)
    commit()
    return jsonify(id=classroom.id), 201


@api.route("/classes/<int:item_id>", methods=["PATCH", "DELETE"])
@access("teacher", "admin")
def change_class(item_id):
    classroom = owned(Classroom, item_id)
    if request.method == "DELETE":
        if classroom.works:
            abort(409, "Elimina primero los trabajos de esta clase.")
        db.session.delete(classroom)
    else:
        classroom.name = text(body(), "name")
    commit()
    return jsonify(ok=True)


@api.post("/works")
@access("teacher", "admin")
def create_work():
    data = body()
    classroom = owned(Classroom, data.get("classroom_id"))
    work = Work(
        classroom_id=classroom.id,
        title=text(data, "title", 160),
        description=text(data, "description", 4000, True),
        deadline=parse_deadline(data.get("deadline")),
    )
    db.session.add(work)
    touch_work(work)
    commit()
    return jsonify(id=work.id), 201


@api.route("/works/<int:item_id>", methods=["PATCH", "DELETE"])
@access("teacher", "admin")
def change_work(item_id):
    work = owned(Work, item_id)
    editable(work)
    if request.method == "DELETE":
        db.session.delete(work)
    else:
        data = body()
        work.title = text(data, "title", 160)
        work.description = text(data, "description", 4000, True)
        work.deadline = parse_deadline(data.get("deadline"))
        touch_work(work)
    commit()
    return jsonify(ok=True)


@api.post("/works/<int:item_id>/state")
@access("teacher", "admin")
def change_state(item_id):
    work = owned(Work, item_id)
    data = body()
    action = data.get("action")
    if action == "publish":
        if not work.teams or not all(results(t)["ready"] for t in work.teams):
            abort(
                409,
                "Faltan evaluaciones o notas grupales. No se pueden publicar resultados incompletos.",
            )
        if data.get("reviewed") is not True:
            abort(400, "Confirma que has revisado los repartos y las notas antes de publicar.")
        if work.published:
            abort(409, "El trabajo ya está publicado.")
        db.session.add(PublicationReview(work_id=work.id, reviewer_id=g.user.id))
        work.closed = True
        work.published = True
    elif action == "unpublish":
        work.published = False
    elif action in ("close", "reopen"):
        editable(work)
        work.closed = action == "close"
    else:
        abort(400, "Acción no válida.")
    touch_work(work)
    commit()
    return jsonify(ok=True)


def set_team(team, data):
    team.name = text(data, "name")
    team.grade = parse_grade(data.get("grade"))
    emails = data.get("emails")
    if not isinstance(emails, list) or not 2 <= len(emails) <= 50:
        abort(400, "Incluye entre 2 y 50 integrantes.")
    emails = [email_value(e) for e in emails]
    if len(set(emails)) != len(emails) or any(not role_allowed(e, "student") for e in emails):
        abort(400, "Usa correos de alumnado de los dominios autorizados, sin duplicados.")
    previous = {m.user.email for m in team.members}
    if team.evaluations and previous != set(emails):
        abort(409, "No se pueden cambiar integrantes cuando ya hay evaluaciones.")
    if previous == set(emails):
        return
    for other in team.work.teams:
        if other is not team and any(m.user.email in emails for m in other.members):
            abort(409, "Un alumno no puede pertenecer a dos equipos del mismo trabajo.")
    team.members.clear()
    db.session.flush()
    for email in emails:
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user and (not user.active or user.role != "student"):
            abort(400, f"El alumno {email} no está activo.")
        if user is None:
            user = User(email=email, name=email.split("@")[0], role="student")
            db.session.add(user)
            db.session.flush()
        team.members.append(Member(user_id=user.id))


@api.post("/works/<int:item_id>/teams")
@access("teacher", "admin")
def create_team(item_id):
    work = owned(Work, item_id)
    editable(work)
    team = Team(work=work, token=secrets.token_urlsafe(24), name="")
    db.session.add(team)
    with db.session.no_autoflush:
        set_team(team, body())
    touch_work(work)
    commit()
    return jsonify(id=team.id), 201


@api.route("/teams/<int:item_id>", methods=["PATCH", "DELETE"])
@access("teacher", "admin")
def change_team(item_id):
    team = owned(Team, item_id)
    editable(team.work)
    touch_work(team.work)
    if request.method == "DELETE":
        db.session.delete(team)
    else:
        set_team(team, body())
    commit()
    return jsonify(ok=True)


@api.get("/evaluation/<token>")
@access("student")
def evaluation_form(token):
    team = db.session.execute(db.select(Team).filter_by(token=token)).scalar_one_or_none()
    if team is None or not any(m.user_id == g.user.id for m in team.members):
        abort(404, "Este enlace no corresponde a uno de tus equipos.")
    return jsonify(work=work_data(team.work), team=team_data(team))


@api.put("/evaluation/<token>")
@access("student")
def save_evaluation(token):
    team = db.session.execute(db.select(Team).filter_by(token=token)).scalar_one_or_none()
    if team is None or not any(m.user_id == g.user.id for m in team.members):
        abort(404, "Este enlace no corresponde a uno de tus equipos.")
    if team.work.closed or team.work.published or utcnow() >= team.work.deadline:
        abort(409, "El plazo de evaluación está cerrado.")
    data = body()
    allocations = data.get("allocations")
    expected = {str(m.user_id) for m in team.members}
    budget = 3 * len(expected)
    if not isinstance(allocations, dict) or set(allocations) != expected:
        abort(400, "Debes puntuar a todos los integrantes, incluido tú.")
    if (
        any(type(v) is not int or v < 0 or v > budget for v in allocations.values())
        or sum(allocations.values()) != budget
    ):
        abort(400, f"Reparte exactamente {budget} puntos enteros entre 0 y {budget}.")
    comment = text(data, "comment", 3000, True)
    evaluation = db.session.execute(
        db.select(Evaluation).filter_by(team_id=team.id, evaluator_id=g.user.id)
    ).scalar_one_or_none()
    if evaluation is None:
        evaluation = Evaluation(team_id=team.id, evaluator_id=g.user.id)
        db.session.add(evaluation)
    evaluation.allocations = allocations
    evaluation.comment = comment
    evaluation.updated_at = utcnow()
    commit()
    return jsonify(ok=True, warnings=warnings(allocations))


@api.post("/teams/<int:item_id>/invite")
@access("teacher", "admin")
def invite(item_id):
    from .mail import send_invitations

    team = owned(Team, item_id)
    if team.work.closed or team.work.published or utcnow() >= team.work.deadline:
        abort(409, "Abre el trabajo y ajusta el plazo antes de enviar invitaciones.")
    return jsonify(send_invitations(team))


@api.get("/works/<int:item_id>/export")
@access("teacher", "admin")
def export(item_id):
    from .export import export_work

    return export_work(owned(Work, item_id))


@api.get("/users")
@access("admin")
def users():
    return jsonify(
        users=[
            u.public() for u in db.session.execute(db.select(User).order_by(User.name)).scalars()
        ]
    )


def set_user(user, data):
    email = email_value(data.get("email"))
    role = data.get("role")
    if not role_allowed(email, role):
        abort(
            400,
            "El correo no está permitido para ese rol. Revisa la política de acceso del centro.",
        )
    if type(data.get("active", True)) is not bool:
        abort(400, "El estado activo debe ser booleano.")
    if user.id == g.user.id and (
        not data.get("active", True) or role != "admin" or email != user.email
    ):
        abort(400, "No puedes desactivar ni cambiar el acceso de tu propia cuenta administradora.")
    if user.id and user.email != email:
        user.google_sub = None
    if user.id and (
        user.email != email or user.role != role or user.active != data.get("active", True)
    ):
        user.auth_version += 1
    if user.id and user.role != role:
        if (
            db.session.query(Member).filter_by(user_id=user.id).first()
            or db.session.query(Classroom).filter_by(owner_id=user.id).first()
            or db.session.query(PublicationReview).filter_by(reviewer_id=user.id).first()
        ):
            abort(409, "No se puede cambiar el rol de un usuario con equipos o clases.")
    user.email = email
    user.name = text(data, "name")
    user.role = role
    user.active = data.get("active", True)


@api.post("/users")
@access("admin")
def create_user():
    user = User()
    set_user(user, body())
    db.session.add(user)
    commit()
    return jsonify(id=user.id), 201


@api.route("/users/<int:item_id>", methods=["PATCH", "DELETE"])
@access("admin")
def change_user(item_id):
    user = db.get_or_404(User, item_id)
    if request.method == "DELETE":
        if user.id == g.user.id:
            abort(400, "No puedes eliminar tu propia cuenta.")
        referenced = (
            db.session.query(Member).filter_by(user_id=user.id).first()
            or db.session.query(Classroom).filter_by(owner_id=user.id).first()
            or db.session.query(Evaluation).filter_by(evaluator_id=user.id).first()
            or db.session.query(PublicationReview).filter_by(reviewer_id=user.id).first()
        )
        if referenced:
            abort(
                409, "Este usuario tiene equipos o clases. Desactívalo para conservar el historial."
            )
        db.session.delete(user)
    else:
        set_user(user, body())
    commit()
    return jsonify(ok=True)
