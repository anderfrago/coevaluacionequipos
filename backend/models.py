from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    google_sub = db.Column(db.String(255), unique=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    auth_version = db.Column(db.Integer, nullable=False, default=1)

    def public(self):
        return {key: getattr(self, key) for key in ("id", "email", "name", "role", "active")}


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    works = db.relationship("Work", backref="classroom", cascade="all, delete-orphan")


class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    deadline = db.Column(db.DateTime, nullable=False)
    closed = db.Column(db.Boolean, nullable=False, default=False)
    published = db.Column(db.Boolean, nullable=False, default=False)
    teams = db.relationship("Team", backref="work", cascade="all, delete-orphan")


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, db.ForeignKey("work.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    grade = db.Column(db.Numeric(4, 2))
    token = db.Column(db.String(100), unique=True, nullable=False)
    members = db.relationship("Member", backref="team", cascade="all, delete-orphan")
    evaluations = db.relationship("Evaluation", backref="team", cascade="all, delete-orphan")


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
    __table_args__ = (db.UniqueConstraint("team_id", "user_id"),)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    allocations = db.Column(db.JSON, nullable=False)
    comment = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    __table_args__ = (db.UniqueConstraint("team_id", "evaluator_id"),)
