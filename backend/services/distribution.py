from typing import List, Dict, Any
import models
import services.calculator as calculator

def calculate_distribution(case: models.Case) -> Dict[str, Any]:
    """
    Calcula el reparto de la herencia entre los herederos basándose en sus porcentajes.
    """
    # 1. Obtener datos de la masa hereditaria
    estate_data = calculator.calculate_estate(case)
    net_estate = estate_data["net_estate"]
    household_goods = estate_data["household_goods"]
    
    distribution_result = {
        "estate_summary": estate_data,
        "heirs_distribution": []
    }
    
    # 2. Calcular cuota para cada heredero
    total_distributed = 0.0
    
    for heir in case.heirs:
        # Porcentaje de participación (defecto 0 si no está definido)
        share = heir.share_percentage or 0.0
        
        # Valor de la cuota (Caudal Relicto)
        quota_value = (net_estate * share) / 100.0
        
        # Valor Ajuar proporcional
        ajuar_value = (household_goods * share) / 100.0
        
        # Base Imponible (Cuota + Ajuar)
        tax_base = quota_value + ajuar_value
        
        # Calcular Impuesto
        tax_calc = calculator.calculate_tax_for_heir(
            tax_base, 
            heir.relationship_degree, 
            heir.pre_existing_wealth or 0.0
        )
        
        heir_data = {
            "heir_id": heir.id,
            "name": heir.name,
            "relationship": heir.relationship_degree,
            "share_percentage": share,
            "quota_value": round(quota_value, 2),
            "tax_base": round(tax_base, 2),
            "pre_existing_wealth": heir.pre_existing_wealth or 0.0,
            "reductions": tax_calc["reductions"],
            "tax_quota": tax_calc["tax_quota"],
            "total_to_pay": tax_calc["tax_quota"] # En este modelo simplificado, Total = Cuota
        }
        
        distribution_result["heirs_distribution"].append(heir_data)
        total_distributed += quota_value
        
    distribution_result["total_distributed"] = round(total_distributed, 2)
    distribution_result["remainder"] = round(net_estate - total_distributed, 2)
    
    return distribution_result
