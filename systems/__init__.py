from systems.economy import handle_upgrade, deploy_agent
from systems.prestige import do_prestige, can_prestige, get_core_gain
from systems.modules import install_module, uninstall_slot
from systems.autobuy import autobuy_tick
from systems.daily import claim_daily, can_claim
from systems.progression import required_exp, check_level_up
from systems.automation import tick_automation
from systems.loot import generate_module
