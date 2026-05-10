"""
game/state_manager.py — Multi‑user state manager.
Loads/saves GameState from SQLite.
Simulates offline progress without spawning duplicate enemies.
"""
import time
from game.state import GameState
from game.combat import tick_combat
from systems.automation import tick_automation
from systems.autobuy import autobuy_tick
from game.event_logger import event_logger
from models.enemy import Enemy
from models.player import Player
from game.offline import calculate_offline_reward
from game.database import get_or_create_user, load_game_state, init_db

OFFLINE_CAP_SECONDS = 8 * 3600


class UserStateManager:

    def __init__(self):
        pass

    # ── PUBLIC API ──────────────────────────

    def load_or_create(self, telegram_id: int, username: str = None) -> GameState:
        """Return hydrated GameState. Creates fresh state for new users."""
        init_db()
        user_db_id = get_or_create_user(telegram_id, username)
        data = load_game_state(user_db_id)

        if data is None:
            state = self._create_fresh(user_db_id)
        else:
            state = self._load_existing(user_db_id, data)

        # Simulate offline ticks
        now = time.time()
        elapsed = now - state.last_save

        if not state.paused and elapsed > 0:
            ticks = int(min(elapsed, OFFLINE_CAP_SECONDS))
            if ticks > 0:
                self._simulate_ticks(state, ticks)

        calculate_offline_reward(state)
        self.save(state)
        return state

    def save(self, state: GameState) -> None:
        """Persist GameState to SQLite."""
        from game.database import save_game_state as db_save
        db_save(state.user_id, {
            "sector": state.sector,
            "substage": state.substage,
            "boss_active": state.boss_active,
            "boss_timer": state.boss_timer,
            "kills_in_stage": state.kills_in_stage,
            "player": state.player.to_dict(),
            "enemy": state.enemy.to_dict() if state.enemy else None,
            "last_save": time.time(),
            "paused": state.paused,
        })

    # ── PRIVATE HELPERS ─────────────────────

    def _create_fresh(self, user_db_id: int) -> GameState:
        """Build a brand‑new GameState for a new user."""
        player = Player()
        enemy = Enemy.generate(sector=1, substage=1, player=player)
        return GameState(
            player=player,
            enemy=enemy,
            user_id=user_db_id,
            last_save=time.time(),
            offline_message="SYSTEMS ONLINE.",
        )

    def _load_existing(self, user_db_id: int, data: dict) -> GameState:
        """Rebuild GameState from database row."""
        player = Player.from_dict(data.get("player_data", {}))

        # Restore enemy from save, or generate fresh one
        enemy_data = data.get("enemy")
        if enemy_data:
            enemy = Enemy.from_dict(enemy_data)
        else:
            enemy = Enemy.generate(
                data.get("sector", 1),
                data.get("substage", 1),
                player,
            )

        return GameState(
            player=player,
            enemy=enemy,
            sector=data.get("sector", 1),
            substage=data.get("substage", 1),
            boss_active=data.get("boss_active", False),
            boss_timer=data.get("boss_timer", 0.0),
            kills_in_stage=data.get("kills_in_stage", 0),
            user_id=user_db_id,
            last_save=data.get("last_save", time.time()),
            paused=bool(data.get("paused", False)),
        )

    def _simulate_ticks(self, state: GameState, ticks: int) -> None:
        """Fast-forward simulation."""
        from game.formulas import combat_damage, apply_crit, enemy_damage

        kills = 0
        gold_earned = 0

        for _ in range(ticks):
            if state.boss_active:
                # Boss timer ticks down
                if state.boss_timer > 0:
                    state.boss_timer -= 1.0
                    if state.boss_timer <= 0.0:
                        state.boss_active = False
                        state.boss_timer = 0.0
                        event_logger.emit("boss_timeout", "BOSS TIMEOUT — Returning to normal patrol.")
                # TETAP FIGHT — jangan skip
                # continue  ← DIHAPUS

            # Normal combat (jalan terus, baik boss maupun normal)
            dmg = combat_damage(state.player.atk, state.player.dps, state.enemy.defense)
            dmg = apply_crit(dmg, state.player.crit_rate, state.player.crit_damage)
            state.enemy.hp -= dmg

            if state.enemy.hp > 0:
                edmg = enemy_damage(state.enemy.atk, int(state.player.effective_def))
                state.player.hp -= edmg
                if state.player.hp <= 0:
                    state.player.hp = state.player.effective_max_hp
                    if state.boss_active:
                        # Player mati saat boss fight = gagal
                        state.boss_active = False
                        state.boss_timer = 0.0
                        event_logger.emit("boss_failed", "OPERATOR DOWN — Boss fight failed. Retry.")
                        continue

            # Enemy killed
            if state.enemy.hp <= 0:
                kills += 1
                gold_earned += state.enemy.reward_gold
                state.player.gold += state.enemy.reward_gold
                state.player.exp += state.enemy.reward_exp
                state.kills_in_stage += 1

                # Boss bonus
                if state.boss_active:
                    state.player.gold += int(state.enemy.reward_gold * 1.5)
                    state.player.exp += int(state.enemy.reward_exp * 2)
                    event_logger.emit("boss_defeated", f"BOSS DEFEATED — Sector {state.sector} cleared!")

                # Progression
                if state.substage >= 10:
                    state.sector += 1
                    state.substage = 1
                    state.boss_active = False
                    state.boss_timer = 0.0
                else:
                    state.substage += 1
                    if state.substage == 10:
                        state.boss_active = True
                        if state.sector <= 5:
                            state.boss_timer = 60.0
                        elif state.sector <= 15:
                            state.boss_timer = 45.0
                        else:
                            state.boss_timer = 30.0

                state.enemy = Enemy.generate(state.sector, state.substage, state.player)

            tick_automation(state)
            autobuy_tick(state)

        if kills > 0:
            event_logger.emit("batch_kills",
                f"> Purged {kills} target(s) | +{gold_earned} OUTPUT | Sector {state.sector}·{state.substage}")
            return

        # Long offline gap — batched simulation
        kills = 0
        gold_earned = 0

        for _ in range(ticks):
            if state.boss_active:
                if state.boss_timer > 0:
                    state.boss_timer -= 1.0
                    if state.boss_timer <= 0.0:
                        state.boss_active = False
                        state.boss_timer = 0.0
                continue

            # Quick damage calc
            from game.formulas import combat_damage, apply_crit, enemy_damage

            dmg = combat_damage(state.player.atk, state.player.dps, state.enemy.defense)
            dmg = apply_crit(dmg, state.player.crit_rate, state.player.crit_damage)
            state.enemy.hp -= dmg

            if state.enemy.hp > 0:
                edmg = enemy_damage(state.enemy.atk, int(state.player.effective_def))
                state.player.hp -= edmg
                if state.player.hp <= 0:
                    state.player.hp = state.player.effective_max_hp

            # Enemy killed
            if state.enemy.hp <= 0:
                kills += 1
                gold_earned += state.enemy.reward_gold
                state.player.gold += state.enemy.reward_gold
                state.player.exp += state.enemy.reward_exp
                state.kills_in_stage += 1

                # Progression
                if state.substage >= 10:
                    state.sector += 1
                    state.substage = 1
                    state.boss_active = False
                    state.boss_timer = 0.0
                else:
                    state.substage += 1
                    if state.substage == 10:
                        state.boss_active = True
                        if state.sector <= 5:
                            state.boss_timer = 60.0
                        elif state.sector <= 15:
                            state.boss_timer = 45.0
                        else:
                            state.boss_timer = 30.0

                state.enemy = Enemy.generate(state.sector, state.substage, state.player)

            tick_automation(state)
            autobuy_tick(state)

        if kills > 0:
            event_logger.emit("batch_kills",
                f"> Purged {kills} target(s) | +{gold_earned} OUTPUT | Sector {state.sector}·{state.substage}")


# Singleton
state_manager = UserStateManager()
