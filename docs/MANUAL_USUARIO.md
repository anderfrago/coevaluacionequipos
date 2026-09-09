# Manual de uso

## Acceso y privacidad

Pulsa **Continuar con Google**. La cuenta debe pertenecer a `gmail.com` si eres alumno, o a `cuatrovientos.org` si eres docente. La cuenta `ander_frago@cuatrovientos.org` accede como administrador desde su primer inicio de sesión.

No se comparten contraseñas de Google con esta aplicación. El reparto y el comentario son visibles para su autor, para el docente responsable de la clase y para el administrador. Los compañeros no ven votos ni comentarios ajenos. Cada alumno ve únicamente su nota individual una vez publicada.

## Profesorado

1. En **Mis trabajos**, pulsa **Gestionar clases** y crea una clase.
2. Pulsa **Nuevo trabajo**. Selecciona la clase, escribe el título, las indicaciones y la fecha límite. Las fechas de la interfaz usan la zona horaria de tu dispositivo.
3. Selecciona el trabajo y pulsa **Añadir equipo**. Indica un nombre, los correos Gmail de sus integrantes y, si ya la conoces, la nota grupal sobre 10. Puedes introducir los correos en líneas separadas, separados por comas o por espacios.
4. Cada estudiante solo puede estar en un equipo dentro del mismo trabajo. Si todavía no tiene cuenta, se crea una ficha que se vinculará cuando acceda con ese correo de Google.
5. Pulsa **Enviar por correo** para enviar a los integrantes el enlace del formulario. Se muestra antes el equipo y sus destinatarios. Si el servidor no tiene correo configurado, puedes usar **Copiar enlace** y compartirlo desde tu correo.
6. Consulta el número de respuestas recibidas. Abre **Ver repartos y comentarios confidenciales** para revisar cada evaluación y sus advertencias MR.
7. Añade la nota grupal desde **Editar equipo** si estaba pendiente.
8. Cuando todas las personas de todos los equipos hayan respondido y existan notas grupales, pulsa **Publicar resultados**. Se cierra el trabajo y cada alumno puede consultar su nota.
9. Pulsa **Exportar XLSX** para descargar el trabajo completo. Puede exportarse antes de terminar: las notas incompletas quedarán vacías y su estado será Pendiente.

Puedes editar el trabajo para ampliar su plazo. **Cerrar plazo** impide nuevas respuestas inmediatamente. **Reabrir** solo permite responder si además la fecha límite es futura. Tras publicar, primero debes **Retirar publicación** para cambiar notas, equipos o plazo. El trabajo seguirá cerrado hasta que lo reabras.

Los integrantes no se pueden modificar cuando el equipo ya tiene respuestas, para evitar que cambie el presupuesto sobre el que se hizo la evaluación. Los cambios en el nombre o la nota grupal sí son posibles mientras el trabajo no esté publicado.

Eliminar un trabajo borra sus equipos y evaluaciones. Eliminar un equipo borra sus evaluaciones. La interfaz pide confirmación. Una clase solo puede eliminarse después de borrar sus trabajos.

## Alumnado

1. Abre el enlace recibido o entra en **Mis trabajos**.
2. Inicia sesión con la cuenta Gmail que facilitaste a tu docente. Un enlace no da acceso a personas ajenas al equipo.
3. Pulsa **Evaluar equipo**. Asigna puntos enteros a todos los integrantes, incluido tú. El total debe ser exactamente `3 × integrantes`.
4. Revisa el contador **Por repartir**. Si sobran puntos, corrige los valores antes de guardar.
5. Añade un comentario si quieres justificar tu reparto. Es opcional y admite hasta 3000 caracteres.
6. Pulsa **Guardar evaluación**. Verás una confirmación. Si cambias algún valor, vuelve a guardar.
7. Puedes volver y editar el reparto hasta que venza el plazo o el docente lo cierre. Al reenviar sustituyes tu evaluación anterior; no sumas otra respuesta.
8. Tu nota aparece cuando el docente publica los resultados.

Una advertencia **MR** indica ceros, concentración de todos los puntos o reparto igualitario. No impide guardar un reparto válido y no descuenta nota. El docente podrá revisar el caso.

## Administración

En **Usuarios**, el administrador puede crear fichas, consultar usuarios, editar nombre/correo/estado y eliminar fichas sin historial. Los roles deben corresponder al dominio. Solo la cuenta administradora designada puede ser administradora.

Para conservar evaluaciones, desactiva las cuentas con equipos o clases en lugar de eliminarlas. Una cuenta desactivada deja de poder entrar. Cambiar el correo o el rol invalida las sesiones anteriores; cambiar el correo transfiere el acceso al historial a la nueva identidad, por lo que debes comprobarlo antes de guardar.

El administrador no puede eliminar ni desactivar su propia cuenta. Los roles de usuarios con clases o equipos no se pueden cambiar. El administrador puede gestionar todas las clases; un docente solo las suyas.

## Interpretación del Excel

- **Resultados:** nota grupal, puntos recibidos, porcentaje, nota antes del límite, nota individual, MH, MR del equipo y estado de publicación.
- **Repartos confidenciales:** una fila por evaluador y destinatario, con puntos, motivos MR, comentario y fecha UTC. El comentario del evaluador se repite en sus filas.
- **Criterios:** fórmulas y significado de advertencias.

La nota individual no se calcula con el porcentaje ya redondeado. Por ejemplo, `7 × (6/9)` da `4,67`, aunque el porcentaje mostrado sea `66,67 %`. No se redistribuyen los puntos ni el exceso de nota después del límite de 10.

## Incidencias habituales

| Mensaje o situación | Qué hacer |
| --- | --- |
| No tienes trabajos asignados | Comprueba que usas el correo facilitado al docente |
| El enlace no corresponde a tu equipo | Accede con la cuenta correcta o solicita el enlace al docente |
| No se puede publicar | Revisa respuestas pendientes y notas grupales sin asignar |
| Sesión caducada | Recarga e inicia sesión de nuevo si es necesario |
| No se pueden cambiar integrantes | El equipo ya recibió evaluaciones |
| Correo no enviado | Copia el enlace y pide revisar la configuración de correo |
