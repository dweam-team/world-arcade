from collections import defaultdict
import pkg_resources
from structlog.stdlib import BoundLogger

from dweam.game import GameInfo
import importlib_metadata


def load_games(log: BoundLogger) -> dict[str, dict[str, GameInfo]]:
    games = defaultdict(dict)
    game_entrypoints = defaultdict(dict)
    entrypoints = importlib_metadata.entry_points(group="dweam")
    for entry_point in entrypoints.select(name="game"):
        try:
            game_class = entry_point.load()
        except Exception as e:
            log.exception("Error loading game entrypoint", entrypoint=entry_point)
            continue

        if isinstance(game_class.game_info, list):
            game_infos = game_class.game_info
        else:
            game_infos = [game_class.game_info]

        for game_info in game_infos:
            game_info._implementation = game_class
            if game_info.id in games[game_info.type]:
                previous_entrypoint = game_entrypoints[game_info.type][game_info.id]
                current_entrypoint = entry_point.name
                log.error(
                    "Game ID already exists for type. Overriding...",
                    type=game_info.type,
                    id=game_info.id,
                    previous_entrypoint=previous_entrypoint,
                    new_entrypoint=current_entrypoint,
                )
            game_entrypoints[game_info.type][game_info.id] = entry_point.name
            games[game_info.type][game_info.id] = game_info

        log.info("Loaded game entrypoint", entrypoint=entry_point)
    return games
