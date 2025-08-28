# 🚀 Desplegar en Render - Calculadora de Presupuestos Láser

Guía paso a paso para desplegar tu API en Render (gratis).

## 📋 Pre-requisitos

1. **Cuenta en Render**: https://render.com
2. **Repositorio Git**: Tu código subido a GitHub, GitLab o Bitbucket
3. **Archivos preparados**: ✅ Ya están listos en tu proyecto

## 🛠️ Archivos de Configuración (Ya Creados)

- ✅ `render.yaml` - Configuración del servicio
- ✅ `gunicorn.conf.py` - Configuración del servidor de producción  
- ✅ `requirements.txt` - Dependencias actualizadas
- ✅ `api.py` - Optimizado para producción

## 🚀 Pasos para Desplegar

### 1. Subir código a repositorio Git

```bash
# Inicializar Git (si no está inicializado)
git init

# Añadir todos los archivos
git add .

# Commit
git commit -m "Preparar API para despliegue en Render"

# Añadir repositorio remoto (sustituir por tu URL)
git remote add origin https://github.com/TU_USUARIO/calculadora-presupuestos.git

# Subir a GitHub/GitLab
git push -u origin main
```

### 2. Crear servicio en Render

1. **Ir a Render Dashboard**: https://dashboard.render.com
2. **Hacer clic en "New"** → **"Web Service"**
3. **Conectar repositorio**: Selecciona tu repositorio Git
4. **Configurar servicio**:

   - **Name**: `calculadora-presupuestos-laser`
   - **Environment**: `Python`
   - **Region**: `Frankfurt` (más cerca de España)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -c gunicorn.conf.py api:app`

### 3. Variables de Entorno (Opcional)

En la sección **Environment Variables**:

```
RENDER=true
PYTHON_VERSION=3.12.0
```

### 4. Configurar CORS para tu Frontend

**Editar `api.py` línea 14:**
```python
FRONTEND_URLS = [
    "https://tu-dominio-frontend.vercel.app",  # ← Cambiar por tu URL real
    "http://localhost:3000",
    "http://localhost:8080"
]
```

### 5. Hacer clic en "Create Web Service"

Render comenzará el despliegue automáticamente.

## 📍 URLs una vez desplegado

- **API**: `https://calculadora-presupuestos-laser.onrender.com`
- **Documentación**: `https://calculadora-presupuestos-laser.onrender.com/docs`
- **Health Check**: `https://calculadora-presupuestos-laser.onrender.com/health`

## 🧪 Probar la API Desplegada

```bash
# Health check
curl https://calculadora-presupuestos-laser.onrender.com/health

# Calcular presupuesto
curl -X POST "https://calculadora-presupuestos-laser.onrender.com/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "Cliente": {
      "Nombre y Apellidos": "Test User",
      "Mail": "test@example.com"
    },
    "Pedido": {
      "¿Quién proporciona el material?": {
        "Material seleccionado": "Contrachapado",
        "Grosor": "4mm",
        "Color": "light-wood"
      },
      "Area material": "10 mm²",
      "Capas": [
        {
          "nombre": "Cortes exterior",
          "longitud_m": 0.5
        }
      ]
    }
  }'
```

## 🔄 Actualizar la API

Cada vez que hagas `git push`, Render automáticamente:
1. Detecta los cambios
2. Reconstruye la aplicación  
3. La redespliega

## 💰 Costos

**Plan Gratuito de Render incluye:**
- ✅ 750 horas/mes (suficiente para uso continuo)
- ✅ SSL certificado automático
- ✅ Dominio personalizable
- ⚠️ La aplicación puede "dormir" tras 15min sin uso
- ⚠️ Tarda ~30s en "despertar"

**Para uso intensivo:** Plan pagado desde $7/mes sin limitaciones.

## 🛠️ Troubleshooting

### Build falla
```bash
# Ver logs completos en Render Dashboard
# Verificar que requirements.txt está correctamente
```

### API no responde
```bash
# Verificar logs del servicio
# Confirmar que el puerto está configurado correctamente
```

### Error de CORS
```python
# Verificar FRONTEND_URLS en api.py línea 13-17
# Añadir tu dominio del frontend
```

## 📱 Integración Frontend

Una vez desplegado, cambiar la URL en tu frontend:

```javascript
// Desarrollo
const API_URL = 'http://localhost:8000';

// Producción  
const API_URL = 'https://calculadora-presupuestos-laser.onrender.com';

const response = await fetch(`${API_URL}/calculate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formularioData)
});
```

## 🎉 ¡Listo!

Tu API estará disponible 24/7 en la nube con:
- ✅ HTTPS automático
- ✅ Escalado automático  
- ✅ Logs en tiempo real
- ✅ Deploy automático desde Git
- ✅ Monitoreo de uptime

**URL de ejemplo final:**
`https://calculadora-presupuestos-laser.onrender.com/calculate`