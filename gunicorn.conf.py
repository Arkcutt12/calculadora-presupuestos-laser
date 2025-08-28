# Configuración de Gunicorn para Render
import os

# Puerto de Render (variable de entorno)
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Workers (recomendado: 2 * CPU cores + 1)
workers = 2

# Clase de worker para FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout para requests
timeout = 30

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Graceful shutdown
graceful_timeout = 10

# Reiniciar workers después de N requests para prevenir memory leaks
max_requests = 1000
max_requests_jitter = 50