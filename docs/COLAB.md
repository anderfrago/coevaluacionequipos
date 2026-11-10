# Ejecución en Google Colab

El proyecto puede ejecutarse en Colab para demostraciones, formación y pruebas. No debe
usarse como despliegue de producción: el proceso se detiene cuando Colab suspende el
entorno y los archivos locales desaparecen al reiniciarlo.

## Preparación

1. Crea una cuenta de ngrok y copia su token de autenticación.
2. Abre `colab/coevaluacion_colab.ipynb` en Colab y crea este secreto (icono de llave):

   - `NGROK_AUTHTOKEN`

   Concede al notebook acceso al secreto. No hacen falta credenciales de Google ni una URL
   pública fija: ngrok asigna la URL al iniciar el entorno.

El notebook activa `COLAB_DEMO_MODE`, que permite entrar como administrador sin autenticar
la identidad. Esta puerta de acceso no se activa en la configuración normal del proyecto.

## Datos persistentes

Por defecto, SQLite se guarda en el almacenamiento efímero de Colab. Para conservar los
datos entre sesiones, activa `USAR_GOOGLE_DRIVE` en la celda de configuración. Colab pedirá
permiso para montar Drive y guardará la base en
`MyDrive/coevaluacion-colab/coevaluacion.db`.

No publiques el notebook con el token de ngrok escrito en sus celdas. El notebook lo lee
desde el almacén de secretos de Colab y no lo imprime.

## Limitaciones

- La URL solo responde mientras la celda final y el entorno de Colab sigan activos.
- Cualquier persona que conozca esa URL puede entrar como administradora. No introduzcas
  nombres, correos, evaluaciones ni otros datos reales.
- El correo requiere configurar también las variables SMTP; sin ellas, las invitaciones no
  se pueden enviar.
- La primera ejecución tarda más porque instala dependencias y compila Angular.
