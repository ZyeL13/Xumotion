"""
Module system - install/uninstall/scrap logic with stat application.
"""
from models.module import Module, Slot


def _module_score(mod: Module) -> float:
    """Calculate a simple score for comparing modules."""
    return (
        mod.atk_bonus * 2.0 +
        mod.def_bonus * 1.5 +
        mod.hp_bonus * 0.5 +
        mod.crit_rate_bonus * 100
    )


def _scrap_value(mod: Module) -> int:
    """Credits earned from scrapping a module."""
    rarity_mult = {
        "common": 5,
        "uncommon": 15,
        "rare": 40,
        "epic": 100,
        "legendary": 300,
    }
    base = rarity_mult.get(mod.rarity.value, 5)
    bonus = int(mod.atk_bonus + mod.def_bonus + mod.hp_bonus * 0.3 + mod.crit_rate_bonus * 50)
    return base + bonus


def install_module(player, inventory_index: int) -> str:
    """Install a specific module by bay index (1-based)."""
    if inventory_index < 1 or inventory_index > len(player.inventory):
        return f"INVALID INDEX. Module bay has {len(player.inventory)} slots."

    module = player.inventory[inventory_index - 1]

    if module.installed:
        return f"'{module.name}' already installed."

    # Uninstall existing module in same slot
    for mod in player.inventory:
        if mod.installed and mod.slot == module.slot:
            mod.installed = False
            _remove_bonuses(player, mod)

    # Install new module
    module.installed = True
    _apply_bonuses(player, module)
    return f"INSTALLED: {module.name} ({module.slot.value})."


def uninstall_slot(player, slot_name: str) -> str:
    """Uninstall module from a slot."""
    try:
        slot = Slot(slot_name.lower())
    except ValueError:
        return "INVALID SLOT. Available: injector, barrier, cache."

    for mod in player.inventory:
        if mod.installed and mod.slot == slot:
            mod.installed = False
            _remove_bonuses(player, mod)
            return f"UNINSTALLED: {mod.name} from {slot.value}."
    return f"No module installed in {slot.value}."


def auto_install_best(state) -> str:
    """
    Auto-merge agents, auto-deploy best agents ke slot kosong,
    lalu auto-install best modules di semua slot, dan scrap sisanya.
    """
    from systems.economy import auto_merge, auto_deploy_best

    # 1. Auto-merge agents (3 tier sama → 1 tier lebih tinggi)
    merge_msg = auto_merge(state)

    # 2. Auto-deploy agents dengan DPS tertinggi ke slot yang kosong
    deploy_msg = auto_deploy_best(state)

    player = state.player
    install_result = ""

    # 3. Auto-install modules (kode asli kamu)
    if not player.inventory:
        install_result = "MODULE BAY EMPTY. Nothing to install."
    else:
        messages = []
        total_scrapped = 0
        scrapped_count = 0

        for slot in (Slot.INJECTOR, Slot.BARRIER, Slot.CACHE):
            slot_modules = [m for m in player.inventory if m.slot == slot]
            if not slot_modules:
                continue

            current = next((m for m in player.inventory if m.installed and m.slot == slot), None)
            best = max(slot_modules, key=_module_score)

            if current and best is current:
                continue

            if current:
                current.installed = False
                _remove_bonuses(player, current)
                messages.append(f"Uninstalled: {current.name}")

            best.installed = True
            _apply_bonuses(player, best)
            messages.append(f"Installed: {best.name} ({slot.value})")

        to_keep = [m for m in player.inventory if m.installed]
        to_scrap = [m for m in player.inventory if not m.installed]

        for mod in to_scrap:
            value = _scrap_value(mod)
            player.gold += value
            total_scrapped += value
            scrapped_count += 1

        player.inventory = to_keep

        if messages:
            install_result = "\n".join(messages)
        else:
            install_result = "All slots already optimal."

        if scrapped_count > 0:
            install_result += f"\n\nScrapped {scrapped_count} modules. +{total_scrapped} credits."

    # Gabungkan semua pesan
    final_parts = []
    if merge_msg:
        final_parts.append(merge_msg)
    if deploy_msg:
        final_parts.append(deploy_msg)
    if install_result:
        final_parts.append(install_result)

    return "\n\n".join(final_parts) or "All systems optimal."


def _apply_bonuses(player, module: Module):
    player.atk += module.atk_bonus
    player.defense += module.def_bonus
    player.max_hp += module.hp_bonus
    player.hp += module.hp_bonus
    player.crit_rate = min(1.0, player.crit_rate + module.crit_rate_bonus)


def _remove_bonuses(player, module: Module):
    player.atk -= module.atk_bonus
    player.defense -= module.def_bonus
    player.max_hp -= module.hp_bonus
    player.hp = min(player.hp, player.max_hp)
    player.crit_rate = max(0.0, player.crit_rate - module.crit_rate_bonus)
