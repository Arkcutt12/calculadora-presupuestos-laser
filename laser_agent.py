import json
import os
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import unicodedata

# Configuración por defecto
DEFAULT_CONFIG = {
    "tarifa_por_minuto": 0.8,
    "margen_beneficio": 50,  # Porcentaje adicional
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
        },
        {
            "material": "MDF",
            "grosor": 6,
            "color": "Natural",
            "precio_plancha": 22.00,
            "tamaño_plancha": 1.44,
            "velocidad_corte": 800,
            "potencia_laser": 90,
            "fuerza_aire": 0.8
        },
        {
            "material": "Acrílico",
            "grosor": 3,
            "color": "Transparente",
            "precio_plancha": 25.00,
            "tamaño_plancha": 1.44,
            "velocidad_corte": 600,
            "potencia_laser": 70,
            "fuerza_aire": 0.6
        },
        {
            "material": "Acrílico",
            "grosor": 5,
            "color": "Transparente",
            "precio_plancha": 35.00,
            "tamaño_plancha": 1.44,
            "velocidad_corte": 400,
            "potencia_laser": 80,
            "fuerza_aire": 0.6
        },
        {
            "material": "Contrachapado",
            "grosor": 3,
            "color": "Natural",
            "precio_plancha": 18.00,
            "tamaño_plancha": 1.44,
            "velocidad_corte": 1000,
            "potencia_laser": 85,
            "fuerza_aire": 0.8
        }
    ]
}

class LaserCuttingAgent:
    def __init__(self, config_file: str = "laser_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo JSON o usa la configuración por defecto"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Crear archivo de configuración por defecto
                self.save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"⚠️  Error al cargar configuración: {e}")
            print("📝 Usando configuración por defecto...")
            return DEFAULT_CONFIG
    
    def save_config(self, config: Dict[str, Any]):
        """Guarda la configuración en archivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error al guardar configuración: {e}")
    
    def find_material(self, material: str, grosor: float, color: str) -> Optional[Dict[str, Any]]:
        """Busca un material específico en la configuración"""
        for mat in self.config["materiales"]:
            # Comparación con tolerancia para grosores decimales
            mismo_material = mat["material"].lower() == material.lower()
            mismo_color = mat["color"].lower() == color.lower()
            try:
                grosor_config = float(mat["grosor"])
            except (TypeError, ValueError):
                continue
            grosor_coincide = abs(grosor_config - float(grosor)) <= 0.05
            if mismo_material and grosor_coincide and mismo_color:
                return mat
        return None
    
    def calculate_cutting_time(self, longitud_vector: float, velocidad_corte_porcentaje: int) -> float:
        """Calcula el tiempo de corte en minutos"""
        # Convertir porcentaje a velocidad real (300mm/s = 100%)
        velocidad_mm_s = (velocidad_corte_porcentaje / 100) * 300
        # Convertir a mm/min
        velocidad_mm_min = velocidad_mm_s * 60
        # Convertir a m/min
        velocidad_m_min = velocidad_mm_min / 1000
        # Tiempo = distancia / velocidad
        tiempo_minutos = longitud_vector / velocidad_m_min
        return round(tiempo_minutos, 2)

    # ===== Soporte de capas =====
    def _resolve_process_params(self, material_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parámetros de proceso para corte/gravado con valores por defecto y override desde JSON."""
        process = {
            'cut': {
                'speed_pct': material_info.get('velocidad_corte') if isinstance(material_info.get('velocidad_corte'), (int, float)) else 25,
                'power_pct': material_info.get('potencia_laser', 90),
                'air_bar': material_info.get('fuerza_aire', 0.8),
                'overhead_factor': 1.05
            },
            'engrave': {
                'speed_pct': 60,  # Valor por defecto
                'power_pct': 30,  # Valor por defecto
                'air_bar': 0.4,   # Valor por defecto
                'hatch_spacing_mm': 0.25,  # Valor por defecto
                'fill_overhead_factor': 1.2  # Valor por defecto
            }
        }
        
        # Usar process_params si está disponible
        pp = material_info.get('process_params')
        if isinstance(pp, dict):
            for key in ('cut', 'engrave'):
                if key in pp and isinstance(pp[key], dict):
                    process[key].update(pp[key])
        
        return process

    def _speed_m_per_min(self, speed_pct: float) -> float:
        """Convierte % de velocidad (100% = 300 mm/s) a m/min."""
        velocidad_mm_s = (float(speed_pct) / 100.0) * 300.0
        return (velocidad_mm_s * 60.0) / 1000.0

    def calculate_layer_time_minutes(self, layer: Dict[str, Any], material_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula tiempo por capa.

        Tipos:
          - cut_outside, cut_inside (corte vectorial)
          - engrave_outline (grabado vectorial)
          - engrave_fill (grabado de relleno por hatch)
        Campos esperados:
          - length_m (outline)
          - area_m2 (fill) y hatch_spacing_mm opcional
        """
        process = self._resolve_process_params(material_info)
        layer_type = (layer.get('type') or '').lower()
        breakdown = {
            'name': layer.get('name', layer_type),
            'type': layer_type,
            'length_m': round(float(layer.get('length_m', 0) or 0), 4),
            'area_m2': round(float(layer.get('area_m2', 0) or 0), 4),
            'time_min': 0.0
        }

        if layer_type in ('cut_outside', 'cut_inside'):
            length_m = float(layer.get('length_m', 0) or 0)
            v_m_min = self._speed_m_per_min(process['cut']['speed_pct'])
            time_min = (length_m / v_m_min) * process['cut'].get('overhead_factor', 1.0) if v_m_min > 0 else 0
            breakdown['time_min'] = round(time_min, 3)
            return breakdown

        if layer_type == 'engrave_outline':
            length_m = float(layer.get('length_m', 0) or 0)
            v_m_min = self._speed_m_per_min(process['engrave']['speed_pct'])
            outline_overhead = 1.08
            time_min = (length_m / v_m_min) * outline_overhead if v_m_min > 0 else 0
            breakdown['time_min'] = round(time_min, 3)
            return breakdown

        if layer_type == 'engrave_fill':
            area_m2 = float(layer.get('area_m2', 0) or 0)
            spacing_mm = float(layer.get('hatch_spacing_mm') or process['engrave']['hatch_spacing_mm'] or 0.25)
            spacing_m = spacing_mm / 1000.0
            total_length_m = (area_m2 / spacing_m) if spacing_m > 0 else 0
            v_m_min = self._speed_m_per_min(process['engrave']['speed_pct'])
            time_min = (total_length_m / v_m_min) * process['engrave'].get('fill_overhead_factor', 1.2) if v_m_min > 0 else 0
            breakdown['length_m'] = round(total_length_m, 4)
            breakdown['time_min'] = round(time_min, 3)
            return breakdown

        return breakdown
    
    def calculate_material_cost(self, cantidad_m2: float, precio_plancha: float, tamaño_plancha: float) -> float:
        """Calcula el coste del material"""
        planchas_necesarias = cantidad_m2 / tamaño_plancha
        coste_material = planchas_necesarias * precio_plancha
        return round(coste_material, 2)
    
    def calculate_budget(self, longitud_vector: float, material: str, grosor: float, 
                        color: str, cantidad_material: float) -> Dict[str, Any]:
        """Calcula el presupuesto completo"""
        
        # Buscar material en la configuración
        material_info = self.find_material(material, grosor, color)
        
        if not material_info:
            return {
                'error': f'Material no encontrado: {material} {grosor}mm {color}',
                'materiales_disponibles': self.get_available_materials()
            }
        
        # Calcular tiempo de corte
        tiempo_corte = self.calculate_cutting_time(longitud_vector, material_info["velocidad_corte"])
        
        # Calcular costes
        coste_corte = tiempo_corte * self.config["tarifa_por_minuto"]
        coste_material = self.calculate_material_cost(
            cantidad_material, 
            material_info["precio_plancha"], 
            material_info["tamaño_plancha"]
        )
        
        # Calcular total
        subtotal = coste_corte + coste_material
        margen = subtotal * (self.config["margen_beneficio"] / 100)
        total = subtotal + margen
        
        return {
            'material': material_info,
            'tiempo_corte_minutos': tiempo_corte,
            'coste_corte': round(coste_corte, 2),
            'coste_material': coste_material,
            'subtotal': round(subtotal, 2),
            'margen_beneficio': round(margen, 2),
            'total': round(total, 2),
            'parametros_corte': {
                'velocidad': f"{material_info['velocidad_corte']}% ({round((material_info['velocidad_corte'] / 100) * 300, 1)} mm/s)",
                'potencia': f"{material_info['potencia_laser']}%",
                'fuerza_aire': f"{material_info['fuerza_aire']} bar"
            }
        }
    
    def get_available_materials(self) -> List[str]:
        """Obtiene lista de materiales disponibles"""
        materiales = []
        for mat in self.config["materiales"]:
            materiales.append(f"{mat['material']} {mat['grosor']}mm {mat['color']}")
        return materiales
    
    def format_budget(self, budget_data: Dict[str, Any]) -> str:
        """Formatea el presupuesto para mostrar"""
        if 'error' in budget_data:
            return f"❌ {budget_data['error']}\n\n📋 Materiales disponibles:\n" + \
                   "\n".join([f"  • {mat}" for mat in budget_data['materiales_disponibles']])
        
        # Parámetros (simple o por proceso)
        params_block = ""
        pc = budget_data.get('parametros_corte')
        if isinstance(pc, dict) and 'cut' in pc:
            cut_info = pc['cut']
            engrave_info = pc.get('engrave', {})
            params_block = (
                f"Corte - Velocidad: {cut_info.get('velocidad', 'N/A')} | Potencia: {cut_info.get('potencia', 'N/A')} | Aire: {cut_info.get('aire', 'N/A')}"
            )
            if engrave_info:
                engrave_line = f"Grabado - Velocidad: {engrave_info.get('velocidad', 'N/A')} | Potencia: {engrave_info.get('potencia', 'N/A')} | Aire: {engrave_info.get('aire', 'N/A')}"
                if 'hatch_spacing_mm' in engrave_info:
                    engrave_line += f" | Hatch: {engrave_info['hatch_spacing_mm']}"
                params_block += f"\n{engrave_line}"
        elif isinstance(pc, dict):
            params_block = (
                f"Velocidad: {pc.get('velocidad', 'N/A')} | Potencia láser: {pc.get('potencia', 'N/A')} | Fuerza aire: {pc.get('fuerza_aire', 'N/A')}"
            )
        else:
            params_block = "Parámetros no disponibles"

        # Desglose de capas
        layers_block = ""
        if budget_data.get('layers'):
            lines = []
            for l in budget_data['layers']:
                extra = []
                if l.get('length_m'):
                    extra.append(f"longitud: {l['length_m']} m")
                if l.get('area_m2'):
                    extra.append(f"área: {l['area_m2']} m²")
                extra_txt = (" | " + " | ".join(extra)) if extra else ""
                lines.append(f"  - {l.get('name') or l.get('type','')} | tiempo: {l['time_min']} min{extra_txt}")
            layers_block = "\nDesglose por capas:\n" + "\n".join(lines)

        return f"""
PRESUPUESTO CORTE LASER

Material: {budget_data['material']['material']} {budget_data['material']['grosor']}mm {budget_data['material']['color']}
Tiempo de corte: {budget_data['tiempo_corte_minutos']} minutos
Coste corte: {budget_data['coste_corte']} EUR
Coste material: {budget_data['coste_material']} EUR
Subtotal: {budget_data['subtotal']} EUR
Margen ({self.config['margen_beneficio']}%): {budget_data['margen_beneficio']} EUR
TOTAL: {budget_data['total']} EUR

Parametros de corte:
  - {params_block}
{layers_block}
        """.strip()

    def _extract_area_from_string(self, area_string: str) -> float:
        """Extrae el área en m² desde un string como '2 mm²' o similar"""
        try:
            if isinstance(area_string, (int, float)):
                return float(area_string)
            
            if not isinstance(area_string, str):
                return 0.0
                
            # Buscar patrón de números seguido de unidades (más flexible)
            import re
            # Buscar patrones como "2 mm²", "2.5 mm2", "0.5 m²", etc.
            match = re.search(r'([\d.,]+)\s*(mm.?²?|m.?²?)', area_string, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace(',', '.')
                valor = float(valor_str)
                unidad = match.group(2).lower()
                
                # Convertir mm² a m²
                if 'mm' in unidad:
                    return valor / 1_000_000  # mm² a m²
                else:  # m² o m2
                    return valor
                    
            return 0.0
        except Exception as e:
            print(f"DEBUG: Error extrayendo área de '{area_string}': {e}")
            return 0.0

    def _map_layer_name_to_type(self, layer_name: str) -> str:
        """Mapea nombres de capas DXF a tipos de operaciones láser"""
        layer_name = layer_name.lower().strip()
        
        # Mapeo de nombres de capas a tipos de operaciones
        if 'corte' in layer_name and 'exterior' in layer_name:
            return 'cut_outside'
        elif 'corte' in layer_name and 'interior' in layer_name:
            return 'cut_inside'
        elif 'material' in layer_name:
            return 'engrave_outline'
        elif 'marc' in layer_name or 'marco' in layer_name:
            return 'engrave_outline'
        elif 'grabado' in layer_name:
            return 'engrave_outline'
        else:
            # Por defecto, asumir corte
            return 'cut_outside'

    def _normalize_material_name(self, material: str) -> str:
        """Normaliza nombres de material para buscar en la configuración"""
        material_lower = material.lower().strip()
        
        # Mapear nombres del frontend a nombres en configuración
        material_mapping = {
            'contrachapado': 'Contrachapado',
            'mdf': 'MDF',
            'metacrilato': 'Metacrilato',
            'acrilico': 'Metacrilato',
            'dm': 'DM'
        }
        
        return material_mapping.get(material_lower, material)

    def _normalize_color_name(self, color: str) -> str:
        """Normaliza nombres de colores para buscar en la configuración"""
        color_lower = color.lower().strip()
        
        # Mapear colores del frontend a colores en configuración
        color_mapping = {
            'light-wood': 'light-wood',
            'dark-wood': 'dark-wood', 
            'madera-clara': 'light-wood',
            'madera-oscura': 'dark-wood',
            'natural': 'light-wood',
            'transparente': 'Transparente',
            'negro': 'Negro',
            'blanco': 'Blanco'
        }
        
        return color_mapping.get(color_lower, color.title())

    def calculate_budget_from_frontend(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula presupuesto basado en JSON del formulario frontend"""
        
        try:
            # Validación inicial
            if not frontend_data or not isinstance(frontend_data, dict):
                return {
                    'error': 'Datos del frontend vacíos o inválidos',
                    'materiales_disponibles': self.get_available_materials()
                }
            
            pedido = frontend_data.get('Pedido')
            if pedido is None:
                return {
                    'error': 'Sección Pedido no encontrada en los datos',
                    'materiales_disponibles': self.get_available_materials()
                }
            
            # Extraer información del material con validación robusta
            material_info_raw = pedido.get('¿Quién proporciona el material?')
            if material_info_raw is None:
                return {
                    'error': 'Información del material no encontrada',
                    'materiales_disponibles': self.get_available_materials()
                }
            
            # Validar que material_info_raw sea un diccionario
            if not isinstance(material_info_raw, dict):
                return {
                    'error': f'Formato de material inválido: {type(material_info_raw)}',
                    'materiales_disponibles': self.get_available_materials()
                }
            
            material_name = self._normalize_material_name(material_info_raw.get('Material seleccionado', ''))
            grosor_str = str(material_info_raw.get('Grosor', '')).replace('mm', '').strip()
            grosor = float(grosor_str) if grosor_str else 0
            color = self._normalize_color_name(material_info_raw.get('Color', ''))
            
            # Extraer área del material
            area_string = pedido.get('Area material', '0 mm²')
            material_area_m2 = self._extract_area_from_string(area_string)
            
            # Procesar capas DXF con validación
            capas_dxf = pedido.get('Capas', [])
            if not isinstance(capas_dxf, list):
                capas_dxf = []
                
            layers = []
            
            for capa in capas_dxf:
                if capa is None or not isinstance(capa, dict):
                    continue
                    
                layer_type = self._map_layer_name_to_type(capa.get('nombre', ''))
                longitud_m = capa.get('longitud_m', 0)
                
                # Asegurar que longitud_m sea un número
                try:
                    longitud_m = float(longitud_m) if longitud_m is not None else 0
                except (ValueError, TypeError):
                    longitud_m = 0
                
                layer = {
                    'name': str(capa.get('nombre', '')),
                    'type': layer_type,
                    'length_m': longitud_m
                }
                
                # Para grabado de relleno, necesitamos área
                if layer_type == 'engrave_fill':
                    layer['area_m2'] = material_area_m2
                    layer['hatch_spacing_mm'] = 0.25  # Valor por defecto
                
                layers.append(layer)
            
            # Crear estructura compatible con el sistema existente
            job_data = {
                'material': material_name,
                'grosor': grosor,
                'color': color,
                'material_area_m2': material_area_m2,
                'layers': layers,
                'cliente': frontend_data.get('Cliente', {}),
                'numero_solicitud': pedido.get('Número de solicitud', ''),
                'archivo_dxf': pedido.get('Archivo dxf', [])
            }
            
            # Usar el método existente para calcular el presupuesto
            budget_result = self.calculate_budget_from_job(job_data)
            
            # Añadir información adicional del frontend
            if 'error' not in budget_result:
                analisis_dxf = pedido.get('Análisis DXF', {})
                calidad_archivo = analisis_dxf.get('Calidad del archivo', {}) if isinstance(analisis_dxf, dict) else {}
                
                budget_result['frontend_info'] = {
                    'numero_solicitud': pedido.get('Número de solicitud', ''),
                    'cliente': frontend_data.get('Cliente', {}),
                    'longitud_total_mm': pedido.get('Longitud vector total', ''),
                    'calidad_archivo': calidad_archivo,
                    'recogida': pedido.get('Datos Recogida', {}),
                    'urgente': pedido.get('Solicitud urgente', False)
                }
            
            return budget_result
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Traceback completo en calculate_budget_from_frontend: {error_trace}")
            return {
                'error': f'Error procesando JSON del frontend: {str(e)}',
                'materiales_disponibles': self.get_available_materials()
            }

    def calculate_budget_from_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula presupuesto basado en un job con capas"""
        
        # Extraer datos del job
        material = job_data.get('material')
        grosor = job_data.get('grosor')
        color = job_data.get('color')
        material_area_m2 = job_data.get('material_area_m2', 0)
        layers = job_data.get('layers', [])
        
        # Buscar material en la configuración
        material_info = self.find_material(material, grosor, color)
        
        if not material_info:
            return {
                'error': f'Material no encontrado: {material} {grosor}mm {color}',
                'materiales_disponibles': self.get_available_materials()
            }
        
        # Calcular tiempo y coste por capa usando los nuevos métodos
        total_time = 0
        layers_with_time = []
        
        for layer in layers:
            layer_breakdown = self.calculate_layer_time_minutes(layer, material_info)
            layers_with_time.append(layer_breakdown)
            total_time += layer_breakdown['time_min']
        
        # Calcular costes
        coste_corte = total_time * self.config["tarifa_por_minuto"]
        coste_material = self.calculate_material_cost(
            material_area_m2, 
            material_info["precio_plancha"], 
            material_info["tamaño_plancha"]
        )
        
        # Calcular total
        subtotal = coste_corte + coste_material
        margen = subtotal * (self.config["margen_beneficio"] / 100)
        total = subtotal + margen
        
        # Preparar parámetros de proceso usando los parámetros resueltos
        resolved_params = self._resolve_process_params(material_info)
        process_params = {}
        
        for process_type, params in resolved_params.items():
            process_params[process_type] = {
                'velocidad': f"{params.get('speed_pct', 0)}% ({round((params.get('speed_pct', 0) / 100) * 300, 1)} mm/s)",
                'potencia': f"{params.get('power_pct', 0)}%",
                'aire': f"{params.get('air_bar', 0)} bar"
            }
            if process_type == 'engrave' and 'hatch_spacing_mm' in params:
                process_params[process_type]['hatch_spacing_mm'] = f"{params['hatch_spacing_mm']} mm"
        
        return {
            'material': material_info,
            'tiempo_corte_minutos': round(total_time, 2),
            'coste_corte': round(coste_corte, 2),
            'coste_material': coste_material,
            'subtotal': round(subtotal, 2),
            'margen_beneficio': round(margen, 2),
            'total': round(total, 2),
            'layers': layers_with_time,
            'parametros_corte': process_params
        }

    def generate_pdf_quote(self, budget_data: Dict[str, Any], output_path: str) -> str:
        """Genera un PDF con el presupuesto replicando exactamente el diseño de MAKOSITE"""
        if 'error' in budget_data:
            raise ValueError(budget_data['error'])

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=10)

        # Obtener datos del cliente y pedido
        cliente_info = budget_data.get('frontend_info', {}).get('Cliente', {})
        pedido_info = budget_data.get('frontend_info', {}).get('Pedido', {})
        numero_presupuesto = pedido_info.get('Número de solicitud', 'PRESUPUESTO')

        # Header - Logo y datos empresa (lado derecho)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "Asociación Junior Empresa MAKOSITE", 0, 1, "R")
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 5, "G72660145", 0, 1, "R")
        pdf.cell(0, 5, "Carrer Ciutat d'Asución 16", 0, 1, "R") 
        pdf.cell(0, 5, "Barcelona (08030), Barcelona, España", 0, 1, "R")
        pdf.ln(5)

        # Línea separadora
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Número de presupuesto y fechas
        pdf.set_font("Arial", "B", 14)
        pdf.cell(100, 8, f"PRESUPUESTO #{numero_presupuesto}", 0, 0, "L")
        
        pdf.set_font("Arial", size=10)
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        fecha_vencimiento = datetime.now().replace(day=datetime.now().day + 15).strftime("%d/%m/%Y")
        pdf.cell(0, 4, f"Fecha: {fecha_hoy}", 0, 1, "R")
        pdf.cell(0, 4, f"Vencimiento: {fecha_vencimiento}", 0, 1, "R")
        pdf.ln(5)

        # Datos del cliente
        cliente_nombre = cliente_info.get('Nombre y Apellidos', 'Cliente')
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, cliente_nombre, 0, 1, "L")
        pdf.set_font("Arial", size=10) 
        pdf.cell(100, 6, "España", 0, 0, "L")
        
        # Total destacado (lado derecho)
        pdf.set_font("Arial", "B", 18)
        total_euros = f"{budget_data['total']:.2f}€"
        pdf.cell(0, 6, f"Total {total_euros}", 0, 1, "R")
        pdf.ln(8)

        # Línea separadora
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Tabla de conceptos - Headers
        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 8, "CONCEPTO", 1, 0, "C")
        pdf.cell(20, 8, "PRECIO", 1, 0, "C") 
        pdf.cell(20, 8, "UNIDADES", 1, 0, "C")
        pdf.cell(25, 8, "SUBTOTAL", 1, 0, "C")
        pdf.cell(15, 8, "IVA", 1, 0, "C")
        pdf.cell(25, 8, "TOTAL", 1, 1, "C")

        pdf.set_font("Arial", size=9)

        # Servicio corte láser
        tiempo_corte = budget_data.get('tiempo_corte_minutos', 0)
        precio_minuto = budget_data.get('tarifa_por_minuto', 0.6)
        coste_corte = budget_data.get('coste_corte', 0)
        coste_corte_con_iva = coste_corte * 1.21

        pdf.cell(80, 6, "Servicio corte láser - Barcelona", 1, 0, "L")
        pdf.cell(20, 6, f"{precio_minuto:.2f}€", 1, 0, "C")
        pdf.cell(20, 6, str(int(tiempo_corte)), 1, 0, "C")
        pdf.cell(25, 6, f"{coste_corte:.2f}€", 1, 0, "C")
        pdf.cell(15, 6, "21%", 1, 0, "C")
        pdf.cell(25, 6, f"{coste_corte_con_iva:.2f}€", 1, 1, "C")

        pdf.cell(80, 4, "Aquí se presupuesta los minutos de corte láser", 1, 0, "L")
        pdf.cell(105, 4, "", 1, 1, "C")

        # Material (si hay coste de material)
        coste_material = budget_data.get('coste_material', 0)
        if coste_material > 0:
            material_info = budget_data.get('material', {})
            material_nombre = f"Tablero {material_info.get('material', 'Material')} {material_info.get('color', '')}"
            grosor_info = f"{material_info.get('grosor', '')}mm grosor"
            coste_material_con_iva = coste_material * 1.21
            
            # Calcular precio unitario asumiendo 1 unidad por ahora
            precio_unitario = coste_material
            unidades = 1
            
            pdf.cell(80, 6, material_nombre, 1, 0, "L")
            pdf.cell(20, 6, f"{precio_unitario:.2f}€", 1, 0, "C")
            pdf.cell(20, 6, str(unidades), 1, 0, "C")
            pdf.cell(25, 6, f"{coste_material:.2f}€", 1, 0, "C")
            pdf.cell(15, 6, "21%", 1, 0, "C")
            pdf.cell(25, 6, f"{coste_material_con_iva:.2f}€", 1, 1, "C")

            pdf.cell(80, 4, grosor_info, 1, 0, "L")
            pdf.cell(105, 4, "", 1, 1, "C")

        pdf.ln(5)

        # Resumen final
        subtotal_sin_iva = coste_corte + coste_material
        descuento = 0  # Por ahora sin descuento
        base_imponible = subtotal_sin_iva - descuento
        iva_total = base_imponible * 0.21
        total_final = base_imponible + iva_total

        pdf.set_font("Arial", "B", 10)
        if descuento > 0:
            pdf.cell(0, 6, f"DESCUENTO 10 %", 0, 0, "R")
            pdf.cell(25, 6, f"{descuento:.2f}€", 0, 1, "R")

        pdf.cell(0, 6, "BASE IMPONIBLE", 0, 0, "R")
        pdf.cell(25, 6, f"{base_imponible:.2f}€", 0, 1, "R")

        pdf.cell(0, 6, "IVA 21%", 0, 0, "R") 
        pdf.cell(25, 6, f"{iva_total:.2f}€", 0, 1, "R")

        pdf.cell(0, 8, "TOTAL", 0, 0, "R")
        pdf.cell(25, 8, f"{total_final:.2f}€", 0, 1, "R")

        # Footer con datos bancarios
        pdf.ln(10)
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, "Pagar por transferencia bancaria al siguiente número de cuenta: ES55 2100 0859 2102 0090 5852", 0, 1, "C")
        
        # Número de página
        pdf.set_y(-20)
        pdf.cell(0, 10, "1/1", 0, 0, "C")

        pdf.output(output_path)
        return output_path


def main():
    parser = argparse.ArgumentParser(description='Agente de Presupuestos de Corte Láser')
    parser.add_argument('--config', default='laser_config.json', help='Archivo de configuración JSON')
    parser.add_argument('--longitud', type=float, help='Longitud del vector en metros')
    parser.add_argument('--material', help='Material (ej: MDF, Acrílico)')
    parser.add_argument('--grosor', type=float, help='Grosor en mm')
    parser.add_argument('--color', help='Color del material')
    parser.add_argument('--cantidad', type=float, help='Cantidad de material en m²')
    parser.add_argument('--pdf', help='Ruta de salida para generar el PDF del presupuesto (ej: presupuesto.pdf)')
    parser.add_argument('--job', help='Ruta a JSON con definición de capas y material')
    parser.add_argument('--frontend', help='Ruta a JSON del formulario frontend')
    
    args = parser.parse_args()
    
    # Crear instancia del agente
    agent = LaserCuttingAgent(args.config)
    
    # Si se proporciona un JSON del formulario frontend
    if args.frontend:
        try:
            with open(args.frontend, 'r', encoding='utf-8') as ff:
                frontend_data = json.load(ff)
        except Exception as e:
            print(f"❌ No se pudo leer el JSON del frontend: {e}")
            return
        budget = agent.calculate_budget_from_frontend(frontend_data)
        print(agent.format_budget(budget))
        if args.pdf:
            try:
                path = agent.generate_pdf_quote(budget, args.pdf)
                print(f"📄 PDF generado: {path}")
            except Exception as e:
                print(f"❌ No se pudo generar el PDF: {e}")
        return
    
    # Si se proporciona un job con capas
    if args.job:
        try:
            with open(args.job, 'r', encoding='utf-8') as jf:
                job = json.load(jf)
        except Exception as e:
            print(f"❌ No se pudo leer el job JSON: {e}")
            return
        budget = agent.calculate_budget_from_job(job)
        print(agent.format_budget(budget))
        if args.pdf:
            try:
                path = agent.generate_pdf_quote(budget, args.pdf)
                print(f"📄 PDF generado: {path}")
            except Exception as e:
                print(f"❌ No se pudo generar el PDF: {e}")
        return

    # Si no se proporcionan argumentos, usar modo interactivo
    if not all([args.longitud, args.material, args.grosor, args.color, args.cantidad]):
        print("🔪 AGENTE DE PRESUPUESTOS DE CORTE LÁSER 🔪")
        print("Escribe 'salir' para terminar")
        print("Escribe 'materiales' para ver materiales disponibles")
        print("-" * 50)
        
        while True:
            try:
                print("\n📋 Ingresa los datos del trabajo:")
                longitud = input("📏 Longitud del vector (metros): ").strip()
                
                if longitud.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if longitud.lower() == 'materiales':
                    print("\n📦 Materiales disponibles:")
                    for mat in agent.get_available_materials():
                        print(f"  • {mat}")
                    continue
                
                if not longitud:
                    print("❌ Por favor, ingresa la longitud del vector")
                    continue
                
                try:
                    longitud = float(longitud)
                except ValueError:
                    print("❌ La longitud debe ser un número")
                    continue
                
                material = input("🏷️  Material: ").strip()
                grosor = input("📏 Grosor (mm): ").strip()
                color = input("🎨 Color: ").strip()
                cantidad = input("📦 Cantidad material (m²): ").strip()
                
                try:
                    grosor = float(grosor)
                    cantidad = float(cantidad)
                except ValueError:
                    print("❌ Grosor y cantidad deben ser números")
                    continue
                
                print("\n🔍 Calculando presupuesto...")
                budget = agent.calculate_budget(longitud, material, grosor, color, cantidad)
                print(agent.format_budget(budget))
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
    else:
        # Modo directo con argumentos
        print(f"🔍 Calculando presupuesto para {args.material}...")
        budget = agent.calculate_budget(args.longitud, args.material, args.grosor, args.color, args.cantidad)
        print(agent.format_budget(budget))
        if args.pdf:
            try:
                path = agent.generate_pdf_quote(budget, args.pdf)
                print(f"📄 PDF generado: {path}")
            except Exception as e:
                print(f"❌ No se pudo generar el PDF: {e}")

if __name__ == "__main__":
    main()
