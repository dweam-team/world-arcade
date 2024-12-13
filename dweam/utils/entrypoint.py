from collections import defaultdict
import importlib
import os
from typing_extensions import assert_never
import tomli
import venv
import subprocess
from pathlib import Path
from structlog.stdlib import BoundLogger
import importlib.util
import sys

from dweam.models import (
    PackageMetadata, GameInfo, GameSource,
    GitBranchSource, PathSource, PyPISource, SourceConfig
)


# Define default sources for each game
DEFAULT_SOURCE_CONFIG = SourceConfig(
    packages={
        "diamond_atari": [
            PathSource(
                path=Path("diamond"),
                metadata=Path("dweam.toml")
            ),
            GitBranchSource(
                git="https://github.com/dweam-team/diamond",
                branch="main",
                metadata=Path("dweam.toml")
            ),
        ],
        # "diamond_csgo": [
        #     PathSource(
        #         path=Path("diamond_csgo"),
        #         metadata=Path("dweam.toml")
        #     ),
        #     GitBranchSource(
        #         git="https://github.com/dweam-team/diamond",
        #         branch="csgo",
        #         metadata=Path("dweam.toml")
        #     ),
        # ],
        # "lucid_v1": [
        #     PathSource(
        #         path=Path("lucid-v1"),
        #         metadata=Path("dweam.toml")
        #     ),
        #     GitBranchSource(
        #         git="https://github.com/dweam-team/lucid-v1",
        #         branch="main",
        #         metadata=Path("dweam.toml")
        #     ),
        # ]
    }
)


def create_and_setup_venv(path: Path) -> Path:
    """Create a new virtual environment and return its path"""
    venv.create(path, with_pip=True)
    return path


def get_cache_dir() -> Path:
    """Get the cache directory for storing git repositories"""
    cache_dir = os.environ.get("CACHE_DIR")
    if cache_dir is not None:
        return Path(cache_dir)
    return Path.home() / ".dweam" / "cache"


def ensure_correct_dweam_version(log: BoundLogger, pip_path: Path) -> None:
    """Ensure the correct version of dweam is installed in the venv"""
    import dweam
    
    # Get our local dweam path, handling both development and PyInstaller environments
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        dweam_path = Path(sys._MEIPASS) / 'dweam'
    else:
        # Running in development
        dweam_path = Path(dweam.__file__).parent.parent
    
    # Get installed version using pip show
    try:
        result = subprocess.run(
            [str(pip_path), "show", "dweam"],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse location from pip show output
        install_location = None
        for line in result.stdout.splitlines():
            if line.startswith("Location: "):
                install_location = line.split(": ")[1].strip()
                break
        
        # If dweam isn't installed from our path, reinstall it
        if not install_location or not Path(install_location).samefile(dweam_path):
            log.warning("dweam is not installed from the correct location, reinstalling")
            subprocess.run([str(pip_path), "install", "-e", str(dweam_path)], check=True)
            
    except subprocess.CalledProcessError:
        # dweam not installed or pip show failed
        log.warning("dweam not installed, reinstalling")
        subprocess.run([str(pip_path), "install", "-e", str(dweam_path)], check=True)


def install_game_source(log: BoundLogger, venv_path: Path, source: GameSource, name: str) -> Path | None:
    """Install a game from its source into the given venv and return the installation path"""
    pip_path = venv_path / "bin" / "pip"
    
    if isinstance(source, PathSource):
        abs_path = source.path.absolute()
        subprocess.run([str(pip_path), "install", "-e", str(abs_path)], check=True)
        ensure_correct_dweam_version(log, pip_path)
        return abs_path
    elif isinstance(source, GitBranchSource):
        git_url = f"git+{source.git}@{source.branch}#egg={name}"
        subprocess.run([str(pip_path), "install", git_url], check=True)
        
        # Clone into a unique directory in our cache
        cache_dir = get_cache_dir()
        package_dir = (cache_dir / name).absolute()
        package_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-b", source.branch, source.git, str(package_dir)], check=True)
        ensure_correct_dweam_version(log, pip_path)
        return package_dir
    elif isinstance(source, PyPISource):
        subprocess.run([str(pip_path), "install", f"{name}=={source.version}"], check=True)
        ensure_correct_dweam_version(log, pip_path)
        site_packages = next((venv_path / "lib").glob("python*/site-packages"))
        return site_packages / name
    else:
        assert_never(source)
        return None


def load_game_source(install_path: Path, source: GameSource) -> PackageMetadata | None:
    """Load game metadata from an installed source"""
    metadata = load_metadata_from_path(install_path)
    if metadata:
        metadata._source = source
        metadata._local_dir = install_path
    return metadata


def load_metadata_from_path(path: Path) -> PackageMetadata | None:
    """Load metadata from a directory path (git clone or local path)"""
    try:
        # First try dweam.toml
        dweam_path = path / "dweam.toml"
        if dweam_path.exists():
            with open(dweam_path, "rb") as f:
                data = tomli.load(f)
            return PackageMetadata.model_validate(data)
        
        # Then try pyproject.toml
        pyproject_path = path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomli.load(f)
                
            # Get the [tool.dweam] table
            if "tool" in pyproject_data and "dweam" in pyproject_data["tool"]:
                dweam_data = pyproject_data["tool"]["dweam"]
                if "games" not in dweam_data:
                    raise ValueError("No [tool.dweam.games] section found in pyproject.toml")
                return PackageMetadata.model_validate(dweam_data)
    except (TypeError, OSError) as e:
        print(f"Error loading metadata from path: {e}")
        pass
    
    return None
def load_metadata_from_package(package_path: Path) -> PackageMetadata | None:
    """Load metadata from the parent directory of an installed package"""
    try:
        # Get the parent directory of the package
        # TODO this'll work for git and local when dweam.toml is in root
        #  but not for pypi
        parent_path = package_path.parent

        # Try dweam.toml in the parent directory
        dweam_path = parent_path / "dweam.toml"
        if dweam_path.exists():
            with open(dweam_path, "rb") as f:
                data = tomli.load(f)
            return PackageMetadata.model_validate(data)
    except (TypeError, OSError) as e:
        print(f"Error loading metadata from package: {e}")
        pass
    
    return None

def load_game_implementation(entrypoint: str) -> type:
    """Load a game implementation from an entrypoint string (e.g. 'package.module:Class')"""
    try:
        module_path, class_name = entrypoint.split(':')
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        raise ImportError(f"Failed to load game implementation from {entrypoint}: {e}")

def load_games(
    log: BoundLogger,
    venv_path: Path | None = None,
    games: defaultdict[str, dict[str, GameInfo]] | None = None,
) -> dict[str, dict[str, GameInfo]]:
    """Load games from their sources into a single venv"""
    if games is None:
        games = defaultdict(dict)

    for name, sources in DEFAULT_SOURCE_CONFIG.packages.items():
        success = False
        for source in sources:
            try:
                if venv_path is not None:
                    # Install and load from venv
                    install_path = install_game_source(log, venv_path, source, name)
                    if install_path is None:
                        continue
                    metadata = load_game_source(install_path, source)
                else:
                    # Try to load from installed package
                    try:
                        spec = importlib.util.find_spec(name)
                        if spec is None or spec.origin is None:
                            continue
                        package_path = Path(spec.origin).parent
                        metadata = load_metadata_from_package(package_path)
                        if metadata:
                            metadata._source = source
                            metadata._local_dir = package_path
                    except ImportError:
                        log.warning("Failed to load game from installed package", name=name, source=source, exc_info=True)
                        continue

                if metadata is None:
                    log.warning("No metadata found for game", name=name)
                    continue
                    
                # Add game info to the games dict
                for game_id, game_info in metadata.games.items():
                    if game_id in games[metadata.type]:
                        log.warning(
                            "Game ID already exists for type. Overriding...",
                            type=metadata.type,
                            id=game_id,
                        )
                    game_info._metadata = metadata
                    games[metadata.type][game_id] = game_info
                
                log.info("Successfully loaded game", name=name)
                success = True
                break
                
            except Exception as e:
                log.warning("Failed to load game from source", name=name, source=source, exc_info=True)
                continue
                
        if not success:
            log.error("Failed to load game from any source", name=name)
            
    return games


# def load_game_entrypoints(log: BoundLogger, games: defaultdict[str, dict[str, GameInfo]] | None = None) -> dict[str, dict[str, GameInfo]]:
#     """Load all games from installed packages"""
#     if games is None:
#         games = defaultdict(dict)

#     game_entrypoints = defaultdict(dict)
#     entrypoints = importlib_metadata.entry_points(group="dweam")
#     for entry_point in entrypoints.select(name="game"):
#         try:
#             game_class = entry_point.load()
#         except Exception as e:
#             log.exception("Error loading game entrypoint", entrypoint=entry_point)
#             continue

#         if isinstance(game_class.game_info, list):
#             game_infos = game_class.game_info
#         else:
#             game_infos = [game_class.game_info]

#         for game_info in game_infos:
#             game_info._implementation = game_class
#             if game_info.id in games[game_info.type]:
#                 previous_entrypoint = game_entrypoints[game_info.type][game_info.id]
#                 current_entrypoint = entry_point.name
#                 log.error(
#                     "Game ID already exists for type. Overriding...",
#                     type=game_info.type,
#                     id=game_info.id,
#                     previous_entrypoint=previous_entrypoint,
#                     new_entrypoint=current_entrypoint,
#                 )
#             game_entrypoints[game_info.type][game_info.id] = entry_point.name
#             games[game_info.type][game_info.id] = game_info

#         log.info("Loaded game entrypoint", entrypoint=entry_point)
#     return games
