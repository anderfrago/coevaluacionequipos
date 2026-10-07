from datetime import timedelta

import pytest
from test_app import app as application_fixture  # noqa: F401
from test_app import client_for, send, setup_team, vote
from werkzeug.exceptions import Forbidden

from backend.auth import user_from_identity
from backend.models import (
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


@pytest.fixture(name="app")
def privacy_app(request):
    return request.getfixturevalue("application_fixture")


@pytest.mark.parametrize("email", ["nuevo@gmail.com", "nuevo@cuatrovientos.org"])
def test_verified_google_identity_does_not_grant_access(app, email):
    with app.app_context():
        with pytest.raises(Forbidden):
            user_from_identity(
                {
                    "email": email,
                    "email_verified": True,
                    "sub": "unknown",
                    "hd": "cuatrovientos.org",
                }
            )
        assert db.session.query(User).filter_by(email=email).count() == 0


def test_corporate_student_is_not_promoted_and_staff_requires_workspace(app):
    admin = client_for(app, 1)
    created = send(
        admin,
        "POST",
        "/users",
        {"email": "estudiante@cuatrovientos.org", "name": "Estudiante", "role": "student"},
    )
    assert created.status_code == 201
    with app.app_context():
        identity = {
            "email": "estudiante@cuatrovientos.org",
            "email_verified": True,
            "sub": "student-corporate",
            "hd": "cuatrovientos.org",
            "role": "admin",
        }
        assert user_from_identity(identity).role == "student"
        with pytest.raises(Forbidden):
            user_from_identity(
                {"email": "docente@cuatrovientos.org", "email_verified": True, "sub": "teacher"}
            )
        assert (
            user_from_identity(
                {
                    "email": "docente@cuatrovientos.org",
                    "email_verified": True,
                    "sub": "teacher",
                    "hd": "cuatrovientos.org",
                }
            ).role
            == "teacher"
        )


def test_student_domain_policy_rejects_new_and_existing_sessions(app):
    student = client_for(app, 10)
    app.config["STUDENT_DOMAINS"] = {"cuatrovientos.org"}
    assert student.get("/api/dashboard").status_code == 401
    teacher, work, _ = setup_team_with_corporate_students(app)
    rejected = send(
        teacher,
        "POST",
        f"/works/{work}/teams",
        {"name": "No autorizado", "grade": 7, "emails": ["externo@gmail.com", "otro@gmail.com"]},
    )
    assert rejected.status_code == 400


def setup_team_with_corporate_students(app):
    with app.app_context():
        for number in range(5):
            db.session.get(User, 10 + number).email = f"alumno{number}@cuatrovientos.org"
        db.session.commit()
    teacher = client_for(app, 2)
    classroom = send(teacher, "POST", "/classes", {"name": "Clase"}).json["id"]
    work = send(
        teacher,
        "POST",
        "/works",
        {
            "classroom_id": classroom,
            "title": "Trabajo",
            "description": "",
            "deadline": (utcnow() + timedelta(days=1)).isoformat() + "Z",
        },
    ).json["id"]
    response = send(
        teacher,
        "POST",
        f"/works/{work}/teams",
        {
            "name": "Equipo",
            "grade": 7,
            "emails": ["alumno0@cuatrovientos.org", "alumno1@cuatrovientos.org"],
        },
    )
    assert response.status_code == 201
    return teacher, work, response.json["id"]


def test_invited_student_can_log_in_but_staff_cannot_be_added_as_student(app):
    teacher, work, _ = setup_team(app)
    response = send(
        teacher,
        "POST",
        f"/works/{work}/teams",
        {
            "name": "Invitados",
            "grade": 7,
            "emails": ["invitado@cuatrovientos.org", "invitado@gmail.com"],
        },
    )
    assert response.status_code == 201
    with app.app_context():
        assert (
            user_from_identity(
                {"email": "invitado@cuatrovientos.org", "sub": "invited", "email_verified": True}
            ).role
            == "student"
        )
    assert (
        send(
            teacher,
            "POST",
            f"/works/{work}/teams",
            {
                "name": "Rechazado",
                "grade": 7,
                "emails": ["docente@cuatrovientos.org", "otra@gmail.com"],
            },
        ).status_code
        == 400
    )


def test_publication_requires_explicit_review_and_records_actor(app):
    teacher, work_id, team = setup_team(app)
    for number in range(3):
        assert vote(app, team, 10 + number, [2, 3, 4]).status_code == 200
    for reviewed in (None, False, "true", 1):
        assert (
            send(
                teacher,
                "POST",
                f"/works/{work_id}/state",
                {"action": "publish", "reviewed": reviewed},
            ).status_code
            == 400
        )
    with app.app_context():
        assert not db.session.get(Work, work_id).published
        assert db.session.query(PublicationReview).count() == 0
    assert (
        send(
            teacher, "POST", f"/works/{work_id}/state", {"action": "publish", "reviewed": True}
        ).status_code
        == 200
    )
    with app.app_context():
        review = db.session.query(PublicationReview).one()
        assert review.reviewer_id == 2 and review.work_id == work_id
    assert (
        send(
            client_for(app, 3),
            "POST",
            f"/works/{work_id}/state",
            {"action": "publish", "reviewed": True},
        ).status_code
        == 403
    )


def make_old_work(app):
    _, work_id, team = setup_team(app)
    vote(app, team, 10, [2, 3, 4], "Comentario a eliminar")
    with app.app_context():
        old = utcnow() - timedelta(days=500)
        work = db.session.get(Work, work_id)
        work.closed = True
        work.deadline = old
        work.activity.changed_at = old
        for evaluation in work.teams[0].evaluations:
            evaluation.updated_at = old
        db.session.commit()
    return work_id


def test_retention_disabled_by_default_and_dry_run_never_deletes(app):
    work_id = make_old_work(app)
    app.config["RETENTION_DAYS"] = ""
    runner = app.test_cli_runner()
    assert runner.invoke(args=["purge-expired"]).exit_code != 0
    app.config["RETENTION_DAYS"] = "365"
    result = runner.invoke(args=["purge-expired"])
    assert result.exit_code == 0 and "VISTA PREVIA" in result.output
    assert f"ID {work_id}" in result.output
    assert "Comentario a eliminar" not in result.output
    assert runner.invoke(args=["purge-expired", "--execute"]).exit_code != 0
    with app.app_context():
        assert db.session.get(Work, work_id) is not None


def test_retention_explicit_selection_cascades_and_keeps_other_work(app):
    work_id = make_old_work(app)
    _, recent_id, _ = setup_team(app)
    app.config["RETENTION_DAYS"] = "365"
    runner = app.test_cli_runner()
    rejected = runner.invoke(
        args=["purge-expired", "--work-id", str(work_id), "--work-id", str(recent_id), "--execute"]
    )
    assert rejected.exit_code != 0
    with app.app_context():
        assert db.session.get(Work, work_id) is not None
    result = runner.invoke(args=["purge-expired", "--work-id", str(work_id), "--execute"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.get(Work, work_id) is None
        assert db.session.get(Work, recent_id) is not None
        assert db.session.query(Evaluation).count() == 0
        assert db.session.query(Team).count() == 1
        assert db.session.query(Member).count() == 3
        assert db.session.query(WorkActivity).count() == 1
        assert db.session.get(User, 10) is not None


@pytest.mark.parametrize("activity", ["evaluation", "review", "open", "edit"])
def test_retention_preserves_recent_activity_and_open_works(app, activity):
    work_id = make_old_work(app)
    app.config["RETENTION_DAYS"] = "365"
    with app.app_context():
        work = db.session.get(Work, work_id)
        if activity == "evaluation":
            work.teams[0].evaluations[0].updated_at = utcnow()
        elif activity == "review":
            db.session.add(PublicationReview(work_id=work_id, reviewer_id=2))
        elif activity == "edit":
            work.activity.changed_at = utcnow()
        else:
            work.closed = False
        db.session.commit()
    result = app.test_cli_runner().invoke(
        args=["purge-expired", "--work-id", str(work_id), "--execute"]
    )
    assert result.exit_code != 0
    with app.app_context():
        assert db.session.get(Work, work_id) is not None


def test_privacy_is_public_escaped_and_contains_no_credentials(app):
    app.config.update(PRIVACY_CONTROLLER="<script>no</script>", GOOGLE_CLIENT_SECRET="secret-test")
    response = app.test_client().get("/privacidad")
    assert response.status_code == 200
    assert b"&lt;script&gt;" in response.data
    assert b"<script>no</script>" not in response.data
    assert b"secret-test" not in response.data
    assert b"Pendiente" in response.data
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_additive_schema_upgrade_preserves_existing_data(app):
    _, work_id, _ = setup_team(app)
    with app.app_context():
        WorkActivity.__table__.drop(db.engine)
        PublicationReview.__table__.drop(db.engine)
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.get(Work, work_id).title == "Proyecto"
        assert db.session.query(Member).count() == 3
        assert db.session.query(User).count() == 8
        assert db.session.query(PublicationReview).count() == 0
        assert db.session.query(WorkActivity).count() == 0
