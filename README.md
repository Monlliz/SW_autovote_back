

# 🗳️ Autovote

## Descripción del Sistema

Sistema basado en inteligencia artificial que facilita y optimiza la toma de decisiones electorales de los ciudadanos, permitiéndoles identificar las opciones políticas que mejor se alinean con sus valores e intereses, a través de la recopilación y análisis de información objetiva.

### ¿Cómo funciona?

- El sistema analiza en profundidad las **preferencias ideológicas** de cada usuario mediante un formulario estructurado que identifica sus posturas en temas clave como:
  - Economía
  - Educación
  - Salud
  - Seguridad
  - Derechos sociales

- Con base en esta información, el software **evalúa las propuestas de los candidatos** y determina cuáles se alinean mejor con el perfil del votante.

- Posteriormente, el sistema **automatiza y simula la selección**, para que el voto refleje fielmente las convicciones del usuario.

---

## ⚙️ Instalación y Configuración

### 🛠️ Herramientas y Librerías Usadas

- **Flask** → Framework para la API REST
- **Flask-CORS** → Para habilitar peticiones desde frontend externos
- **Flask-PyMongo** → Conexión con MongoDB
- **PyMongo** → Cliente MongoDB para Python
- **Marshmallow** → Validación y serialización de datos
- **Requests** → Cliente HTTP para llamadas externas
- **Google-Genai** →  Integración con servicios de IA de Google
- **bcrypt** → Cifra contraseñas de forma segura. 
- **PyJWT** → Maneja tokens JWT para autenticación. 
- **python-dotenv** → Carga variables de entorno desde un archivo. 

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/Monlliz/SW_autovote_back.git
cd SW_autovote_back
```

---

### 2️⃣ Instala las dependencias:

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Ejecutar el servidor

```bash
python app.py
```

El servidor se ejecutará en:  
```
http://127.0.0.1:5000/
```

---

## 📋 Colecciones


---

### v_administradores

```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "apellido": "String",
  "correo": "String"
}
```

---

### v_politicos

```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "apellido": "String",
  "edad": "Number",
  "correo": "String",
  "photoURL": "String",
  "codigo_postal": "String",
  "colonia": "String",
  "ciudad": "String",
  "estado": "String",
  "candidatura": "String",
  "cedula_politica": "String",
  "validacion": "String"
}
```

---

### v_votantes

```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "apellido": "String",
  "edad": "Number",
  "correo": "String",
  "codigo_postal": "String",
  "colonia": "String",
  "ciudad": "String",
  "estado": "String",
  "propuestas_votadas": ["ObjectId"],
  "preferencias": ["String"]
}
```

---

### v_propuestas

```json
{
  "_id": "ObjectId",
  "id_politico": "ObjectId",
  "titulo": "String",
  "descripcion": "String",
  "categoria": "String",
  "valoracion": ["Number"],
  "votos": [
    {
      "id_votante": "ObjectId"
    }
  ]
}
```

---

## 📊 Endpoints

### 📄 **Rutas para `/api/administrador`**

| Método | Endpoint                          | Descripción                                 |
|--------|-----------------------------------|---------------------------------------------|
| GET    | `/api/administrador/`             | Obtener todos los administradores           |
| GET    | `/api/administrador/`         | Obtener un administrador por su ID          |
| GET    | `/api/administrador/correo/` | Obtener un administrador por su CORREO    |

---

### 📄 **Rutas para `/api/politico`**

| Método | Endpoint                              | Descripción                                        |
|--------|---------------------------------------|----------------------------------------------------|
| POST   | `/api/politico/`                      | Crear un nuevo político con validación             |
| GET    | `/api/politico/`                      | Obtener todos los políticos                        |
| GET    | `/api/politico/`                  | Obtener un político por su ID                      |
| GET    | `/api/politico/correo/`       | Obtener un político por su CORREO                  |
| PUT    | `/api/politico/`                  | Actualizar político por ID con validación parcial  |
| DELETE | `/api/politico/`                  | Eliminar un político por ID                        |

---

### 📄 **Rutas para `/api/votante`**

| Método | Endpoint                          | Descripción                                    |
|--------|-----------------------------------|------------------------------------------------|
| POST   | `/api/votante/`                  | Crear nuevo votante con validación completa    |
| POST   | `/api/votante/login/`                | Inicia sesión, recibiendo el correo y contraseña, verificando la contraseña existente en la base de datos, con la introducida, además, genera un JWT|
| GET    | `/api/votante/`                  | Obtener todos los votantes                     |
| GET    | `/api/votante/`              | Obtener votante por ID                         |
| GET    | `/api/votante/correo/`   | Obtener votante por correo electrónico         |
| PUT    | `/api/votante/`              | Actualizar votante con validación parcial      |
| PUT    | `/api/votante/manual/`           | Actualizar votante por ID con validación parcial, verificando el JWT|
| DELETE | `/api/votante/`              | Eliminar votante por ID                        |
| GET    | `/api/votante/preguntas`         | Obtener cuestionario de preferencias (10 categorías con 3 preguntas cada una) |

---

### Estructura del cuestionario de preferencias (ejemplo)

```json
{
  "categorias": [
    {
      "numero": 1,
      "nombre": "Economía y Empleo",
      "preguntas": [
        "¿Apoya políticas para crear más empleo...?",
        "¿Está a favor de incentivos...?",
        "¿Cree que es clave capacitar...?"
      ]
    },
    // ... (9 categorías adicionales)
  ]
}
```

---

### 📄 **Rutas para `/api/propuestas`**

| Método | Endpoint                                 | Descripción                                                                                 |
|--------|------------------------------------------|---------------------------------------------------------------------------------------------|
| GET    | `/api/propuestas/`                       | Obtener todas las propuestas. Incluye datos completos del político asociado.                |
| GET    | `/api/propuestas/ultimas`                | Obtener las 5 propuestas más recientes.                                                     |
| GET    | `/api/propuestas/`                   | Obtener una propuesta por su ID.                                                            |
| GET    | `/api/propuestas/politico/` | Obtener todas las propuestas creadas por un político específico.                            |
| POST   | `/api/propuestas/`                       | Crear una nueva propuesta. Valida político, usa IA para valoración y asigna votos automáticos.|
| PUT    | `/api/propuestas/`                   | Actualizar una propuesta por ID con validación parcial.                                     |
| DELETE | `/api/propuestas/`                   | Eliminar una propuesta por ID.                                                              |

---

### 📄 **Rutas para `/api/estadisticas`**

| Método | Endpoint                          | Descripción                                      |
|--------|-----------------------------------|--------------------------------------------------|
| GET    | `/api/estadisticas/dashboard`     | Obtener estadísticas generales del sistema      |

---
