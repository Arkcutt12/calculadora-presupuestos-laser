import os
import requests
from typing import Dict, Any
import argparse

# Configuración de la API key
API_KEY = os.getenv('OPENWEATHER_API_KEY', '')  # Dejar vacío por defecto

def get_weather(city: str) -> Dict[str, Any]:
    """
    Obtiene el clima de una ciudad usando la API de OpenWeatherMap
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric',  # Para temperatura en Celsius
            'lang': 'es'  # Para descripciones en español
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        weather_info = {
            'ciudad': data['name'],
            'pais': data['sys']['country'],
            'temperatura': f"{data['main']['temp']}°C",
            'sensacion_termica': f"{data['main']['feels_like']}°C",
            'humedad': f"{data['main']['humidity']}%",
            'presion': f"{data['main']['pressure']} hPa",
            'descripcion': data['weather'][0]['description'],
            'viento_velocidad': f"{data['wind']['speed']} m/s",
            'visibilidad': f"{data.get('visibility', 'N/A')} metros"
        }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Error al obtener datos del clima: {str(e)}'}
    except KeyError as e:
        return {'error': f'Error en el formato de datos: {str(e)}'}

class WeatherAgent:
    def __init__(self):
        self.name = "weather_agent"
        self.description = "Un agente del clima que puede obtener información meteorológica de una ciudad"
    
    def get_weather_info(self, city: str) -> str:
        """
        Obtiene y formatea la información del clima
        """
        weather_data = get_weather(city)
        
        if 'error' in weather_data:
            return f"❌ Error: {weather_data['error']}"
        
        # Formatear la respuesta de manera amigable
        response = f"""
🌤️  CLIMA EN {weather_data['ciudad'].upper()}, {weather_data['pais']} 🌤️

🌡️  Temperatura: {weather_data['temperatura']}
🌡️  Sensación térmica: {weather_data['sensacion_termica']}
💧 Humedad: {weather_data['humedad']}
🌪️  Viento: {weather_data['viento_velocidad']}
👁️  Visibilidad: {weather_data['visibilidad']}
📊 Presión: {weather_data['presion']}
☁️  Condición: {weather_data['descripcion'].title()}
        """
        
        return response.strip()

def main():
    parser = argparse.ArgumentParser(description='Agente del Clima - Consulta información meteorológica')
    parser.add_argument('ciudad', nargs='?', help='Nombre de la ciudad para consultar el clima')
    parser.add_argument('--api-key', help='Tu API key de OpenWeatherMap')
    
    args = parser.parse_args()
    
    # Configurar API key
    global API_KEY
    if args.api_key:
        API_KEY = args.api_key
    elif not API_KEY:
        print("⚠️  ADVERTENCIA: No se ha configurado la API key de OpenWeatherMap")
        print("Para obtener una API key gratuita, visita: https://openweathermap.org/api")
        print("\n¿Tienes tu API key? Puedes:")
        print("1. Configurar la variable de entorno: $env:OPENWEATHER_API_KEY='tu_api_key'")
        print("2. Usar --api-key: python agent.py --api-key 'tu_api_key' 'Madrid'")
        print("3. Ingresarla ahora (se guardará temporalmente):")
        
        api_key_input = input("\nIngresa tu API key de OpenWeatherMap: ").strip()
        if api_key_input:
            API_KEY = api_key_input
            print("✅ API key configurada temporalmente")
        else:
            print("❌ No se proporcionó API key. Saliendo...")
            return
    
    # Crear instancia del agente
    agent = WeatherAgent()
    
    # Si no se proporciona ciudad como argumento, usar modo interactivo
    if not args.ciudad:
        print("🌤️  AGENTE DEL CLIMA 🌤️")
        print("Escribe 'salir' para terminar")
        print("-" * 40)
        
        while True:
            try:
                ciudad = input("\n🏙️  ¿De qué ciudad quieres saber el clima? ").strip()
                
                if ciudad.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if not ciudad:
                    print("❌ Por favor, ingresa el nombre de una ciudad")
                    continue
                
                print("\n🔍 Consultando el clima...")
                resultado = agent.get_weather_info(ciudad)
                print(resultado)
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
    else:
        # Modo directo con ciudad como argumento
        print(f"🔍 Consultando el clima de {args.ciudad}...")
        resultado = agent.get_weather_info(args.ciudad)
        print(resultado)

if __name__ == "__main__":
    main()