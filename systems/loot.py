"""
Loot system - module generation from purged entities.
"""
import random   # # nosec B311
from models.module import Module, Rarity, Slot


# Base stat ranges per slot (before rarity multiplier)
SLOT_BASE_STATS = {
    Slot.INJECTOR: {"atk": (2, 5), "crit_rate": (0.01, 0.03)},
    Slot.BARRIER: {"def": (2, 4), "hp": (5, 10)},
    Slot.CACHE: {"atk": (1, 3), "hp": (3, 8), "crit_rate": (0.005, 0.015)},
}

# Module name templates per slot (common → legendary)
SLOT_NAMES = {
    Slot.INJECTOR: ["Relay Module", "Signal Injector", "Consensus Relay", "Stability Matrix", "Genesis Kernel"],
    Slot.BARRIER: ["Cache Layer", "Runtime Patch", "Barrier Array", "Archive Engine", "Zero State Core"],
    Slot.CACHE: ["Echo Unit", "Proxy Node", "Sentinel Unit", "Oracle Fragment", "Prime Agent"],
}

# Rarity weights: [common, uncommon, rare, epic, legendary]
def _rarity_weights(stage: int) -> list:
    factor = min(0.9, stage / 200)
    return [
        max(1, int(100 * (1 - factor))),
        max(1, int(40 * (0.5 + factor))),
        max(1, int(15 * (0.3 + factor))),
        max(0, int(5 * factor)),
        max(0, int(1 * factor)),
    ]


def roll_rarity(stage: int) -> Rarity:
    weights = _rarity_weights(stage)
    rarities = [Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY]
    return random.choices(rarities, weights=weights, k=1)[0]


def generate_module(stage: int) -> Module:
    """Generate a random module scaled to sector."""
    slot = random.choice(list(Slot))
    rarity = roll_rarity(stage)
    
    rarity_index = list(Rarity).index(rarity)
    name_pool = SLOT_NAMES[slot]
    name = name_pool[min(rarity_index, len(name_pool) - 1)]
    name = f"{name} [{rarity.value.title()}]"
    
    base_stats = SLOT_BASE_STATS[slot]
    atk = 0
    def_bonus = 0
    hp = 0
    crit = 0.0
    
    if "atk" in base_stats:
        lo, hi = base_stats["atk"]
        atk = random.randint(lo, hi)
    if "def" in base_stats:
        lo, hi = base_stats["def"]
        def_bonus = random.randint(lo, hi)
    if "hp" in base_stats:
        lo, hi = base_stats["hp"]
        hp = random.randint(lo, hi)
    if "crit_rate" in base_stats:
        lo, hi = base_stats["crit_rate"]
        crit = round(random.uniform(lo, hi), 3)
    
    return Module(
        name=name,
        slot=slot,
        rarity=rarity,
        atk_bonus=atk,
        def_bonus=def_bonus,
        hp_bonus=hp,
        crit_rate_bonus=crit,
    )
