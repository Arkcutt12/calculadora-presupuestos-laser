from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
from laser_agent import LaserCuttingAgent
import tempfile

# Configuración para producción
PRODUCTION = os.getenv('RENDER') is not None
FRONTEND_URLS = [
    "https://tu-frontend.vercel.app",  # Cambiar por tu URL del frontend
    "http://localhost:3000",           # Para desarrollo local
    "http://localhost:8080"            # Para desarrollo local alternativo
]

app = FastAPI(
    title="Calculadora de Presupuestos Láser",
    description="API para calcular presupuestos de corte láser basado en archivos DXF",
    version="1.0.0"
)

# Configurar CORS para permitir conexiones del frontend
origins = ["*"] if not PRODUCTION else FRONTEND_URLS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Instancia global del agente láser
laser_agent = LaserCuttingAgent()

def adapt_frontend_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapta el formato del frontend Next.js al formato esperado por laser_agent
    """
    if not data:
        raise ValueError("Datos del formulario vacíos")
    
    # Si ya tiene el formato antiguo, devolverlo tal como está
    if "Cliente" in data and "Pedido" in data:
        return data
    
    # Adaptar formato del frontend Next.js
    adapted = {
        "Cliente": {},
        "Pedido": {}
    }
    
    # Adaptar información del cliente
    if "cliente" in data and data["cliente"] is not None and isinstance(data["cliente"], dict):
        cliente_data = data["cliente"]
        adapted["Cliente"] = {
            "Nombre y Apellidos": cliente_data.get("nombre_completo", ""),
            "Mail": cliente_data.get("email", ""),
            "Número de Teléfono": cliente_data.get("telefono", "")
        }
    
    # Adaptar información del pedido
    if "pedido" in data and data["pedido"] is not None and isinstance(data["pedido"], dict):
        pedido_data = data["pedido"]
        
        # Información básica del pedido
        adapted["Pedido"] = {
            "Número de solicitud": data.get("numero_solicitud", ""),
            "Fecha de solicitud": data.get("fecha_solicitud", ""),
            "Material seleccionado": pedido_data.get("material_seleccionado", ""),
            "Longitud vector total": f"{pedido_data.get('longitud_vector_total_metros', 0)} m",
            "Area material": f"{pedido_data.get('area_material', 0)} mm²",
            "Solicitud urgente": pedido_data.get("servicio_urgente", "no") == "sí"
        }
        
        # Información del material - BASADA EN TU ESTRUCTURA REAL
        # Tu frontend NO envía detalles_material, necesitamos valores por defecto
        adapted["Pedido"]["¿Quién proporciona el material?"] = {
            "proveedor": "Arkcutt",
            "Material seleccionado": pedido_data.get("material_seleccionado", "Contrachapado"),
            "Grosor": "4",
            "Color": "light-wood"
        }
        
        # Adaptar capas del frontend
        capas_data = pedido_data.get("capas")
        if capas_data is not None and isinstance(capas_data, list):
            adapted_capas = []
            for capa in capas_data:
                if capa is not None and isinstance(capa, dict):
                    # Obtener longitud y convertir a número seguro
                    longitud_mm = capa.get("longitud_mm", 0)
                    try:
                        longitud_mm = float(longitud_mm) if longitud_mm is not None else 0
                    except (ValueError, TypeError):
                        longitud_mm = 0
                    
                    adapted_capa = {
                        "nombre": str(capa.get("nombre", "")),
                        "vectores": int(capa.get("vectores", 0)) if capa.get("vectores") else 0,
                        "longitud_mm": longitud_mm,
                        "longitud_m": longitud_mm / 1000,
                        "area_material": float(capa.get("area_material", 0)) if capa.get("area_material") else 0
                    }
                    adapted_capas.append(adapted_capa)
            
            adapted["Pedido"]["Capas"] = adapted_capas
        
        # Información de recogida
        datos_recogida = pedido_data.get("datos_recogida")
        if datos_recogida is not None and isinstance(datos_recogida, dict):
            adapted["Pedido"]["Datos Recogida"] = datos_recogida
    
    # Validar que tenemos los datos mínimos necesarios
    if not adapted["Pedido"].get("¿Quién proporciona el material?"):
        # Si no hay material, crear estructura básica para evitar errores
        adapted["Pedido"]["¿Quién proporciona el material?"] = {
            "proveedor": "Arkcutt",
            "Material seleccionado": "Contrachapado", 
            "Grosor": "4",
            "Color": "light-wood"
        }
    
    return adapted

class FormularioData(BaseModel):
    """Modelo para recibir datos del formulario frontend"""
    Cliente: Optional[Dict[str, Any]] = None
    Pedido: Optional[Dict[str, Any]] = None
    cliente: Optional[Dict[str, Any]] = None
    pedido: Optional[Dict[str, Any]] = None
    numero_solicitud: Optional[str] = None
    fecha_solicitud: Optional[str] = None
    analisis_backend: Optional[Dict[str, Any]] = None

class PresupuestoResponse(BaseModel):
    """Modelo de respuesta para el presupuesto calculado"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """Endpoint principal de bienvenida"""
    return {
        "message": "API Calculadora de Presupuestos Láser",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "/calculate": "POST - Calcular presupuesto desde JSON del formulario",
            "/calculate/pdf": "POST - Calcular y generar PDF del presupuesto",
            "/health": "GET - Estado de la API",
            "/docs": "GET - Documentación interactiva"
        }
    }

@app.get("/health")
async def health():
    """Verificar estado de la API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "materiales_disponibles": len(laser_agent.get_available_materials())
    }

@app.post("/calculate", response_model=PresupuestoResponse)
async def calculate_budget(formulario_data: FormularioData):
    """
    Calcular presupuesto basado en JSON del formulario frontend
    
    Recibe la estructura JSON completa del formulario y devuelve:
    - Presupuesto calculado
    - Desglose por capas
    - Parámetros de corte
    - Información del cliente
    """
    try:
        # Convertir a diccionario para usar con laser_agent
        data_dict = formulario_data.dict()
        print(f"[DEBUG] Datos recibidos del frontend: {data_dict}")
        
        # Adaptar formato del frontend al formato interno
        print(f"[DEBUG] Iniciando adaptación del formato...")
        adapted_data = adapt_frontend_format(data_dict)
        print(f"[DEBUG] Datos adaptados: {adapted_data}")
        
        # Calcular presupuesto usando el agente
        print(f"[DEBUG] Iniciando cálculo de presupuesto...")
        budget_result = laser_agent.calculate_budget_from_frontend(adapted_data)
        print(f"[DEBUG] Resultado del cálculo: {budget_result}")
        
        if 'error' in budget_result:
            return PresupuestoResponse(
                success=False,
                error=budget_result['error'],
                data=budget_result
            )
        
        return PresupuestoResponse(
            success=True,
            data=budget_result
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DEBUG] Error completo: {error_trace}")
        
        return PresupuestoResponse(
            success=False,
            error=f"Error procesando JSON del frontend: {str(e)}",
            data={
                "error": f"Error procesando JSON del frontend: {str(e)}",
                "materiales_disponibles": laser_agent.get_available_materials()
            }
        )

@app.post("/calculate/pdf")
async def calculate_budget_with_pdf(formulario_data: FormularioData):
    """
    Calcular presupuesto y generar PDF DIRECTO sin adaptador
    
    Usa los datos tal como vienen del frontend en formato correcto
    """
    try:
        # Convertir a diccionario
        data_dict = formulario_data.dict()
        print(f"[PDF] Datos recibidos: {data_dict}")
        
        # Verificar si ya tiene el formato correcto (Cliente, Pedido)
        if "Cliente" in data_dict and "Pedido" in data_dict:
            # Formato correcto - usar calculate_budget_from_job directamente
            budget_result = laser_agent.calculate_budget_from_job(data_dict)
        else:
            # Formato antiguo - usar con adaptador
            budget_result = laser_agent.calculate_budget_from_frontend(data_dict)
        
        print(f"[PDF] Resultado cálculo: {budget_result}")
        
        if 'error' in budget_result:
            raise HTTPException(
                status_code=400,
                detail=budget_result['error']
            )
        
        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            pdf_path = laser_agent.generate_pdf_quote(budget_result, temp_pdf.name)
            
            # Leer el contenido del PDF
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Limpiar archivo temporal
            os.unlink(pdf_path)
            
            # Generar nombre de archivo basado en número de solicitud
            numero_solicitud = data_dict.get('Pedido', {}).get('Número de solicitud', 'presupuesto')
            filename = f"presupuesto_{numero_solicitud}.pdf"
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[PDF] Error completo: {error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error generando PDF: {str(e)}"
        )

@app.get("/materiales")
async def get_available_materials():
    """
    Obtener lista de materiales disponibles
    
    Devuelve todos los materiales configurados en el sistema
    con sus especificaciones
    """
    try:
        materiales_lista = laser_agent.get_available_materials()
        materiales_detalle = []
        
        for material_config in laser_agent.config["materiales"]:
            materiales_detalle.append({
                "material": material_config["material"],
                "grosor": material_config["grosor"],
                "color": material_config["color"],
                "precio_plancha": material_config["precio_plancha"],
                "tamaño_plancha": material_config["tamaño_plancha"],
                "descripcion": f"{material_config['material']} {material_config['grosor']}mm {material_config['color']}"
            })
        
        return {
            "materiales": materiales_lista,
            "detalle": materiales_detalle,
            "total": len(materiales_lista)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo materiales: {str(e)}"
        )

@app.get("/config")
async def get_config():
    """
    Obtener configuración actual del sistema
    
    Devuelve la configuración de tarifas y parámetros
    """
    try:
        return {
            "tarifa_por_minuto": laser_agent.config["tarifa_por_minuto"],
            "margen_beneficio": laser_agent.config["margen_beneficio"],
            "total_materiales": len(laser_agent.config["materiales"])
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo configuración: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("Iniciando API Calculadora de Presupuestos Laser...")
    print(f"API disponible en: http://localhost:{port}")
    if not PRODUCTION:
        print(f"Documentacion disponible en: http://localhost:{port}/docs")
        uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
    else:
        uvicorn.run("api:app", host="0.0.0.0", port=port)