# 🔪 Agente de Presupuestos de Corte Láser

Un agente inteligente que calcula presupuestos para servicios de corte láser basado en longitud del vector, material, grosor y cantidad.

## 🚀 Características

- ✅ **Cálculo automático** de tiempo de corte
- ✅ **Base de datos de materiales** con precios y parámetros
- ✅ **Cálculo de costes** de material y corte
- ✅ **Parámetros de corte** automáticos (velocidad, potencia, fuerza aire)
- ✅ **Margen de beneficio** configurable (50% por defecto)
- ✅ **Exportación a PDF** del presupuesto
- ✅ **Modo interactivo** y **modo directo**
- ✅ **Configuración JSON** personalizable

## 📋 Requisitos

- Python 3.7+
- Dependencias:
  ```bash
  pip install -r requirements.txt
  ```

## 🎯 Uso

### Modo Interactivo (Recomendado)
```bash
python laser_agent.py
```

### Modo Directo
```bash
python laser_agent.py --longitud 2.5 --material "MDF" --grosor 3 --color "Natural" --cantidad 0.5
```

### Exportar a PDF
```bash
python laser_agent.py --longitud 2.5 --material "MDF" --grosor 3 --color "Natural" --cantidad 0.5 --pdf "presupuesto.pdf"
```

### Ver Materiales Disponibles
```bash
python laser_agent.py
# Luego escribe: materiales
```

## 📊 Ejemplo de Salida

```
🔪 PRESUPUESTO CORTE LÁSER 🔪

📏 Longitud del vector: MDF 3mm Natural
⏱️  Tiempo de corte: 2.08 minutos
💰 Coste corte: 1.66€
📦 Coste material: 5.38€
📊 Subtotal: 7.04€
💵 Margen (50%): 3.52€
🎯 TOTAL: 10.56€

⚙️  Parámetros de corte:
  • Velocidad: 1200 mm/min
  • Potencia láser: 80%
  • Fuerza aire: 0.8 bar
```

## ⚙️ Configuración

### Archivo JSON (`laser_config.json`)

```json
{
  "tarifa_por_minuto": 0.8,
  "margen_beneficio": 50,
  "materiales": [
    {
      "material": "MDF",
      "grosor": 3,
      "color": "Natural",
      "precio_plancha": 15.50,
      "tamaño_plancha": 1.44,
      "velocidad_corte": 1200,
      "potencia_laser": 80,
      "fuerza_aire": 0.8
    }
  ]
}
```

### Campos de Material

- **material**: Nombre del material (MDF, Acrílico, etc.)
- **grosor**: Grosor en milímetros
- **color**: Color del material
- **precio_plancha**: Precio por plancha en euros
- **tamaño_plancha**: Tamaño de la plancha en m²
- **velocidad_corte**: Velocidad de corte en mm/min
- **potencia_laser**: Potencia del láser en porcentaje
- **fuerza_aire**: Fuerza del aire en bar

## 🧮 Cálculos

### Tiempo de Corte
```
Tiempo (min) = Longitud (m) / (Velocidad (mm/min) / 1000)
```

### Coste de Corte
```
Coste Corte = Tiempo (min) × Tarifa por minuto
```

### Coste de Material
```
Planchas necesarias = Cantidad (m²) / Tamaño plancha (m²)
Coste Material = Planchas necesarias × Precio plancha
```

### Total
```
Subtotal = Coste Corte + Coste Material
Margen = Subtotal × (Margen % / 100)
Total = Subtotal + Margen
```

## 📝 Personalización

### Añadir Nuevos Materiales

1. Edita `laser_config.json`
2. Añade un nuevo objeto en el array `materiales`
3. Incluye todos los campos requeridos

### Cambiar Tarifas

1. Modifica `tarifa_por_minuto` en el JSON
2. Ajusta `margen_beneficio` según necesites

### Crear Configuración Personalizada

```bash
python laser_agent.py --config "mi_config.json"
```

## 🎯 Comandos Útiles

```bash
# Ver materiales disponibles
python laser_agent.py
# Luego escribe: materiales

# Presupuesto rápido
python laser_agent.py --longitud 1.5 --material "Acrílico" --grosor 3 --color "Transparente" --cantidad 0.3

# Modo interactivo
python laser_agent.py
```

## 🔧 Solución de Problemas

### Error: "Material no encontrado"
- Verifica que el material, grosor y color coincidan exactamente
- Usa el comando `materiales` para ver opciones disponibles

### Error: "La longitud debe ser un número"
- Asegúrate de usar números decimales (ej: 2.5, no 2,5)

### Error: "Grosor debe ser un número entero"
- El grosor debe ser un número entero (ej: 3, 6, 9)

## 📈 Materiales Incluidos

- **MDF**: 3mm, 6mm, 9mm (Natural)
- **Acrílico**: 3mm, 5mm (Transparente, Negro)
- **Contrachapado**: 3mm, 6mm (Natural)
- **DM**: 3mm, 6mm (Blanco)

¡Tu agente de presupuestos de corte láser está listo! 🎉

¡Listo! Ahora puedes generar presupuestos y exportarlos a PDF.
