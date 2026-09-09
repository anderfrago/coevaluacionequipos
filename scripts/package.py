"""Empaqueta solo fuentes y frontend compilado; excluye secretos y datos."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
build = root / "frontend" / "dist" / "coevaluacion" / "browser"
if not (build / "index.html").is_file():
    raise SystemExit("Primero ejecuta npm run build dentro de frontend/.")

files = [
    root / name
    for name in (
        "README.md",
        "requirements.txt",
        "requirements-dev.txt",
        "constraints.txt",
        ".env.example",
        ".editorconfig",
        ".gitignore",
        "pyproject.toml",
        "wsgi.py",
    )
]
for directory in ("backend", "docs", "tests", "scripts", "frontend/src"):
    files.extend(
        path
        for path in (root / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
files.extend((root / "frontend").glob("*.json"))
files.extend(path for path in build.parent.rglob("*") if path.is_file())
destination = root / "dist" / "coevaluacion-pythonanywhere.zip"
destination.parent.mkdir(exist_ok=True)
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        if path.is_file():
            archive.write(path, path.relative_to(root))

print(f"Paquete creado: {destination}")
