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

class FormularioData(BaseModel):
    """Modelo para recibir datos del formulario frontend"""
    Cliente: Dict[str, Any]
    Pedido: Dict[str, Any]

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
        
        # Calcular presupuesto usando el agente
        budget_result = laser_agent.calculate_budget_from_frontend(data_dict)
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Error interno calculando presupuesto: {str(e)}"
        )

@app.post("/calculate/pdf")
async def calculate_budget_with_pdf(formulario_data: FormularioData):
    """
    Calcular presupuesto y generar PDF
    
    Similar a /calculate pero además genera un PDF del presupuesto
    y lo devuelve como descarga
    """
    try:
        # Convertir a diccionario para usar con laser_agent
        data_dict = formulario_data.dict()
        
        # Calcular presupuesto
        budget_result = laser_agent.calculate_budget_from_frontend(data_dict)
        
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
            numero_solicitud = budget_result.get('frontend_info', {}).get('numero_solicitud', 'presupuesto')
            filename = f"presupuesto_{numero_solicitud}.pdf"
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except Exception as e:
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