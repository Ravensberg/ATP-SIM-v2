"""One-game tactical modifiers for the ATP Sim Pygame layer.

Stats use the existing per-1000 probability model from player.py.
These helpers do not simulate points; they only provide temporary stat deltas
that matchsimulation.MatchSimulation can apply for one game.

Python 3.9 compatible.
"""

from copy import deepcopy
from typing import Dict, List

STAT_KEYS = [
    "ace",
    "double_fault",
    "first_serve_in",
    "first_serve_won",
    "second_serve_won",
    "break_point_saved",
    "return_first_serve_won",
    "return_second_serve_won",
    "break_point_won",
]

TACTICS = {
    "Serve + Volley": {
        "serving": {
            "ace": 35,
            "first_serve_won": 55,
            "second_serve_won": -20,
            "break_point_saved": 35,
        },
        "returning": {
            "return_first_serve_won": -15,
            "return_second_serve_won": 15,
            "break_point_won": 10,
        },
        "desc": "Aggressive first strike. Strong on serve, less stable in longer rallies.",
    },
    "Baseline Defense": {
        "serving": {
            "first_serve_in": 45,
            "second_serve_won": 45,
            "break_point_saved": 45,
            "ace": -25,
            "first_serve_won": -10,
        },
        "returning": {
            "return_first_serve_won": 25,
            "return_second_serve_won": 45,
            "break_point_won": 25,
        },
        "desc": "Raise the floor and protect pressure points. Lower explosive upside.",
    },
    "Return Attack": {
        "serving": {
            "first_serve_in": -20,
            "first_serve_won": 15,
            "double_fault": 15,
        },
        "returning": {
            "return_first_serve_won": 35,
            "return_second_serve_won": 70,
            "break_point_won": 55,
        },
        "desc": "Step in on return. Best when trying to break; slightly volatile on serve.",
    },
    "Redline Forehand": {
        "serving": {
            "ace": 30,
            "first_serve_won": 50,
            "second_serve_won": 25,
            "double_fault": 35,
            "first_serve_in": -35,
        },
        "returning": {
            "return_first_serve_won": 45,
            "return_second_serve_won": 45,
            "break_point_won": 40,
        },
        "desc": "High variance. More cheap points, more errors. Useful when chasing.",
    },
}

# Backwards-compatible alias expected by app.py.
TARGETS = {
    "Wide": {
        "ace": 15,
        "first_serve_won": 15,
        "return_first_serve_won": -5,
    },
    "Body": {
        "first_serve_in": 20,
        "second_serve_won": 15,
        "break_point_saved": 10,
    },
    "T": {
        "ace": 25,
        "first_serve_won": 10,
        "double_fault": 10,
    },
}

# Older app versions may reference ZONE_BONUS.
ZONE_BONUS = TARGETS


def merge_modifiers(*mods):
    # type: (*Dict[str, int]) -> Dict[str, int]
    merged = {}
    for mod in mods:
        for key, value in mod.items():
            merged[key] = merged.get(key, 0) + int(value)
    return merged


def build_player_modifier(tactic_name, target_name, is_serving):
    # type: (str, str, bool) -> Dict[str, int]
    """Return one player's temporary modifier for the next game.

    This is the function expected by the newer Pygame app:
        modifier = build_player_modifier(tactic, target, is_player_a_serving)
        modifiers = {player_a.name: modifier}
    """
    tactic = deepcopy(TACTICS.get(tactic_name, TACTICS["Baseline Defense"]))
    role = "serving" if is_serving else "returning"
    target = TARGETS.get(target_name, {})
    return merge_modifiers(tactic[role], target)


def describe_choice(tactic_name, target_name, is_serving=None):
    # type: (str, str, object) -> str
    tactic = TACTICS.get(tactic_name, TACTICS["Baseline Defense"])
    target = TARGETS.get(target_name, {})
    target_parts = []
    for key in sorted(target.keys()):
        value = target[key]
        sign = "+" if value >= 0 else ""
        target_parts.append("{} {}{}".format(key, sign, value))
    if target_parts:
        return "{} / {}: {} Target: {}.".format(
            tactic_name,
            target_name,
            tactic.get("desc", ""),
            ", ".join(target_parts),
        )
    return "{} / {}: {}".format(tactic_name, target_name, tactic.get("desc", ""))


def player_a_modifiers_for_next_game(player_a_name, server_name, tactic_name, zone_name):
    # type: (str, str, str, str) -> Dict[str, Dict[str, int]]
    """Return modifiers in the format expected by MatchSimulation.simulate_next_game.

    Only Player A receives the interactive tactical modifier. The role is inferred
    from whether Player A is currently serving the next game.
    """
    is_serving = server_name == player_a_name
    return {player_a_name: build_player_modifier(tactic_name, zone_name, is_serving)}
