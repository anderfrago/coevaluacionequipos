# Actualización de acceso, privacidad y conservación

Esta actualización aplica controles técnicos a la coevaluación. No declara cumplimiento RGPD ni autoriza el uso en el centro. No cambia la fórmula de las notas.

## Cambios

- Se elimina el registro libre por Google. El administrador autoriza al profesorado; el alumnado debe estar dado de alta o incluido por su docente en un equipo.
- Los roles no se deducen del dominio. Un estudiante corporativo sigue siendo estudiante. El personal utiliza Google Workspace del dominio configurado; se comprueba `email_verified`, identidad Google y `hd`.
- Se conserva la vinculación de identidades existentes; no se reasigna automáticamente un historial a otra identidad Google.
- Publicar exige confirmar la revisión docente y registra su autor y fecha en `publication_review`. El docente debe revisar efectivamente el caso y atender reclamaciones.
- `work_activity` registra la última modificación del trabajo/equipos y los cambios de estado, para evitar seleccionar para borrado trabajos recién utilizados.
- `/privacidad` funciona sin iniciar sesión y presenta datos, destinatarios, derechos y textos institucionales configurables. No contiene secretos de configuración.
- La política de referente pasa a `no-referrer`; HTTPS requiere cookies seguras. Se mantienen CSRF, aislamiento por clase/equipo y revocación de sesiones ante cambios de identidad, rol o estado.

## Actualización de una instalación existente

1. Pausa las escrituras y realiza una copia protegida y consistente de la base de datos y configuración. Prueba la restauración en un entorno de pruebas.
2. Revisa las fichas docentes existentes: la versión anterior permitía el alta automática por dominio. Conserva activas solo las autorizadas por el centro. Esta actualización no puede inferir cuáles fueron aprobadas.
3. Copia el código y el frontend compilado. Mantén `.env` y la base de datos fuera del repositorio y del paquete público.
4. Configura las variables siguientes. Rota `SECRET_KEY` por una clave aleatoria nueva para invalidar las sesiones anteriores durante esta transición. La rotación no elimina evaluaciones ni identidades Google vinculadas.
5. Con la misma configuración y entorno virtual del WSGI, ejecuta `python -m flask --app wsgi:application init-db`. Añade las dos tablas; no borra las tablas anteriores. Las publicaciones históricas no reciben una revisión inventada.
6. Recarga la aplicación y comprueba el aviso público, el acceso del administrador, un docente autorizado, un estudiante y los rechazos de cuentas no autorizadas.
7. Verifica con cuentas de prueba el aislamiento entre clases/equipos, el cierre de sesiones al desactivar, la revisión antes de publicar y la exportación confidencial.
8. Reanuda únicamente según la autorización institucional. Si se retrocede de versión, ten presente que la anterior recupera el registro libre: no debe exponerse como solución de contingencia sin controles adicionales.

## Variables a completar

| Variable | Uso |
|---|---|
| `ADMIN_EMAIL` | Única cuenta de administración designada; debe pertenecer al dominio Workspace del personal |
| `TEACHER_DOMAIN` | Dominio exacto del personal; inicialmente `cuatrovientos.org` |
| `STUDENT_DOMAINS` | Dominios autorizados, separados por comas; inicialmente `cuatrovientos.org,gmail.com`. No conceden acceso sin ficha previa |
| `RETENTION_DAYS` | Plazo operativo de selección para conservación; vacío hasta que el centro lo apruebe |
| `PRIVACY_CONTROLLER` | Identificación del responsable real |
| `PRIVACY_CONTACT` | Contacto para privacidad, derechos y DPD |
| `PRIVACY_LEGAL_BASIS` | Base jurídica y norma aplicable determinadas por el centro |
| `PRIVACY_RETENTION` | Explicación comprensible del plazo y sus excepciones; debe concordar con el procedimiento operativo |
| `PRIVACY_PROVIDERS` | Proveedores realmente utilizados, región y transferencias/garantías aplicables; incluir alojamiento, Google y correo |

Los valores son texto plano; no se interpreta HTML. En `.env`, encierra entre comillas los textos con espacios o `#`. No pongas contraseñas en estas variables públicas. Si faltan datos, el aviso muestra que la información está pendiente: no utilizar con datos reales hasta completarla. Cambiar la configuración requiere recargar la aplicación.

## Conservación: siempre vista previa primero

No hay plazo legal preestablecido en el código ni tarea automática instalada. `RETENTION_DAYS` debe ser un entero positivo (hasta 36500 días); vacío o inválido impide ejecutar el comando. El centro define el plazo según su finalidad, normativa académica y reclamaciones.

Con el plazo ya aprobado y configurado:

```bash
python -m flask --app wsgi:application purge-expired
```

Muestra IDs, número de equipos/evaluaciones y fecha de última actividad, sin nombres, correos ni comentarios. **No borra nada.** Solo selecciona trabajos cerrados con fecha límite y actividad conocida anteriores al corte. Se toma la fecha más reciente entre plazo, evaluaciones, revisiones de publicación y modificaciones registradas del trabajo/equipos. Los trabajos antiguos de la versión anterior no tienen toda su actividad histórica registrada: confirmar manualmente su antigüedad y situación antes de seleccionarlos.

Revisar los IDs en el panel institucional y excluir los sujetos a reclamación, obligación de conservación o bloqueo. La candidatura técnica no autoriza por sí sola una supresión.

```bash
# Ejemplo: sustituir 12 y 18 por IDs realmente revisados y autorizados.
python -m flask --app wsgi:application purge-expired --work-id 12 --work-id 18
```

Solo después de aprobar la selección, pausar las escrituras y ejecutar:

```bash
python -m flask --app wsgi:application purge-expired --work-id 12 --work-id 18 --execute
```

Sin IDs explícitos se rechaza la ejecución. Si algún ID no es candidato se rechaza toda la selección. La eliminación se realiza en una transacción y borra trabajos, equipos, membresías, evaluaciones, confirmaciones de revisión y actividad relacionada. No se limita a esconderlos. Registrar internamente la autorización y resultado del procedimiento sin copiar contenidos académicos innecesarios.

Las cuentas y clases se conservan porque pueden tener otros usos. Después de revisar su finalidad, el administrador puede eliminar desde Usuarios las cuentas que ya no tengan referencias; las clases vacías pueden borrarse desde su gestión. Una cuenta con historial se desactiva mientras siga existiendo una justificación para conservarlo. No se implementa una anonimización ficticia sustituyendo solo el nombre.

## Copias, exportaciones y registros

La supresión anterior es lógica en la base activa, no un borrado forense de todos los soportes. No elimina por sí misma copias antiguas, páginas libres de SQLite, diarios del sistema de archivos ni informes ya descargados. Mantener almacenamiento y copias protegidos, una rotación aprobada y un procedimiento que no vuelva a introducir datos suprimidos al restaurar. Valorar el tratamiento del espacio libre de SQLite en una ventana de mantenimiento; no ejecutar operaciones de mantenimiento destructivas sobre la única copia útil.

Usar destinos institucionales para XLSX y borrar duplicados al finalizar su necesidad. Comprobar la retención de logs de PythonAnywhere, que puede incluir rutas de invitación y OAuth. El cambio de referente evita enviarlos como referente a otras páginas, pero no sustituye la configuración de registros del servidor.

## Pendientes ajenos al código

Titularidad y control del alojamiento, contrato y garantías de proveedores, región efectiva, plazos y base jurídica, información a menores/familias, procedimiento de derechos, copias, incidentes y autorización del centro. El panel de usuarios no sustituye el proceso institucional de altas. No se ha desplegado esta actualización ni se han enviado mensajes o eliminado datos reales.
