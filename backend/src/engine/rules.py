from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Rule:
    rule_id: str
    antecedents: List[Tuple[str, str]]  # [(field, fuzzy_set), ...]
    conclusion_category: str  # 'risk', 'dietary_risk', 'micronutrient_risk'
    conclusion_level: str  # 'high', 'moderate', 'low'
    expert_cf: float

def load_rules(config: Dict) -> List[Rule]:
    """Parse rules from config dict into Rule objects."""
    rules = []
    for r in config.get("rules", []):
        antecedents = [(ant[0], ant[1]) for ant in r.get("antecedents", [])]
        conc = r.get("conclusion", ["unknown", "unknown"])
        rules.append(Rule(
            rule_id=r.get("id", "unknown"),
            antecedents=antecedents,
            conclusion_category=conc[0],
            conclusion_level=conc[1],
            expert_cf=float(r.get("expert_cf", 0.0))
        ))
    return rules

def fire_rules(fuzzified: Dict[str, Dict[str, float]], rules: List[Rule]) -> List[Dict]:
    """Fire all rules. For each rule, compute:
    firing_strength = min(membership values for all antecedents) * expert_cf
    Only include rules with firing_strength > 0.
    Returns list of {rule_id, antecedents, strength, expert_cf, conclusion_category, conclusion_level}"""
    fired_rules = []
    
    for rule in rules:
        min_membership = 1.0
        match_found = True
        
        for field, fuzzy_set in rule.antecedents:
            if field in fuzzified and fuzzy_set in fuzzified[field]:
                membership = fuzzified[field][fuzzy_set]
                min_membership = min(min_membership, membership)
            else:
                match_found = False
                break
                
        if match_found and min_membership > 0:
            firing_strength = min_membership * rule.expert_cf
            if firing_strength > 0:
                fired_rules.append({
                    "rule_id": rule.rule_id,
                    "antecedents": rule.antecedents,
                    "strength": firing_strength,
                    "expert_cf": rule.expert_cf,
                    "conclusion_category": rule.conclusion_category,
                    "conclusion_level": rule.conclusion_level
                })
                
    return fired_rules

def combine_conclusions(fired_rules: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Combine multiple rules pointing to the same conclusion using MYCIN combination:
    CF_combined = CF1 + CF2 * (1 - CF1)
    Applied iteratively. Returns {category: {level: combined_cf}}"""
    combined: Dict[str, Dict[str, float]] = {}
    
    for rule in fired_rules:
        category = rule["conclusion_category"]
        level = rule["conclusion_level"]
        cf = rule["strength"]
        
        if category not in combined:
            combined[category] = {}
            
        if level not in combined[category]:
            combined[category][level] = cf
        else:
            current_cf = combined[category][level]
            # MYCIN combination
            combined[category][level] = current_cf + cf * (1.0 - current_cf)
            
    return combined

def determine_final_risk(combined: Dict[str, Dict[str, float]]) -> Tuple[str, float]:
    """Pick the risk level with highest combined CF across all categories.
    Returns (risk_level, confidence)."""
    best_level = "normal"
    max_cf = 0.0
    
    # If there are multiple categories (e.g. general risk, dietary risk), we find the highest overall risk signal.
    for category, levels in combined.items():
        for level, cf in levels.items():
            if cf > max_cf:
                max_cf = cf
                best_level = level
                
    return best_level, max_cf
