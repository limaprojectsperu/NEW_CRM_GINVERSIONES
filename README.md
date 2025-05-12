# Nombre del Proyecto Django

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.0%2B-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Breve descripción del proyecto (1-2 párrafos explicando su propósito y funcionalidades principales).

## 🚀 Características principales

- Lista de las funcionalidades clave
- Tecnologías utilizadas
- Integraciones con otros servicios

## 📦 Prerrequisitos

- Python 3.8+
- Django 4.0+
- PostgreSQL/MySQL (o la base de datos que uses)
- Otras dependencias importantes

## 🛠️ Configuración del entorno

### 1. Clonar el repositorio

```bash
git clone git@github.com:limaprojectsperu/NEW_CRM_GINVERSIONES.git
cd NEW_CRM_GINVERSIONES
```

### 2. Crear y activar entorno virtual (recomendado)

```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con:

```ini
POSTGRES_DB=grupoimagen
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin
DEBUG=True
# Otras variables necesarias
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

## 🧪 Ejecutar tests

```bash
python manage.py test
```

## 🌍 Despliegue

Instrucciones básicas para desplegar en plataformas como:
- Heroku
- AWS
- DigitalOcean
- PythonAnywhere

## 🤝 Cómo contribuir

1. Haz un fork del proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✉️ Contacto

RTM Software - ventas@rtmsoftware.com

Yefer Espinoza - espinozayefer96@gmail.com
