"""Conservación configurable: vista previa por defecto y selección explícita al borrar."""

from datetime import timedelta

import click
from flask import current_app

from .models import Work, db, utcnow


def last_activity(work):
    return max(
        [work.deadline]
        + ([work.activity.changed_at] if work.activity else [])
        + [evaluation.updated_at for team in work.teams for evaluation in team.evaluations]
        + [review.reviewed_at for review in work.reviews]
    )


def register_commands(app):
    @app.cli.command("purge-expired")
    @click.option(
        "--work-id",
        "work_ids",
        multiple=True,
        type=int,
        help="ID aprobado para supresión; puede repetirse.",
    )
    @click.option("--execute", is_flag=True, help="Ejecuta solo los IDs seleccionados.")
    def purge_expired(work_ids, execute):
        """Muestra trabajos cerrados fuera de plazo; no borra sin --execute y --work-id."""
        configured = str(current_app.config["RETENTION_DAYS"]).strip()
        if not configured:
            raise click.ClickException("Conservación sin definir: configura RETENTION_DAYS.")
        if not configured.isdecimal() or not 1 <= int(configured) <= 36500:
            raise click.ClickException("RETENTION_DAYS debe ser un entero entre 1 y 36500.")
        cutoff = utcnow() - timedelta(days=int(configured))
        if execute and not work_ids:
            raise click.ClickException("Para borrar indica expresamente cada --work-id autorizado.")
        query = db.select(Work).where(Work.closed.is_(True), Work.deadline < cutoff)
        candidates = {
            work.id: work
            for work in db.session.execute(query).scalars()
            if last_activity(work) < cutoff
        }
        if work_ids:
            if set(work_ids) - candidates.keys():
                raise click.ClickException(
                    "Algún ID no existe, sigue abierto o tiene actividad dentro del plazo. No se borra nada."
                )
            candidates = {work_id: candidates[work_id] for work_id in sorted(set(work_ids))}
        click.echo(f"Fecha de corte UTC: {cutoff.date()}. Trabajos candidatos: {len(candidates)}.")
        for work in candidates.values():
            click.echo(
                f"ID {work.id}: {len(work.teams)} equipos, "
                f"{sum(len(team.evaluations) for team in work.teams)} evaluaciones, "
                f"última actividad {last_activity(work).date()}."
            )
        if not execute:
            click.echo("VISTA PREVIA. No se ha borrado ningún dato.")
            return
        # One transaction: an invalid selection above never produces partial deletion.
        for work in candidates.values():
            db.session.delete(work)
        db.session.commit()
        click.echo(
            f"Eliminados {len(candidates)} trabajos con sus equipos, evaluaciones y revisiones. "
            "Revisa aparte las cuentas sin historial, exportaciones y copias según la política del centro."
        )
