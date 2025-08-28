# 🌤️ Agente del Clima

Un agente inteligente que te permite consultar información meteorológica de cualquier ciudad del mundo desde la terminal.

## 🚀 Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Obtener API Key gratuita:**
   - Ve a [OpenWeatherMap](https://openweathermap.org/api)
   - Regístrate gratuitamente
   - Obtén tu API key

## 🔧 Configuración

### Opción 1: Variable de entorno (Recomendado)
```bash
# Windows (PowerShell)
$env:OPENWEATHER_API_KEY="tu_api_key_aqui"

# Windows (CMD)
set OPENWEATHER_API_KEY=tu_api_key_aqui

# Linux/Mac
export OPENWEATHER_API_KEY="tu_api_key_aqui"
```

### Opción 2: Pasar como argumento
```bash
python agent.py --api-key "tu_api_key_aqui" "Madrid"
```

## 📖 Uso

### Modo interactivo (Recomendado)
```bash
python agent.py
```
Luego simplemente escribe el nombre de la ciudad cuando te pregunte.

### Modo directo
```bash
python agent.py "Madrid"
python agent.py "New York"
python agent.py "Tokyo"
```

### Con API key como argumento
```bash
python agent.py --api-key "tu_api_key" "Barcelona"
```

## 🎯 Ejemplos de uso

```bash
# Consultar clima de Madrid
python agent.py "Madrid"

# Consultar clima de Nueva York
python agent.py "New York"

# Modo interactivo
python agent.py
# Luego escribe: Madrid
# Luego escribe: Barcelona
# Luego escribe: salir
```

## 📊 Información que proporciona

- 🌡️ Temperatura actual
- 🌡️ Sensación térmica
- 💧 Humedad
- 🌪️ Velocidad del viento
- 👁️ Visibilidad
- 📊 Presión atmosférica
- ☁️ Condición del clima

## 🛠️ Tecnologías utilizadas

- **Python 3.7+**
- **requests**: Para hacer llamadas a la API
- **OpenWeatherMap API**: Para obtener datos meteorológicos
- **argparse**: Para procesar argumentos de línea de comandos

## 🔍 Solución de problemas

### Error: "No se ha configurado la API key"
- Asegúrate de haber configurado la variable de entorno `OPENWEATHER_API_KEY`
- O pasa la API key como argumento con `--api-key`

### Error: "Error al obtener datos del clima"
- Verifica que tu API key sea válida
- Asegúrate de tener conexión a internet
- Verifica que el nombre de la ciudad sea correcto

### Error: "Ciudad no encontrada"
- Intenta con el nombre en inglés
- Usa el formato "Ciudad, País" (ej: "Madrid, Spain")
