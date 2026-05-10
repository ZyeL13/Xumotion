import random  # nosec B311 — gameplay randomness only
import time
from systems import progression
from game.event_logger import event_logger
from game.formulas import combat_damage, apply_crit, enemy_damage
from game.achievement_tracker import check_and_unlock


def tick_combat(state):
    player = state.player
    enemy = state.enemy

    # Jika operator mati, tidak ada proses combat
    if getattr(state, "player_dead", False):
        return

    # Auto-regen: heal 1% max HP per tick
    regen = max(1, int(player.effective_max_hp * 0.01))
    player.hp = min(player.effective_max_hp, player.hp + regen)

    # === BOSS CHECK: skip auto-combat, player must tap ===
    if state.boss_active:
        # Boss timer ticks down
        if state.boss_timer > 0.0:
            state.boss_timer -= 1.0
            if state.boss_timer <= 0.0:
                # Boss timed out
                state.boss_active = False
                state.boss_timer = 0.0
                event_logger.emit("checkpoint_failed",
                    f"CHECKPOINT FAILED — Timeout. Sector {state.sector} Boss remains. Use Start to retry.")
        # Do NOT auto-fight boss
        return

    # === NORMAL COMBAT ===
    # Player deals damage
    damage = combat_damage(player.atk, player.dps, enemy.defense)
    damage = apply_crit(damage, player.crit_rate, player.crit_damage)
    enemy.hp = max(0, enemy.hp - damage)

    # Enemy attacks back (only if enemy still alive)
    if enemy.hp > 0:
        enemy_dmg = enemy_damage(enemy.atk, int(player.effective_def))
        player.hp = max(0, player.hp - enemy_dmg)

        # Player death check
        if player.hp <= 0:
            # Auto-respawn with full HP, same enemy stays
            player.hp = player.effective_max_hp
            event_logger.emit("operator_down",
                f"OPERATOR DOWN — Auto‑recovered at Sector {state.sector} · {state.substage}/10")
            return

    # === ENEMY DEATH + PROGRESSION ===
    if enemy.hp <= 0:
        # Rewards
        player.gold += enemy.reward_gold
        player.exp += enemy.reward_exp

        state.kills_in_stage += 1

        event_logger.emit("target_purged",
            f"TARGET PURGED: {enemy.name} | +{enemy.reward_gold} CREDITS +{enemy.reward_exp} EXP")

        # Loot drop (50% chance for normal)
        if random.random() < 0.5:  # nosec B311
            from systems.loot import generate_module
            loot = generate_module(state.sector * 10)
            player.inventory.append(loot)
            event_logger.emit("module_found",
                f"MODULE FOUND: {loot.name} ({loot.rarity.value})")

        # Level up check
        leveled = progression.check_level_up(player)
        if leveled:
            event_logger.emit("rank_up", f"RANK UPDATED → LVL {player.level}")

        # Achievements
        check_and_unlock(state)

        # === PROGRESSION ===
        if state.substage >= 10:
            # Finished sector → move to next
            state.sector += 1
            state.substage = 1
            state.boss_active = False
            state.boss_timer = 0.0
            event_logger.emit("sector_clear", f"SECTOR {state.sector - 1} CLEARED — Entering Sector {state.sector}")
        else:
            state.substage += 1

        # === CHECK IF NEW SUBSTAGE IS BOSS (substage 10) ===
        if state.substage == 10 and not state.boss_active:
            state.boss_active = True
            # Set boss timer based on sector
            if state.sector <= 5:
                state.boss_timer = 60.0
            elif state.sector <= 15:
                state.boss_timer = 45.0
            else:
                state.boss_timer = 30.0
            event_logger.emit("boss_spawn",
                f"⚠ BOSS ENCOUNTER — Sector {state.sector} · 10/10 — Tap to fight!")

        # Spawn new enemy for next encounter
        from models.enemy import Enemy
        state.enemy = Enemy.generate(state.sector, state.substage, state.player)
        event_logger.emit("new_target",
            f"SECTOR {state.sector} · {state.substage}/10: {state.enemy.name}")
