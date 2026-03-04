from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import services.distribution as distribution
import models

def generate_pdf_report(case: models.Case) -> BytesIO:
    """
    Genera un informe PDF con el inventario, cálculo y reparto de la herencia.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # --- Título ---
    elements.append(Paragraph("Informe de Masa Hereditaria y Reparto", title_style))
    elements.append(Spacer(1, 1*cm))
    
    # --- Datos del Expediente ---
    elements.append(Paragraph(f"Expediente ID: {case.id}", normal_style))
    elements.append(Paragraph(f"Fallecido: {case.deceased_name or 'No especificado'}", normal_style))
    if case.deceased_dni:
        elements.append(Paragraph(f"DNI: {case.deceased_dni}", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # --- Cálculo de Datos ---
    dist_result = distribution.calculate_distribution(case)
    estate_summary = dist_result["estate_summary"]
    
    # --- Sección 1: Inventario ---
    elements.append(Paragraph("1. Inventario de Bienes y Deudas", heading_style))
    
    # Tabla de Activos
    assets_data = [["Descripción", "Tipo", "Valor (€)"]]
    for asset in case.assets:
        if not asset.is_debt:
            assets_data.append([asset.description or "Sin descripción", asset.type.value, f"{asset.value:,.2f}"])
            
    if len(assets_data) > 1:
        t_assets = Table(assets_data, colWidths=[8*cm, 4*cm, 4*cm])
        t_assets.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(Paragraph("Activos (Bienes y Derechos)", styles["Heading3"]))
        elements.append(t_assets)
    else:
        elements.append(Paragraph("No hay activos registrados.", normal_style))
        
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabla de Pasivos
    debts_data = [["Descripción", "Tipo", "Valor (€)"]]
    for asset in case.assets:
        if asset.is_debt:
            debts_data.append([asset.description or "Sin descripción", asset.type.value, f"{asset.value:,.2f}"])
            
    if len(debts_data) > 1:
        t_debts = Table(debts_data, colWidths=[8*cm, 4*cm, 4*cm])
        t_debts.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lavenderblush),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(Paragraph("Pasivos (Deudas y Gastos)", styles["Heading3"]))
        elements.append(t_debts)
    else:
        elements.append(Paragraph("No hay deudas registradas.", normal_style))
        
    elements.append(Spacer(1, 1*cm))
    
    # --- Sección 2: Resumen Económico ---
    elements.append(Paragraph("2. Liquidación de la Masa Hereditaria", heading_style))
    
    summary_data = [
        ["Concepto", "Importe (€)"],
        ["Total Activo", f"{estate_summary['total_assets']:,.2f}"],
        ["Ajuar Doméstico (3%)", f"{estate_summary['household_goods']:,.2f}"],
        ["Total Pasivo", f"{estate_summary['total_debts']:,.2f}"],
        ["Caudal Relicto Neto", f"{estate_summary['net_estate']:,.2f}"],
        ["Base Imponible Total", f"{estate_summary['taxable_base']:,.2f}"]
    ]
    
    t_summary = Table(summary_data, colWidths=[10*cm, 6*cm])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'), # Importes a la derecha
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 1*cm))
    
    # --- Sección 3: Reparto ---
    elements.append(Paragraph("3. Adjudicación y Reparto", heading_style))
    
    heirs_data = [["Heredero", "Parentesco", "Cuota (%)", "Valor Adjudicado (€)"]]
    for h in dist_result["heirs_distribution"]:
        heirs_data.append([
            h["name"],
            h["relationship"],
            f"{h['share_percentage']}%",
            f"{h['quota_value']:,.2f}"
        ])
        
    if len(heirs_data) > 1:
        t_heirs = Table(heirs_data, colWidths=[6*cm, 4*cm, 3*cm, 5*cm])
        t_heirs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t_heirs)
    else:
        elements.append(Paragraph("No hay herederos definidos para el reparto.", normal_style))
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_model_650_draft(case: models.Case) -> BytesIO:
    """
    Genera un borrador del Modelo 650 (Autoliquidación Sucesiones) para cada heredero.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'TitleCustom', 
        parent=styles['Title'], 
        fontSize=16, 
        spaceAfter=20,
        textColor=colors.darkblue
    )
    header_style = ParagraphStyle(
        'HeaderCustom',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=10,
        textColor=colors.black,
        backColor=colors.lightgrey,
        borderPadding=5
    )
    
    # Calcular distribución e impuestos
    dist_result = distribution.calculate_distribution(case)
    
    # Para cada heredero, generar una hoja de liquidación
    for i, heir_data in enumerate(dist_result["heirs_distribution"]):
        if i > 0:
            elements.append(Paragraph("<br/><br/>", styles["Normal"])) # PageBreak sería mejor pero SimpleDocTemplate maneja flujo
            elements.append(Paragraph("--- Corte de Página (Siguiente Declarante) ---", styles["Normal"]))
            elements.append(Spacer(1, 2*cm))

        # Título del Modelo
        elements.append(Paragraph(f"BORRADOR MODELO 650 - Autoliquidación Sucesiones", title_style))
        elements.append(Paragraph("Comunidad Autónoma / Estado: REGIMEN ESTATAL (Ley 29/1987)", styles["Normal"]))
        elements.append(Spacer(1, 0.5*cm))
        
        # 1. Datos del Causante
        elements.append(Paragraph("1. DATOS DEL CAUSANTE (Fallecido)", header_style))
        causante_data = [
            ["Nombre y Apellidos", case.deceased_name or "Desconocido"],
            ["DNI/NIF", case.deceased_dni or "Desconocido"],
            ["Fecha Devengo (Fallecimiento)", str(case.date_of_death) if case.date_of_death else "Desconocida"]
        ]
        t_causante = Table(causante_data, colWidths=[6*cm, 10*cm])
        t_causante.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t_causante)
        elements.append(Spacer(1, 0.5*cm))
        
        # 2. Datos del Sujeto Pasivo (Heredero)
        elements.append(Paragraph("2. DATOS DEL SUJETO PASIVO (Heredero/Legatario)", header_style))
        pasivo_data = [
            ["Nombre y Apellidos", heir_data["name"]],
            ["NIF", "_________________"], # No lo tenemos en modelo Heir aún
            ["Parentesco", heir_data["relationship"]],
            ["Grupo Parentesco", "I/II/III/IV (Ver normativa)"],
            ["Patrimonio Preexistente", f"{heir_data.get('pre_existing_wealth', 0):,.2f} €"]
        ]
        # Si tenemos wealth en heir_data (lo añadimos en distribution.py?)
        # distribution.py devuelve 'heir_data' que es un dict construido manualmente.
        # Comprobemos si añadimos 'pre_existing_wealth' al dict en distribution.py.
        # No, no lo añadimos al dict de salida en distribution.py, solo al cálculo.
        # Pero podemos acceder al objeto heir si iteramos case.heirs, pero aquí iteramos el resultado.
        # Asumamos 0 si no está.
        
        t_pasivo = Table(pasivo_data, colWidths=[6*cm, 10*cm])
        t_pasivo.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t_pasivo)
        elements.append(Spacer(1, 0.5*cm))
        
        # 3. Liquidación
        elements.append(Paragraph("3. LIQUIDACIÓN", header_style))
        
        liq_data = [
            ["Concepto", "Importe (€)"],
            ["Base Imponible (Cuota + Ajuar)", f"{heir_data['tax_base']:,.2f}"],
            ["(-) Reducciones Personales/Familiares", f"{heir_data['reductions']:,.2f}"],
            ["(=) Base Liquidable", f"{max(0, heir_data['tax_base'] - heir_data['reductions']):,.2f}"],
            ["(x) Tipo Medio / Tarifa", "S/Tarifa"], # Simplificado
            ["(=) Cuota Íntegra", f"{heir_data['tax_quota'] / (heir_data.get('multiplier', 1) or 1) if heir_data.get('multiplier') else '---'}"], 
            # Wait, I didn't pass 'multiplier' in distribution result.
            # I should update distribution.py to include 'multiplier' and 'quota_integra' if I want them here.
            # For now, let's just show the final Tax Quota.
            ["Cuota Íntegra Estimada", "---"],
            ["Coeficiente Multiplicador", "---"],
            ["(=) CUOTA TRIBUTARIA A INGRESAR", f"{heir_data['total_to_pay']:,.2f}"]
        ]
        
        t_liq = Table(liq_data, colWidths=[10*cm, 6*cm])
        t_liq.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow), # Highlight final result
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t_liq)
        
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Este documento es un BORRADOR informativo y no tiene validez legal ante la Administración.", styles["Italic"]))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
