from decimal import ROUND_HALF_UP, Decimal


def warnings(allocations):
    values = list(allocations.values())
    reasons = []
    if 0 in values:
        reasons.append("Se han asignado 0 puntos a un integrante.")
    if values and sum(values) in values:
        reasons.append("Se han asignado todos los puntos a una persona.")
    if values and len(set(values)) == 1:
        reasons.append("Se han repartido los mismos puntos a todos.")
    return reasons


def rounded(value):
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def results(team):
    complete = len(team.evaluations) == len(team.members) and bool(team.members)
    ready = complete and team.grade is not None
    rows = []
    for member in team.members:
        points = sum(e.allocations.get(str(member.user_id), 0) for e in team.evaluations)
        factor = Decimal(points) / Decimal(3 * len(team.members))
        raw = Decimal(team.grade) * factor if ready else None
        rows.append(
            {
                "user_id": member.user_id,
                "name": member.user.name,
                "email": member.user.email,
                "points": points,
                "percentage": rounded(factor * 100) if ready else None,
                "raw_grade": rounded(raw) if ready else None,
                "grade": rounded(min(raw, Decimal(10))) if ready else None,
                "mh": bool(ready and raw > 10),
            }
        )
    return {"complete": complete, "ready": ready, "rows": rows}
