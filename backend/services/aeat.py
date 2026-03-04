import xml.etree.ElementTree as ET
from io import BytesIO
import models
import services.distribution as distribution

def generate_model_650_xml(case: models.Case) -> BytesIO:
    """
    Genera un archivo XML con los datos del Modelo 650 para importación o referencia.
    Estructura simplificada basada en los datos requeridos por la AEAT.
    """
    root = ET.Element("DeclaracionModelo650")
    
    # 1. Datos del Causante
    causante = ET.SubElement(root, "Causante")
    ET.SubElement(causante, "Nombre").text = case.deceased_name or "Desconocido"
    ET.SubElement(causante, "DNI").text = case.deceased_dni or ""
    ET.SubElement(causante, "FechaDevengo").text = str(case.date_of_death) if case.date_of_death else ""
    
    # 2. Bienes y Derechos (Inventario)
    bienes = ET.SubElement(root, "BienesYDerechos")
    for asset in case.assets:
        bien = ET.SubElement(bienes, "Bien")
        ET.SubElement(bien, "Descripcion").text = asset.description or "Sin descripción"
        ET.SubElement(bien, "Tipo").text = asset.type
        ET.SubElement(bien, "Valor").text = f"{asset.value:.2f}"
        ET.SubElement(bien, "Clave").text = "DEUDA" if asset.is_debt else "ACTIVO"
        if asset.cadastral_reference:
            ET.SubElement(bien, "ReferenciaCatastral").text = asset.cadastral_reference

    # 3. Sujetos Pasivos (Herederos) y Liquidación
    dist_result = distribution.calculate_distribution(case)
    sujetos = ET.SubElement(root, "SujetosPasivos")
    
    for heir_data in dist_result["heirs_distribution"]:
        sujeto = ET.SubElement(sujetos, "SujetoPasivo")
        
        # Datos Personales
        datos = ET.SubElement(sujeto, "DatosPersonales")
        ET.SubElement(datos, "Nombre").text = heir_data["name"]
        ET.SubElement(datos, "Parentesco").text = heir_data["relationship"]
        ET.SubElement(datos, "PatrimonioPreexistente").text = f"{heir_data.get('pre_existing_wealth', 0):.2f}"
        
        # Liquidación
        liq = ET.SubElement(sujeto, "Liquidacion")
        ET.SubElement(liq, "BaseImponible").text = f"{heir_data['tax_base']:.2f}"
        ET.SubElement(liq, "Reducciones").text = f"{heir_data['reductions']:.2f}"
        ET.SubElement(liq, "BaseLiquidable").text = f"{max(0, heir_data['tax_base'] - heir_data['reductions']):.2f}"
        ET.SubElement(liq, "CuotaTributaria").text = f"{heir_data['total_to_pay']:.2f}"

    # Generar XML string
    tree = ET.ElementTree(root)
    buffer = BytesIO()
    tree.write(buffer, encoding="utf-8", xml_declaration=True)
    buffer.seek(0)
    
    return buffer
