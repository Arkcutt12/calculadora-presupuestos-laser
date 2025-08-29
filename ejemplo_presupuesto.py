#!/usr/bin/env python3

from laser_agent import LaserCuttingAgent

def crear_presupuesto_ejemplo():
    # Crear instancia del agente
    agent = LaserCuttingAgent()
    
    # Datos de ejemplo similar a los que envía el frontend
    datos_ejemplo = {
        "Cliente": {
            "Nombre y Apellidos": "Iván Hierro",
            "Mail": "ivan.hierro@alumni.mondragon.edu",
            "Número de Teléfono": "+34661691017"
        },
        "Pedido": {
            "Número de solicitud": "DXF500098",
            "Fecha de solicitud": "2025-08-29T05:04:45.565Z",
            "Material seleccionado": "Contrachapado",
            "Longitud vector total": "64.712 m",
            "Area material": "1553733.0625720571 mm²",
            "Solicitud urgente": False,
            "¿Quién proporciona el material?": {
                "proveedor": "Arkcutt",
                "Material seleccionado": "Contrachapado",
                "Grosor": "4",
                "Color": "light-wood"
            },
            "Capas": [
                {
                    "nombre": "corte interior",
                    "vectores": 161,
                    "longitud_mm": 4877.36,
                    "longitud_m": 4.87736,
                    "area_material": 0
                },
                {
                    "nombre": "1_LimiteMaterial",
                    "vectores": 9,
                    "longitud_mm": 11460.48,
                    "longitud_m": 11.46048,
                    "area_material": 0
                },
                {
                    "nombre": "corte exterior",
                    "vectores": 239,
                    "longitud_mm": 44972.35,
                    "longitud_m": 44.97235,
                    "area_material": 0
                },
                {
                    "nombre": "2_Gravado",
                    "vectores": 64,
                    "longitud_mm": 3401.93,
                    "longitud_m": 3.40193,
                    "area_material": 0
                }
            ],
            "Datos Recogida": {
                "tipo": "Recogida en tienda",
                "ciudad_seleccionada": "Barcelona"
            }
        }
    }
    
    # Calcular presupuesto
    print("Calculando presupuesto...")
    budget_result = agent.calculate_budget_from_frontend(datos_ejemplo)
    
    if 'error' in budget_result:
        print(f"Error: {budget_result['error']}")
        return
    
    # Generar PDF de ejemplo
    pdf_path = "C:\\Users\\hiero\\Desktop\\Aprender\\presupuesto_ejemplo.pdf"
    print("Generando PDF...")
    
    try:
        agent.generate_pdf_quote(budget_result, pdf_path)
        print(f"PDF generado exitosamente: {pdf_path}")
        print(f"Total del presupuesto: {budget_result['total']:.2f}€")
    except Exception as e:
        print(f"Error generando PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crear_presupuesto_ejemplo()