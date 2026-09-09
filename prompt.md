Quiero realizar una aplicación web con flask y angular 22. Pero quiero que mantenas saltos de línea y el código formateado, sepanrando las plantillas html a archivos separados.

La aplicación permite la autoevaluación y coevaluación de los estudiantes en trabajos grupales.

Mi planteamiento es el siguiente:

Un grupo de 3 integrantes 
<use_case>
Cada integrante tiene 3 puntos.
Por lo que cada alumno tiene 9 puntos a repartir entre todos los compañeros. De manera que si repartiera 3 puntos a cada uno el 100% de la nota grupal sería para cada uno de ellos. Entiendo que esta situación no debería darse y habría que aplicar alguna medida de penalización.

La idea es sumar los puntos totales asignados a cada uno de los integrantes (valor X1).
En un grupo de 9,  11,11 (100/9) es el valor a multiplicar por los puntos obtenidos por cada integrante. PORCENTAJE de la NOTA => X1 * 11,11

La NOTA INDIVIDUAL es NOTA GRUPAL * PORCENTAJE de la NOTA
De forma que un alumno con 66% de la nota en un grupo con un 7 de nota, su nota individual es 4,62
<use_case>

Te en cuenta que puede haber grupos de más integrantes, por ejemplo, en un grupo de 4 repartiría 12 puntos.

La aplicación debe permitir el registro con google.
La aplicación debe tener rol de docente (dominio @cuatrovientos) y alumno.
El administrador puede hacer CRUD de usuarios.

El resultado es exportado a excel

Quiero un manual de despliegue en Pythonanywhere.

Debe cumplir con los estilos de cuatrovientos.org
- primary color: #0f4285
- background color: white
- font family Segoe UI

Lanzame las preguntas que consideres oportunas
-----------------------

1. 
- Sí

¿Qué puntuaciones se permiten? ¿Solo enteros o también decimales? ¿Existe un máximo por persona? Si el máximo fuera 3 y fuera obligatorio repartir todos los puntos, solo sería posible dar 3 a cada integrante. Propongo permitir desde 0 hasta el total disponible, obligando a repartirlo completo.
2.
- Solo se permiten enteros. Me parece bien tu propuesta, de 0 hasta el total disponible.
En casos donde alguien reparta 0, todos los puntos o todos los integrantes se repartan lo mismo quiero una advertencia de mal repartido (MR)


3.
- Acepto tu propuesta

4. 
- Nota máxima un 10, pero si alguien la excede una advertencia de Matricula de Honor (MH)

5.
- Solo una advertencia. Considero que en ese caso no están realizando una coevaluación ajustada a la realidad

6. 
- Me encaja, debemos pasar por cada equipo un enlace al formulario para hacerle llegar a cada equipo mediante envío de un mail

¿Las evaluaciones serán confidenciales? Propongo que el docente vea quién asignó cada puntuación y que cada alumno vea únicamente su resultado final. ¿Quieres también comentarios justificativos obligatorios o criterios separados, como participación, responsabilidad y calidad del trabajo?
7. 
- Evaluaciones confidenciales, el docente puede ver. Posibilidad de agregar cometnarios

8.
- Los alumnos dominio gmail. Los docentes cuatrovientos.org y ander_frago@cuatrovientos.org es administrador

9
- Formato xlsx

10.
- Gratuita, generare una cuenta con usuario coevaluacionequipos

