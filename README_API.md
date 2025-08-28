# 🚀 API Calculadora de Presupuestos Láser

API REST para calcular presupuestos de corte láser basado en archivos DXF procesados por el frontend.

## 🏃 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Lanzar el servidor
```bash
python api.py
```

La API estará disponible en: **http://localhost:8000**

## 📚 Endpoints Disponibles

### 🏠 `/` - Información de la API
```http
GET /
```
**Respuesta:**
```json
{
  "message": "API Calculadora de Presupuestos Láser",
  "version": "1.0.0", 
  "status": "online",
  "endpoints": { ... }
}
```

### 💰 `/calculate` - Calcular Presupuesto
```http
POST /calculate
Content-Type: application/json
```

**Cuerpo (JSON del formulario):**
```json
{
  "Cliente": {
    "Nombre y Apellidos": "Juan Pérez",
    "Mail": "juan@example.com",
    "Número de Teléfono": "+34123456789"
  },
  "Pedido": {
    "Material seleccionado": "Contrachapado",
    "Area material": "10 mm²",
    "¿Quién proporciona el material?": {
      "Material seleccionado": "Contrachapado",
      "Grosor": "4mm", 
      "Color": "light-wood"
    },
    "Capas": [
      {
        "nombre": "Cortes exterior",
        "longitud_m": 0.5
      },
      {
        "nombre": "Cortes interior", 
        "longitud_m": 0.2
      }
    ]
  }
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "material": { ... },
    "tiempo_corte_minutos": 2.5,
    "coste_corte": 2.0,
    "coste_material": 5.5,
    "subtotal": 7.5,
    "margen_beneficio": 3.75,
    "total": 11.25,
    "layers": [ ... ],
    "parametros_corte": { ... },
    "frontend_info": { ... }
  }
}
```

### 📄 `/calculate/pdf` - Presupuesto + PDF
```http
POST /calculate/pdf
Content-Type: application/json
```
Mismo cuerpo que `/calculate`, pero devuelve el PDF como descarga.

### 📦 `/materiales` - Materiales Disponibles
```http
GET /materiales
```
**Respuesta:**
```json
{
  "materiales": [
    "MDF 2.5mm Natural",
    "Contrachapado 4mm Natural", 
    ...
  ],
  "detalle": [ ... ],
  "total": 10
}
```

### ⚙️ `/config` - Configuración
```http
GET /config
```
**Respuesta:**
```json
{
  "tarifa_por_minuto": 0.8,
  "margen_beneficio": 50,
  "total_materiales": 10
}
```

### 🔍 `/health` - Estado de la API
```http
GET /health
```
**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "materiales_disponibles": 10
}
```

## 🌐 Integración Frontend

### JavaScript/Fetch
```javascript
const calculateBudget = async (formularioData) => {
  try {
    const response = await fetch('http://localhost:8000/calculate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formularioData)
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Presupuesto:', result.data);
      return result.data;
    } else {
      console.error('Error:', result.error);
    }
  } catch (error) {
    console.error('Error de conexión:', error);
  }
};
```

### Descargar PDF
```javascript
const downloadPDF = async (formularioData) => {
  try {
    const response = await fetch('http://localhost:8000/calculate/pdf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formularioData)
    });
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'presupuesto.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    console.error('Error descargando PDF:', error);
  }
};
```

## 📖 Documentación Interactiva

Una vez lanzada la API, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuración

### Variables de Entorno (Opcional)
```bash
# Puerto de la API (por defecto: 8000)
export PORT=8000

# Host (por defecto: 0.0.0.0)
export HOST=localhost
```

### Archivo de Configuración
Los materiales y tarifas se configuran en `laser_config.json`.

## 🚀 Despliegue en Producción

### Usando Uvicorn directamente
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Usando Gunicorn (Linux/Mac)
```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## ⚠️ Consideraciones de Seguridad

Para producción:
1. **Limitar CORS**: Cambiar `allow_origins=["*"]` por tu dominio
2. **Añadir autenticación**: Implementar tokens o API keys  
3. **Límites de tasa**: Prevenir abuso de la API
4. **HTTPS**: Usar certificados SSL

## 🐛 Troubleshooting

### Error: "Port already in use"
```bash
# Encontrar proceso usando el puerto
netstat -ano | findstr :8000
# Matar proceso
taskkill /PID <PID> /F
```

### Error: "Module not found"
```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Error de CORS
Verifica que el frontend esté haciendo peticiones al puerto correcto (8000).

## 📊 Ejemplo de Respuesta Completa

```json
{
  "success": true,
  "data": {
    "material": {
      "material": "Contrachapado",
      "grosor": 4,
      "color": "Natural",
      "precio_plancha": 21.5,
      "tamaño_plancha": 1.44
    },
    "tiempo_corte_minutos": 12.12,
    "coste_corte": 9.7,
    "coste_material": 23.2,
    "subtotal": 32.9,
    "margen_beneficio": 16.45,
    "total": 49.34,
    "layers": [
      {
        "name": "corte exterior",
        "type": "cut_outside", 
        "length_m": 44.97,
        "time_min": 9.369
      }
    ],
    "parametros_corte": {
      "cut": {
        "velocidad": "28% (84.0 mm/s)",
        "potencia": "87%",
        "aire": "0.8 bar"
      }
    },
    "frontend_info": {
      "numero_solicitud": "DXF366699",
      "cliente": { ... },
      "urgente": false
    }
  }
}
```