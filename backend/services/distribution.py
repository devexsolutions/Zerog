from typing import List, Dict, Any
import models
import services.calculator as calculator

def calculate_distribution(case: models.Case) -> Dict[str, Any]:
    """
    Calcula el reparto de la herencia entre los herederos basándose en sus porcentajes.
    Aplica gananciales, reducciones por parentesco y grupo, patrimonio preexistente y CCAA.
    """
    # 1. Obtener datos de la masa hereditaria (ya con gananciales aplicados)
    estate_data = calculator.calculate_estate(case)
    net_estate = estate_data["net_estate"]
    household_goods = estate_data["household_goods"]

    distribution_result = {
        "estate_summary": estate_data,
        "heirs_distribution": []
    }

    total_distributed = 0.0

    for heir in case.heirs:
        share = heir.share_percentage or 0.0

        # Valor de la cuota del caudal relicto neto
        quota_value = (net_estate * share) / 100.0

        # Ajuar proporcional
        ajuar_value = (household_goods * share) / 100.0

        # Base Imponible individual = Cuota + Ajuar
        tax_base = quota_value + ajuar_value

        # Calcular impuesto con todos los parámetros disponibles
        tax_calc = calculator.calculate_tax_for_heir(
            base_imponible=tax_base,
            relationship=heir.relationship_degree,
            pre_existing_wealth=heir.pre_existing_wealth or 0.0,
            age=heir.age,
            fiscal_residence=heir.fiscal_residence,
        )

        heir_data = {
            "heir_id": heir.id,
            "name": heir.name,
            "relationship": heir.relationship_degree or "",
            "share_percentage": share,
            "quota_value": round(quota_value, 2),
            "tax_base": round(tax_base, 2),
            "pre_existing_wealth": heir.pre_existing_wealth or 0.0,
            "reductions": tax_calc["reductions"],
            "quota_integra": tax_calc["quota_integra"],
            "multiplier": tax_calc["multiplier"],
            "tax_quota": tax_calc["tax_quota"],
            "total_to_pay": tax_calc["tax_quota"],
        }

        distribution_result["heirs_distribution"].append(heir_data)
        total_distributed += quota_value

    distribution_result["total_distributed"] = round(total_distributed, 2)
    distribution_result["remainder"] = round(net_estate - total_distributed, 2)

    return distribution_result
