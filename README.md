# Smart Parking App

Aplicación para encontrar aparcamiento en la calle con sistema anti-fraude y detección automática de estacionamiento.

## Características

- Reportar espacios de aparcamiento disponibles
- Buscar espacios cercanos
- Sistema de reputación de usuarios
- Detección automática de estacionamiento
- Prevención de reportes falsos
- Sistema de confirmación y reporte de espacios

## Requisitos

- Python 3.8+
- Flask y dependencias (ver requirements.txt)
- React Native (para la app móvil)

## Configuración del Backend

1. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Iniciar el servidor:
```bash
python app.py
```

## Características de Seguridad

- Sistema de reputación de usuarios
- Límite de tiempo entre reportes (5 minutos)
- Reputación mínima requerida para reportar
- Sistema de confirmación comunitaria
- Detección automática de estacionamiento

## API Endpoints

- `/register` - Registro de usuarios
- `/login` - Inicio de sesión
- `/report-spot` - Reportar espacio disponible
- `/nearby-spots` - Buscar espacios cercanos
- `/confirm-spot/<id>` - Confirmar espacio disponible
- `/report-fake/<id>` - Reportar espacio falso
- `/parking-event` - Registrar evento de estacionamiento
