# Despliegue en PythonAnywhere gratuito

Destino previsto: cuenta **coevaluacionequipos**. Este documento prepara una instalación inicial; no se ha creado ni desplegado una cuenta remota desde el proyecto.

## 1. Arquitectura

Flask sirve la API y el Angular ya compilado desde el mismo dominio. No hace falta mantener Node ejecutándose en PythonAnywhere. SQLite guarda los datos en `instance/coevaluacion.db`. El acceso usa Google OpenID Connect; las invitaciones se envían por SMTP con STARTTLS.

Las cuentas gratuitas nuevas disponen de espacio y recursos limitados y requieren renovar la aplicación periódicamente; la documentación indica 512 MiB, un worker y un mes de vigencia. No dependemos de MySQL ni de tareas programadas, que ya no se incluyen en las cuentas gratuitas nuevas. [Características del plan gratuito](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/).

## 2. Preparar el paquete en tu ordenador

Desde la carpeta raíz:

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
python scripts/package.py
```

El archivo `dist/coevaluacion-pythonanywhere.zip` contiene backend, frontend compilado y fuentes, requisitos, pruebas y manuales. No contiene `.env`, bases de datos, `.venv` ni `node_modules`. Si no has compilado el frontend, el empaquetador se detiene.

El desarrollo necesita Node compatible con Angular 22 y TypeScript 6.0; las dependencias concretas quedan en `frontend/package-lock.json`. [Versiones compatibles](https://angular.dev/reference/versions).

## 3. Crear la cuenta y subir el proyecto

1. Crea la cuenta gratuita con usuario `coevaluacionequipos`.
2. Desde **Files**, sube el ZIP a `/home/coevaluacionequipos/`.
3. Abre una consola **Bash**.

```bash
cd /home/coevaluacionequipos
mkdir -p coevaluacion-equipos
unzip coevaluacion-pythonanywhere.zip -d coevaluacion-equipos
cd coevaluacion-equipos
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -c constraints.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Si eliges otra versión de Python disponible, usa esa misma versión para el entorno virtual y la aplicación web. El proyecto requiere Python 3.10 o posterior.

## 4. Configurar variables

Edita `/home/coevaluacionequipos/coevaluacion-equipos/.env` desde **Files**. Sustituye la clave de ejemplo por la que acabas de generar:

```dotenv
SECRET_KEY=PEGA_AQUI_LA_CLAVE_ALEATORIA_GENERADA
BASE_URL=https://coevaluacionequipos.pythonanywhere.com
COOKIE_SECURE=true
DATABASE_URL=sqlite:////home/coevaluacionequipos/coevaluacion-equipos/instance/coevaluacion.db
ADMIN_EMAIL=ander_frago@cuatrovientos.org
GOOGLE_CLIENT_ID=COMPLETAR_EN_EL_PASO_6
GOOGLE_CLIENT_SECRET=COMPLETAR_EN_EL_PASO_6
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
MAIL_FROM=
```

Usa como `BASE_URL` el dominio exacto que aparezca en la pestaña **Web**; puede variar según la región de tu cuenta. No añadas una barra final. La dirección de retorno de Google debe usar ese mismo origen.

La URL SQLite absoluta lleva cuatro barras después de `sqlite:`. El directorio `instance` se crea automáticamente al cargar Flask. Las claves nunca deben guardarse en Angular ni en un repositorio.

```bash
chmod 600 .env
source .venv/bin/activate
python -m flask --app wsgi:application init-db
```

`init-db` crea las tablas iniciales, no elimina datos y no migra esquemas de versiones futuras.

## 5. Configurar la aplicación web

En **Web → Add a new web app**, selecciona **Manual configuration** y la versión de Python usada en el entorno virtual. En **Virtualenv**, indica:

```text
/home/coevaluacionequipos/coevaluacion-equipos/.venv
```

Abre el archivo WSGI enlazado en esa pestaña y sustituye su contenido por:

```python
import sys

from dotenv import load_dotenv

project_path = "/home/coevaluacionequipos/coevaluacion-equipos"

if project_path not in sys.path:
    sys.path.insert(0, project_path)

load_dotenv(project_path + "/.env")

from wsgi import application
```

No añadas `app.run()` al WSGI. Flask ya sirve las rutas y los archivos compilados; esta instalación no necesita mapeos estáticos. Activa la redirección a HTTPS si el panel ofrece esa opción y pulsa **Reload**. [Configuración oficial de Flask](https://help.pythonanywhere.com/pages/Flask/).

Abre el dominio de la aplicación. Debe aparecer la pantalla de acceso. Si muestra «Compila el frontend», comprueba que existe:

```text
/home/coevaluacionequipos/coevaluacion-equipos/frontend/dist/coevaluacion/browser/index.html
```

## 6. Configurar Google

En Google Cloud / Google Auth Platform:

1. Crea un proyecto y configura el nombre de la aplicación, correo de soporte y contacto.
2. Configura la audiencia como **External**, ya que accederán cuentas Gmail externas al centro.
3. Solicita únicamente los ámbitos básicos `openid`, `email` y `profile`.
4. Crea un cliente OAuth de tipo **Web application**.
5. Añade como URI de redirección autorizada:

```text
https://coevaluacionequipos.pythonanywhere.com/auth/google/callback
```

6. Para desarrollo local puedes añadir también `http://localhost:5000/auth/google/callback` o `http://localhost:4200/auth/google/callback`, según el modo de ejecución.
7. Copia el identificador y el secreto del cliente en `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` del `.env` del servidor.
8. Si la configuración de audiencia mantiene restricciones de prueba, añade las cuentas que usarás para probar. Antes de compartirlo con el centro, revisa el estado de publicación y los requisitos que indique Google.
9. Pulsa **Reload** en PythonAnywhere e inicia sesión con `ander_frago@cuatrovientos.org`.

El backend valida la identidad mediante Authlib y asigna el rol según el correo verificado; un dato enviado desde Angular no puede asignar el rol. El parámetro de dominio de una pantalla de acceso no sustituye la comprobación del servidor. [OpenID Connect de Google](https://developers.google.com/identity/openid-connect/openid-connect).

Las cuentas gratuitas limitan las conexiones salientes. Si el acceso falla por proxy o 403, consulta la lista permitida y comprueba los dominios de descubrimiento y tokens de Google. [Lista de dominios permitidos](https://www.pythonanywhere.com/whitelist/) y [errores de conexión](https://help.pythonanywhere.com/pages/403ForbiddenError/).

## 7. Configurar el correo

Usa una cuenta remitente dedicada. Para Gmail, activa la verificación en dos pasos y, si tu cuenta lo permite, genera una contraseña de aplicación. No uses tu contraseña habitual. Algunas políticas de Workspace impiden crear estas contraseñas. [Contraseñas de aplicación de Google](https://support.google.com/accounts/answer/185833?hl=es).

Completa:

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=TU_CUENTA_REMITENTE@gmail.com
SMTP_PASSWORD=TU_CONTRASENA_DE_APLICACION
MAIL_FROM=TU_CUENTA_REMITENTE@gmail.com
```

Se usa autenticación con STARTTLS por el puerto 587. [Configuración SMTP de Gmail](https://support.google.com/mail/answer/7104828?hl=es).

PythonAnywhere ha documentado Gmail como opción para SMTP desde cuentas gratuitas, pero hay que verificar la conexión en la cuenta concreta antes de darla por operativa. No asumas que un servidor SMTP de otro proveedor funcionará en el plan gratuito. [Respuesta del equipo de PythonAnywhere sobre Gmail](https://www.pythonanywhere.com/forums/topic/30283/).

Pulsa **Reload**. Crea un trabajo y un equipo con cuentas de prueba bajo tu control; desde la aplicación pulsa **Enviar por correo**. Cada destinatario recibe un mensaje independiente. Comprueba también la carpeta de spam.

Si el envío falla, se muestran los destinatarios fallidos y los ya enviados. Reintentar el envío completo vuelve a enviar a todo el equipo. Puedes compartir el enlace manualmente mientras solucionas la configuración. No hay envíos automáticos al crear equipos ni tareas en segundo plano.

## 8. Comprobación de la instalación

1. Entra como administrador y comprueba **Usuarios**.
2. Crea clase, trabajo y equipo de tres integrantes con nota grupal 7.
3. Abre el enlace con cada una de las tres cuentas Gmail. Reparte 2, 3 y 4 a los mismos destinatarios en las tres evaluaciones.
4. Verifica notas 4,67; 7,00; 9,33. Antes de la tercera respuesta, las notas deben estar pendientes.
5. Publica y comprueba que cada alumno solo ve su nota y su reparto.
6. Descarga el XLSX y ábrelo en Excel o LibreOffice.
7. En otro trabajo de prueba, comprueba MR con 3/3/3 y MH con 9/0/0 repetido por los tres evaluadores: el primer alumno obtiene 10 con MH.
8. Confirma el correo real y la apertura directa del enlace después de iniciar sesión.

El código se verifica localmente con pruebas automatizadas. Las credenciales reales, las políticas del centro y la conectividad de PythonAnywhere deben validarse en esta fase.

## 9. Copias de seguridad y actualizaciones

La base contiene usuarios, clases y evaluaciones. Haz una copia consistente con la API de backup de SQLite desde Bash:

```bash
cd /home/coevaluacionequipos/coevaluacion-equipos
source .venv/bin/activate
mkdir -p backups
python - <<'PY'
import sqlite3
from datetime import datetime, timezone

stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
with sqlite3.connect("instance/coevaluacion.db") as source:
    with sqlite3.connect(f"backups/coevaluacion-{stamp}.db") as target:
        source.backup(target)
PY
```

Descarga y custodia las copias. Conserva también una copia segura del `.env`. Vigila el espacio disponible y la fecha de renovación de la aplicación.

Para actualizar, crea una copia de seguridad, sube un ZIP nuevo, extrae las fuentes sobre la instalación, instala los requisitos y pulsa **Reload**. El empaquetador excluye la base y `.env`, por lo que no los sustituye. Comprueba que el paquete procede de una versión compatible con tu esquema. Esta primera versión no incorpora migraciones automáticas: si una actualización cambia tablas, deberá incluir un procedimiento específico de migración.

Para restaurar una copia, detén/desactiva temporalmente la aplicación desde el panel, conserva la base actual, reemplaza `instance/coevaluacion.db` por la copia y vuelve a habilitar y recargar. No reemplaces la base mientras la aplicación escribe en ella.

## 10. Resolución de errores

| Problema | Comprobación |
| --- | --- |
| Error 500 al iniciar | Revisa el error log de Web; entorno virtual, SECRET_KEY y ruta WSGI |
| No existe una tabla | Ejecuta `init-db` con el mismo `.env` que usa la web |
| `redirect_uri_mismatch` | URI exacta en Google, con protocolo, host y `/auth/google/callback` |
| Acceso rechazado | Cuenta verificada, dominio autorizado, estado activo y política de Google |
| Bucle o sesión caducada | HTTPS, COOKIE_SECURE, cookies habilitadas y SECRET_KEY estable |
| La web muestra código antiguo | Recompila, sube `frontend/dist/coevaluacion/browser` completo y recarga |
| Envío SMTP fallido | Contraseña de aplicación, puerto 587, remitente y conectividad del plan |
| No se puede escribir en SQLite | Permisos y ruta absoluta del directorio `instance` |
| Trabajo reabierto pero no editable | Amplía también la fecha límite |

No se ha realizado un despliegue remoto ni una prueba real de Google o del correo sin sus credenciales.
