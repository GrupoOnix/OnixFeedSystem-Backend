# Análisis de Requerimientos

Hora de creación: 16 de septiembre de 2025 11:17
Estado: Listo

# Información del documento

- Version: 1.0
- Fecha: Septiembre 2025
- Autor: Jonatan Reyes
- Cliente: Onix Servicios
- Estado: En desarrollo

# Introducción

## Proposito del documento

Este documento define los requerimientos funcionales y no funcionales para el desarrollo del Sistema de Alimentación Onix para centros acuícolas. Servirá como referencia técnica para el desarrollo, testing y validación del sistema.

# Requerimientos funcionales

### RF-01: Control de Dispositivos

- El sistema debe permitir la creación de líneas de alimentación mediante interfaz gráfica de arrastrar y soltar
- Debe permitir controlar los sopladores, dosificadores y selectoras del pontón desde la interfaz de usuario.
- Debe poder establecer: cantidad de alimento, tiempo de dosificación, jaula de destino.
- Debe poder iniciar, pausar y detener alimentaciones de forma manual o automática.
- Debe validar los parámetros antes de ejecutar las instrucciones.

### RF-02: Configuración del Sistema

- El sistema debe permitir la configuración de parámetros de operación para los equipos.
- Debe permitir la creación y edición de grupos de alimentación.
- Debe incluir la capacidad de configurar alertas.
- Debe permitir la calibración de dosificadores y selectoras desde la interfaz.

### RF-03: Monitoreo de Equipos

- El sistema debe mostrar en tiempo real el estado de los equipos conectados.
- Debe detectar y mostrar fallas automáticamente
- Debe mostrar indicadores visuales de estado (operativo, falla, falta de configuración, etc)

### RF-04: Gestión de Usuarios

- El sistema debe permitir la creación y administración de cuentas de usuario.
- Debe implementar roles con diferentes niveles de acceso (técnico, operador).
- Debe restringir funcionalidades según roles

### RF-05: Gestión de Silos

- Debe permitir registrar la cantidad de alimento ingresado.
- El sistema debe calcular y mostrar el nivel de alimento restante en los silos.
- Debe alertar cuando el nivel de alimento esté por debajo del umbral configurable.
- Debe registrar el consumo de alimento por silo y tipo de alimento.

### RF-06: Monitoreo de alimentación

- El sistema debe registrar la cantidad de alimento dispensado por jaula
- Debe mostrar el flujo de alimento a las jaulas
- Debe registrar los tiempos de inicio y fin de cada alimentación

### RF-07: Autenticación de usuarios

- El sistema debe incluir módulo de login con autenticación segura
- Debe tener gestión de usuarios con distintos perfiles (técnico, operador)
- Debe incluir funcionalidades de cambio de contraseña

### RF-08: Sistema de alertas

- Debe generar alertas visuales por fallas de equipos
- Debe alertar por alimentación no completada o interrumpida
- Debe alertar por parámetros no válidos o peligrosos
- Debe permitir configurar umbrales de alerta

# Requerimientos no funcionales

- RNF-01: Backend desarrollado en Python con librerías de uso gratuito
- RNF-02: Frontend desarrollado en React con interfaz intuitiva
- RNF-03: API Restful documentada entre Backend y Frontend
- RNF-04: Base de datos relacional para almacenamiento de datos operativos
- RNF-05: El sistema debe tener un tiempo de respuesta menor a 1 segundo para operaciones críticas
- RNF-06: Disponibilidad del sistema de al menos 99.5% durante las operaciones diarias
- RNF-07: Interfaz de usuario compatible con computadores con resolución mínima de 1024x768
- RNF-08: Capacidad de operar sin conexión a internet
- RNF-09: Sistema de logs detallado para auditoría y diagnóstico de problemas
- RNF-10: Cumplimiento con estándares de seguridad para protección de datos operativos
- RNF-11: Documentación técnica completa del sistema y manuales de usuario
- RNF-12: Interfaz y documentación técnica en español
- RNF-13: Escalabilidad y compatibilidad con futuras expansiones de funcionalidad
- RNF-14 El sistema debe ser ligero para correr en un computador de escritorio (4gb de ram, 30 gb almacenamiento)