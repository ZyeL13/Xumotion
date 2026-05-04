from game.constants import LEVEL_EXP_BASE, LEVEL_EXP_GROWTH
from game.formulas import required_exp as _required_exp


def required_exp(level: int) -> int:
    return _required_exp(level, LEVEL_EXP_BASE, LEVEL_EXP_GROWTH)


def check_level_up(player):
    leveled = False
    while player.exp >= required_exp(player.level):
        player.exp -= required_exp(player.level)
        player.level += 1
        from game.constants import ATK_PER_LEVEL, HP_PER_LEVEL
        player.atk += ATK_PER_LEVEL
        player.max_hp += HP_PER_LEVEL
        player.hp = player.max_hp
        leveled = True
    return leveled
