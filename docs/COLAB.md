# Ejecución en Google Colab

El proyecto puede ejecutarse en Colab para demostraciones, formación y pruebas. No debe
usarse como despliegue de producción: el proceso se detiene cuando Colab suspende el
entorno y los archivos locales desaparecen al reiniciarlo.

## Preparación (una sola vez)

1. Crea una cuenta de ngrok y reserva un dominio HTTPS estático. Los dominios aleatorios
   no son adecuados porque Google OAuth exige que la URL de retorno coincida exactamente.
2. En el cliente OAuth de Google añade como URI de redirección autorizada:

   ```text
   https://TU-DOMINIO.ngrok-free.app/auth/google/callback
   ```

3. Abre `colab/coevaluacion_colab.ipynb` en Colab y crea estos secretos (icono de llave):

   - `NGROK_AUTHTOKEN`
   - `COLAB_PUBLIC_URL`, por ejemplo `https://TU-DOMINIO.ngrok-free.app`
   - `SECRET_KEY`, aleatoria y de al menos 32 caracteres
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

   Concede al notebook acceso a cada secreto.

El notebook admite además `ADMIN_EMAIL`, `TEACHER_DOMAIN` y `STUDENT_DOMAINS`. Si no se
definen, usa los valores actuales del proyecto.

## Datos persistentes

Por defecto, SQLite se guarda en el almacenamiento efímero de Colab. Para conservar los
datos entre sesiones, activa `USAR_GOOGLE_DRIVE` en la celda de configuración. Colab pedirá
permiso para montar Drive y guardará la base en
`MyDrive/coevaluacion-colab/coevaluacion.db`.

No publiques el notebook con valores secretos escritos en sus celdas. El notebook los lee
desde el almacén de secretos de Colab y no los imprime.

## Limitaciones

- La URL solo responde mientras la celda final y el entorno de Colab sigan activos.
- El correo requiere configurar también las variables SMTP; sin ellas, las invitaciones no
  se pueden enviar.
- La primera ejecución tarda más porque instala dependencias y compila Angular.
- Un dominio reservado de ngrok puede depender del plan de la cuenta.
