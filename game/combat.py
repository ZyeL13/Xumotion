import random  # nosec B311 — used for gameplay randomness only
import time
from systems import progression
from game.event_logger import event_logger
from game.formulas import combat_damage, apply_crit, enemy_damage
from game.achievement_tracker import check_and_unlock


def tick_combat(state):
    player = state.player
    enemy = state.enemy

    # Player deal damage
    damage = combat_damage(player.atk, player.dps, enemy.defense)
    damage = apply_crit(damage, player.crit_rate, player.crit_damage)  # nosec B311
    enemy.hp = max(0, enemy.hp - damage)

    # Enemy attacks back (only if enemy alive)
    if enemy.hp > 0:
        enemy_dmg = enemy_damage(enemy.atk, int(player.effective_def))
        player.hp = max(0, player.hp - enemy_dmg)

        # Check player death
        if player.hp <= 0:
            if not getattr(state, "player_dead", False):
                state.player_dead = True
                event_logger.emit("player_died", "OPERATOR DOWN — Type /restore to continue")
            return

    # Prime Instance spawn (every 5 minutes real time)
    if not hasattr(state, "prime_timer"):
        state.prime_timer = time.time()
    if time.time() - state.prime_timer >= 300:  # 5 minutes
        state.prime_timer = time.time()
        from models.enemy import Enemy
        state.enemy = Enemy.generate_prime(state.current_stage)
        event_logger.emit("prime_spawn", f"PRIME INSTANCE DETECTED: {state.enemy.name}")
        return

    # Enemy death
    if enemy.hp <= 0:
        player.gold += enemy.reward_gold
        player.exp += enemy.reward_exp
        state.kills_in_stage += 1

        event_logger.emit("target_purged", f"TARGET PURGED: {enemy.name} | +{enemy.reward_gold} CREDITS +{enemy.reward_exp} EXP")

        # Loot drop (50%)
        if random.random() < 0.5:  # nosec B311 — gameplay loot roll
            from systems.loot import generate_module
            loot = generate_module(state.current_stage)
            player.inventory.append(loot)
            event_logger.emit("module_found", f"MODULE FOUND: {loot.name} ({loot.rarity.value})")

        # Level up
        leveled = progression.check_level_up(player)
        if leveled:
            event_logger.emit("rank_up", f"RANK UPDATED → LVL {player.level}")

        # Check achievements
        check_and_unlock(state)

        # Advance sector
        if not getattr(state, "player_dead", False):
            state.current_stage += 1
            from models.enemy import Enemy
            state.enemy = Enemy.generate(state.current_stage)
            event_logger.emit("new_target", f"SECTOR {state.current_stage}: {state.enemy.name}")

    # Auto-restore if dead
    if getattr(state, "player_dead", False):
        player.hp = player.effective_max_hp
        state.player_dead = False
        event_logger.emit("restore", "AUTO-RESTORE: Operator back online")
