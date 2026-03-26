from typing import List, Dict, Any
import models

# CCAA con bonificaciones significativas (simplificado MVP)
# En producción, cada CCAA tiene su propia tabla
CCAA_BONIFICACIONES = {
    "Madrid": 0.99,        # 99% bonificación -> efectivamente pagan 1%
    "Canarias": 0.99,
    "Andalucia": 0.99,
    "Murcia": 0.99,
    "Extremadura": 0.99,
    "La Rioja": 0.98,
    "Cantabria": 0.90,
    "Baleares": 0.50,
    "Aragon": 0.65,
    "Cataluna": 0.0,       # Sin bonificación, tarifa propia
    "Valencia": 0.0,
    "Galicia": 0.0,
    "Asturias": 0.0,
    "Castilla Leon": 0.0,
    "Castilla La Mancha": 0.0,
    "Navarra": 0.0,        # Régimen foral propio
    "Pais Vasco": 0.0,     # Régimen foral propio
    "Estado": 0.0,         # Normativa estatal
}

def calculate_estate(case: models.Case) -> Dict[str, Any]:
    """
    Calcula la masa hereditaria, ajuar y caudal relicto.
    - Bienes gananciales: solo el 50% pertenece al caudal del fallecido.
    - Ajuar doméstico: 3% del activo bruto (LISD Art. 15).
    - Gastos deducibles: deudas + gastos de sepelio.
    """
    total_assets = 0.0
    total_debts = 0.0
    ganancial_deduction = 0.0

    for asset in case.assets:
        if asset.is_debt or asset.is_funeral_expense:
            total_debts += asset.value
        else:
            asset_value = asset.value
            # Bienes gananciales: solo el 50% forma parte del caudal relicto
            if asset.is_ganancial:
                effective_value = asset_value * 0.5
                ganancial_deduction += asset_value - effective_value
                total_assets += effective_value
            else:
                total_assets += asset_value

    # Ajuar Doméstico (3% del valor de activos que entran en masa)
    household_goods = total_assets * 0.03

    # Caudal Relicto Neto (Activos - Deudas)
    net_estate = total_assets - total_debts

    # Base Imponible (Neto + Ajuar)
    taxable_base = net_estate + household_goods

    return {
        "total_assets": round(total_assets, 2),
        "total_debts": round(total_debts, 2),
        "net_estate": round(net_estate, 2),
        "household_goods": round(household_goods, 2),
        "taxable_base": round(taxable_base, 2),
        "ganancial_deduction": round(ganancial_deduction, 2),
    }


def calculate_tax_for_heir(
    base_imponible: float,
    relationship: str,
    pre_existing_wealth: float,
    age: int = None,
    fiscal_residence: str = None
) -> Dict[str, float]:
    """
    Calcula la Cuota Tributaria según normativa (Ley 29/1987).
    Considera grupos de parentesco, edad, patrimonio preexistente y CCAA.
    """
    rel = relationship.lower() if relationship else ""

    # --- 1. Determinar Grupo de Parentesco (LISD Art. 20) ---
    # Grupo I: Descendientes < 21 años
    # Grupo II: Descendientes >= 21, cónyuge, ascendientes
    # Grupo III: Colaterales 2º y 3º grado, ascendientes/descendientes por afinidad
    # Grupo IV: Colaterales 4º grado, extraños
    group = _get_parentesco_group(rel, age)

    # --- 2. Reducción Personal (LISD Art. 20) ---
    reductions = _get_reduccion_personal(group, age)

    liquidable_base = max(0, base_imponible - reductions)

    # --- 3. Tarifa Progresiva Estatal (LISD Art. 21) ---
    quota_integra = calculate_tariff(liquidable_base)

    # --- 4. Coeficiente Multiplicador por Patrimonio Preexistente (LISD Art. 22) ---
    multiplier = get_multiplier(pre_existing_wealth, group)

    tax_quota = quota_integra * multiplier

    # --- 5. Bonificación Autonómica (si aplica) ---
    bonificacion = 0.0
    if fiscal_residence and fiscal_residence in CCAA_BONIFICACIONES:
        bonif_rate = CCAA_BONIFICACIONES[fiscal_residence]
        if bonif_rate > 0:
            bonificacion = tax_quota * bonif_rate
            tax_quota = tax_quota * (1 - bonif_rate)

    return {
        "group": group,
        "reductions": round(reductions, 2),
        "liquidable_base": round(liquidable_base, 2),
        "quota_integra": round(quota_integra, 2),
        "multiplier": round(multiplier, 4),
        "bonificacion": round(bonificacion, 2),
        "tax_quota": round(tax_quota, 2),
    }


def _get_parentesco_group(rel: str, age: int = None) -> int:
    """Determina el grupo de parentesco LISD."""
    # Descendientes directos
    if rel in ["child", "hijo", "son", "daughter", "hija",
               "grandchild", "nieto", "nieta", "grandson", "granddaughter"]:
        # Grupo I si menor de 21 años
        if age is not None and age < 21:
            return 1
        return 2  # Grupo II si >= 21

    # Cónyuge y ascendientes
    if rel in ["spouse", "conyuge", "husband", "wife", "esposo", "esposa",
               "parent", "padre", "madre", "father", "mother",
               "abuelo", "abuela", "grandfather", "grandmother"]:
        return 2

    # Colaterales 2º y 3º grado, y afinidad
    if rel in ["sibling", "hermano", "hermana", "brother", "sister",
               "uncle", "aunt", "tio", "tia",
               "nephew", "niece", "sobrino", "sobrina",
               "cuñado", "cuñada", "suegro", "suegra",
               "yerno", "nuera", "hijastro", "hijastra"]:
        return 3

    # Resto (colaterales 4º grado o extraños)
    return 4


def _get_reduccion_personal(group: int, age: int = None) -> float:
    """Reducciones personales LISD Art. 20 (normativa estatal 2024)."""
    if group == 1:
        # Grupo I: 15.956,87 € + 3.990,72 € por cada año < 21
        base = 15956.87
        if age is not None and age < 21:
            extra = (21 - age) * 3990.72
            return min(base + extra, 47858.59)  # Límite máximo Grupo I
        return base
    elif group == 2:
        return 15956.87
    elif group == 3:
        return 7993.46
    else:  # Grupo IV
        return 0.0


def calculate_tariff(base: float) -> float:
    """Tarifa estatal progresiva LISD Art. 21."""
    if base <= 0:
        return 0.0

    brackets = [
        (0,          0,         0.0765),
        (7993.46,    611.50,    0.0850),
        (15980.91,   1290.43,   0.0935),
        (23968.36,   2037.26,   0.1020),
        (31955.81,   2852.98,   0.1105),
        (39943.26,   3735.65,   0.1190),
        (47930.72,   4686.22,   0.1275),
        (55918.17,   5704.77,   0.1360),
        (63905.62,   6791.30,   0.1445),
        (71893.07,   7946.06,   0.1530),
        (79880.52,   9168.99,   0.1615),
        (119757.67,  15609.63,  0.1870),
        (159634.83,  23067.81,  0.2125),
        (239389.13,  40011.04,  0.2550),
        (398777.54,  80655.08,  0.2975),
        (797555.08,  199291.40, 0.3400),
    ]

    for i in range(len(brackets) - 1, -1, -1):
        limit, base_cuota, percent = brackets[i]
        if base >= limit:
            return base_cuota + (base - limit) * percent

    return base * 0.0765


def get_multiplier(wealth: float, group: int) -> float:
    """Coeficiente multiplicador LISD Art. 22."""
    if wealth <= 402678.11:
        if group <= 2:  return 1.0000
        if group == 3:  return 1.5882
        return 2.0000
    elif wealth <= 2007380.43:
        if group <= 2:  return 1.0500
        if group == 3:  return 1.6676
        return 2.1000
    elif wealth <= 4020770.98:
        if group <= 2:  return 1.1000
        if group == 3:  return 1.7471
        return 2.2000
    else:
        if group <= 2:  return 1.2000
        if group == 3:  return 1.9059
        return 2.4000
