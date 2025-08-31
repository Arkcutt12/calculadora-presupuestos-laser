#!/usr/bin/env python3

import csv
import json
import re

def parse_price(price_str):
    """Convierte precio del CSV (ej: '4,80 €') a float"""
    # Quitar simbolo euro y espacios, reemplazar coma por punto
    clean_price = price_str.replace('EUR', '').replace(' ', '').replace(',', '.')
    # Quitar el simbolo euro si existe
    import re
    clean_price = re.sub(r'[€€]', '', clean_price)
    return float(clean_price)

def parse_dimensions(dim_str):
    """Convierte dimensiones del CSV (ej: '60x100') a área en m²"""
    parts = dim_str.split('x')
    if len(parts) == 2:
        ancho_cm = int(parts[0])
        alto_cm = int(parts[1])
        # Convertir a mm y calcular área en m²
        ancho_mm = ancho_cm * 10
        alto_mm = alto_cm * 10
        area_m2 = (ancho_mm * alto_mm) / 1000000
        return area_m2, ancho_mm, alto_mm
    return 0.6, 600, 1000  # Default

def parse_thickness(thickness_str):
    """Convierte grosor del CSV (ej: '2.5mm') a float"""
    return float(thickness_str.replace('mm', ''))

def normalize_material_name(material_name):
    """Normaliza nombres de materiales"""
    material_name = material_name.upper()
    if 'METACRILATO' in material_name and any(color in material_name for color in ['LILA', 'AZUL', 'BLANCO']):
        return 'Metacrilato'
    elif 'METACRILATO' in material_name:
        return 'Metacrilato'
    elif 'CONTRACHAPADO' in material_name:
        return 'Contrachapado'
    elif 'MADERA BALSA' in material_name:
        return 'Madera Balsa'
    elif 'CARTÓN' in material_name:
        return 'Cartón'
    else:
        return material_name.title()

def extract_color(material_name, color_column):
    """Extrae el color correcto del material"""
    color_column = color_column.strip()
    if color_column == 'Lila':
        return 'Lila'
    elif color_column == 'Azul':
        return 'Azul'
    elif color_column == 'Blanco':
        return 'Blanco'
    elif color_column == 'Transparente':
        return 'Transparente'
    elif color_column == 'Gris':
        return 'Gris'
    elif color_column == 'Madera clara':
        return 'light-wood'
    elif color_column == 'Madera Natural':
        return 'natural'
    else:
        return color_column

# Leer CSV y convertir
csv_path = r"C:\Users\hiero\Downloads\Hoja de cálculo sin título - Hoja 1 (2).csv"
materiales = []

with open(csv_path, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        try:
            # Parsear datos
            precio = parse_price(row['PRECIO POR PLANCHA'])
            area_m2, ancho_mm, alto_mm = parse_dimensions(row['MEDIDA PLANCHA'])
            grosor = parse_thickness(row['GROSORES'])
            material = normalize_material_name(row['MATERIALES'])
            color = extract_color(row['MATERIALES'], row['COLOR'])
            
            # Crear entrada JSON
            material_entry = {
                "material": material,
                "grosor": grosor,
                "color": color,
                "precio_plancha": precio,
                "tamaño_plancha": area_m2,
                "dimensiones_plancha_mm": {
                    "ancho": ancho_mm,
                    "alto": alto_mm
                },
                "velocidad_corte": int(row['VELOCIDAD CORTE']),
                "potencia_laser": int(row['POTENCIA CORTE']),
                "fuerza_aire": 0.8,  # Valor por defecto
                "process_params": {
                    "cut": {
                        "speed_pct": int(row['VELOCIDAD CORTE']),
                        "power_pct": int(row['POTENCIA CORTE']),
                        "air_bar": 0.8
                    },
                    "engrave": {
                        "speed_pct": int(row['VELOCIDAD GRABADO']),
                        "power_pct": int(row['POTENCIA GRABADO']),
                        "air_bar": 0.6,
                        "hatch_spacing_mm": 0.25,
                        "fill_overhead_factor": 1.2
                    }
                }
            }
            
            materiales.append(material_entry)
            print(f"Procesado: {material} {grosor}mm {color} - {precio} EUR")
            
        except Exception as e:
            print(f"Error procesando fila: {row}")
            print(f"Error: {e}")

# Crear JSON final con estructura laser_config
laser_config = {
    "tarifa_por_minuto": 0.8,
    "margen_beneficio": 50,
    "materiales": materiales
}

# Guardar JSON
output_path = "C:\\Users\\hiero\\Desktop\\Aprender\\laser_config_nuevo.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(laser_config, f, indent=2, ensure_ascii=False)

print(f"JSON generado exitosamente: {output_path}")
print(f"Total de materiales procesados: {len(materiales)}")