from collections import defaultdict
import importlib
from structlog.stdlib import BoundLogger

from dweam.game import GameInfo

HARDCODED_ENTRYPOINTS = {
    "diamond_atari": "diamond_atari.dweam_game:DiamondGame",
    "diamond_csgo": "diamond_csgo.dweam_game:CSGOGame",
    "lucid_v1": "lucid_v1.dweam_game:LucidGame",
}


def load_games(log: BoundLogger, games: defaultdict[str, dict[str, GameInfo]] | None = None) -> dict[str, dict[str, GameInfo]]:
    """Load hardcoded game entrypoints"""
    if games is None:
        games = defaultdict(dict)

    for entrypoint_name, entrypoint_path in HARDCODED_ENTRYPOINTS.items():
        module_path, class_name = entrypoint_path.split(":")
        try:
            module = importlib.import_module(module_path)
            game_class = getattr(module, class_name)
        except Exception as e:
            log.warning("Failed to load game entrypoint", entrypoint_name=entrypoint_name, error=str(e))
            continue

        if isinstance(game_class.game_info, list):
            game_infos = game_class.game_info
        else:
            game_infos = [game_class.game_info]

        for game_info in game_infos:
            game_info._implementation = game_class
            if game_info.id in games[game_info.type]:
                log.error(
                    "Game ID already exists for type. Overriding...",
                    type=game_info.type,
                    id=game_info.id,
                    previous_game=games[game_info.type][game_info.id],
                )
            games[game_info.type][game_info.id] = game_info

        log.info("Loaded game entrypoint", entrypoint=entrypoint_name)
    return games
