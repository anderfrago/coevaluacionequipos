import smtplib
import ssl
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from flask import abort, current_app, render_template


def send_invitations(team):
    config = current_app.config
    if not all(config.get(k) for k in ("SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_FROM")):
        abort(
            503,
            "Configura la cuenta de correo en el servidor. Mientras tanto puedes copiar el enlace del equipo.",
        )
    link = f"{config['BASE_URL']}/evaluar/{team.token}"
    deadline = (
        team.work.deadline.replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(ZoneInfo("Europe/Madrid"))
        .strftime("%d/%m/%Y %H:%M")
    )
    sent, failed = [], []
    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            for member in team.members:
                message = EmailMessage()
                message["Subject"] = f"Coevaluación: {team.work.title}".replace("\r", " ").replace(
                    "\n", " "
                )
                message["From"] = config["MAIL_FROM"]
                message["To"] = member.user.email
                context = dict(name=member.user.name, team=team, link=link, deadline=deadline)
                message.set_content(render_template("invitation.txt", **context))
                message.add_alternative(
                    render_template("invitation.html", **context), subtype="html"
                )
                try:
                    smtp.send_message(message)
                    sent.append(member.user.email)
                except smtplib.SMTPException:
                    failed.append(member.user.email)
    except (OSError, smtplib.SMTPException):
        failed = [m.user.email for m in team.members if m.user.email not in sent]
    return {"sent": sent, "failed": failed}
