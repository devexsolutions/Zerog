from typing import List, Dict, Any
import models

def calculate_estate(case: models.Case) -> Dict[str, Any]:
    """
    Calcula la masa hereditaria, ajuar y caudal relicto.
    Regla general LISD Art. 15: Ajuar = 3% del Caudal Relicto (interpretado como Activo Bruto).
    """
    total_assets = 0.0
    total_debts = 0.0
    
    # Sumar activos y pasivos
    for asset in case.assets:
        if asset.is_debt or asset.is_funeral_expense:
            total_debts += asset.value
        else:
            total_assets += asset.value
            
    # Calcular Ajuar Doméstico (3% del valor de los bienes activos)
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
        "taxable_base": round(taxable_base, 2)
    }

def calculate_tax_for_heir(base_imponible: float, relationship: str, pre_existing_wealth: float) -> Dict[str, float]:
    """
    Calcula la Cuota Tributaria según normativa estatal (Ley 29/1987).
    Simplificado para MVP.
    """
    # 1. Reducciones (Art. 20 LISD)
    reductions = 0.0
    # Simplificación Grupos Parentesco
    # I (<21), II (>21, Conyuge, Ascendientes), III (Colaterales 2/3 grado), IV (Colaterales 4 grado, Extraños)
    rel = relationship.lower()
    if rel in ["child", "hijo", "son", "daughter", "hija"]:
        # Asumimos Grupo II por defecto (>21) si no tenemos edad. MVP.
        reductions = 15956.87
    elif rel in ["spouse", "conyuge", "husband", "wife", "esposo", "esposa"]:
        reductions = 15956.87
    elif rel in ["parent", "padre", "madre", "father", "mother"]:
        reductions = 15956.87
    elif rel in ["sibling", "hermano", "hermana", "brother", "sister", "uncle", "aunt", "tio", "tia", "nephew", "niece", "sobrino", "sobrina"]:
        reductions = 7993.46
    else:
        reductions = 0.0 # Grupo IV
    
    liquidable_base = max(0, base_imponible - reductions)
    
    # 2. Tarifa (Art. 21 LISD - Simplificada)
    # Tramos estatales (0 - 7.65% ... >797k - 34%)
    # Usaremos una aproximación lineal o tabla simplificada
    quota_integra = calculate_tariff(liquidable_base)
    
    # 3. Coeficiente Multiplicador (Art. 22 LISD)
    multiplier = get_multiplier(pre_existing_wealth, rel)
    
    tax_quota = quota_integra * multiplier
    
    return {
        "reductions": round(reductions, 2),
        "liquidable_base": round(liquidable_base, 2),
        "quota_integra": round(quota_integra, 2),
        "multiplier": round(multiplier, 4),
        "tax_quota": round(tax_quota, 2)
    }

def calculate_tariff(base: float) -> float:
    # Tabla Estatal (aproximada)
    # Hasta 0 -> 0
    # 7993.46 -> 7.65%
    # ...
    # Simplificación MVP: Tabla progresiva
    brackets = [
        (0, 0, 0.0765),
        (7993.46, 611.5, 0.085),
        (15980.91, 1290.43, 0.0935),
        (23968.36, 2037.26, 0.102),
        (31955.81, 2852.98, 0.1105),
        (39943.26, 3735.65, 0.119),
        (47930.72, 4686.22, 0.1275),
        (55918.17, 5704.77, 0.136),
        (63905.62, 6791.30, 0.1445),
        (71893.07, 7946.06, 0.153),
        (79880.52, 9168.99, 0.1615),
        (119757.67, 15609.63, 0.187),
        (159634.83, 23067.81, 0.2125),
        (239389.13, 40015.60, 0.255),
        (398777.54, 80655.19, 0.2975),
        (797555.08, 199291.40, 0.34)
    ]
    
    cuota = 0
    remaining = base
    
    # Encontrar el tramo
    for i in range(len(brackets) - 1, -1, -1):
        limit, base_cuota, percent = brackets[i]
        if base >= limit:
            cuota = base_cuota + (base - limit) * percent
            return cuota
            
    return base * 0.0765

def get_multiplier(wealth: float, relationship: str) -> float:
    # Tabla Coeficientes (Simplificada)
    # Patrimonio < 402k -> 1.0 (I, II), 1.5882 (III), 2.0 (IV)
    # Patrimonio > 4M -> 1.2 (I, II), 1.9 (III), 2.4 (IV)
    
    # Grupo
    group = 4
    rel = relationship.lower()
    if rel in ["child", "hijo", "son", "daughter", "hija", "spouse", "conyuge", "husband", "wife", "parent", "padre", "madre"]:
        group = 2 # Asumimos I/II
    elif rel in ["sibling", "hermano", "hermana", "uncle", "aunt", "nephew", "niece"]:
        group = 3
    
    if wealth <= 402678.11:
        if group <= 2: return 1.0
        if group == 3: return 1.5882
        return 2.0
    elif wealth <= 2007380.43:
        if group <= 2: return 1.05
        if group == 3: return 1.6676
        return 2.1
    elif wealth <= 4020770.98:
        if group <= 2: return 1.1
        if group == 3: return 1.7471
        return 2.2
    else:
        if group <= 2: return 1.2
        if group == 3: return 1.9059
        return 2.4
