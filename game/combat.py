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

    # Player deal damage
    damage = combat_damage(player.atk, player.dps, enemy.defense)
    damage = apply_crit(damage, player.crit_rate, player.crit_damage)
    enemy.hp = max(0, enemy.hp - damage)

    # Enemy attacks back (only if enemy alive)
    if enemy.hp > 0:
        enemy_dmg = enemy_damage(enemy.atk, int(player.effective_def))
        player.hp = max(0, player.hp - enemy_dmg)

        # Check player death
        if player.hp <= 0:
            state.player_dead = True
            if state.boss_active:
                # Boss fight: gagal total
                state.boss_active = False
                state.boss_timer = 0.0
                event_logger.emit("checkpoint_failed", f"CHECKPOINT FAILED — Sector {state.sector} Boss remains. Use /next to retry.")
                return
            else:
                # Normal encounter: auto‑respawn
                player.hp = player.effective_max_hp
                state.player_dead = False
                from models.enemy import Enemy
                state.enemy = Enemy.generate(state.sector, state.substage, state.player)
                event_logger.emit("operator_down", f"OPERATOR DOWN — Auto‑recovered at Sector {state.sector} · {state.substage}/10")
                return

    # Boss timer check (only when active)
    if state.boss_active and state.boss_timer > 0.0:
        state.boss_timer -= 1.0  # tick adalah 1 detik
        if state.boss_timer <= 0.0:
            state.boss_active = False
            state.boss_timer = 0.0
            event_logger.emit("checkpoint_failed", f"CHECKPOINT FAILED — Timeout. Sector {state.sector} Boss remains. Use /next to retry.")
            return

    # Enemy death
    if enemy.hp <= 0:
        # Rewards
        loot_chance = 0.5
        if state.boss_active:
            player.gold += int(enemy.reward_gold * 2.5)
            player.exp += int(enemy.reward_exp * 3)
            loot_chance = 0.9
            state.boss_active = False
            state.boss_timer = 0.0
            event_logger.emit("checkpoint_cleared", f"CHECKPOINT CLEARED — Sector {state.sector} Boss defeated!")
        else:
            player.gold += enemy.reward_gold
            player.exp += enemy.reward_exp

        state.kills_in_stage += 1

        event_logger.emit("target_purged", f"TARGET PURGED: {enemy.name} | +{enemy.reward_gold} CREDITS +{enemy.reward_exp} EXP")

        # Loot drop
        if random.random() < loot_chance:  # nosec B311
            from systems.loot import generate_module
            # gunakan sector untuk penentuan loot (bisa diadaptasi)
            loot = generate_module(state.sector * 10)  # temporary scaling
            player.inventory.append(loot)
            event_logger.emit("module_found", f"MODULE FOUND: {loot.name} ({loot.rarity.value})")

        # Level up
        leveled = progression.check_level_up(player)
        if leveled:
            event_logger.emit("rank_up", f"RANK UPDATED → LVL {player.level}")

        # Check achievements
        check_and_unlock(state)

        # Maju ke encounter berikutnya
        if state.substage == 10:
            # Boss selesai → pindah sektor
            state.sector += 1
            state.substage = 1
            state.boss_active = False
            state.boss_timer = 0.0
        else:
            state.substage += 1
            # Jika substage sekarang 10, tandai boss aktif dan setel timer
            if state.substage == 10:
                state.boss_active = True
                # Pilih timer berdasarkan sektor
                if state.sector <= 5:
                    state.boss_timer = 60.0
                elif state.sector <= 15:
                    state.boss_timer = 45.0
                else:
                    state.boss_timer = 30.0

        # Spawn musuh baru untuk encounter berikutnya
        from models.enemy import Enemy
        state.enemy = Enemy.generate(state.sector, state.substage, state.player)
        event_logger.emit("new_target", f"SECTOR {state.sector} · {state.substage}/10: {state.enemy.name}")
