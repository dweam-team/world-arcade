import json
from typing import Any, Literal, Mapping, Sequence, Union
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field as PydanticField, PrivateAttr
import pydantic


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def Field(*args, ui_schema: dict | None = None, **kwargs):
    if ui_schema:
        kwargs["json_schema_extra"] = {"_ui_schema": ui_schema}
    return PydanticField(*args, **kwargs)


class BaseSource(StrictModel):
    """Base class for all dependency sources"""
    markers: str | None = Field(
        default=None, 
        description="Environment markers (e.g. 'platform_system != \"Windows\"')"
    )
    # FIXME support nonstandard metadata locations?
    # metadata: Path = Field(default=Path("dweam.toml"), description="Path to the package's game metadata file")


class PathSource(BaseSource):
    """Local path source"""
    path: Path


class PyPISource(BaseSource):
    """PyPI package source"""
    version: str


class BaseGitSource(BaseSource):
    """Git repository source"""
    git: str
    branch: str | None = None
    tag: str | None = None
    rev: str | None = None

class GitBranchSource(BaseGitSource):
    branch: str


class GitTagSource(BaseGitSource):
    tag: str


class GitRevSource(BaseGitSource):
    rev: str


# Union type for all sources
GameSource = PathSource | PyPISource | GitBranchSource | GitTagSource | GitRevSource


class GameInfo(StrictModel):
    """Metadata for a specific game variant"""
    title: str | None = Field(default=None, description="Display name for the game")
    description: str | None = Field(default=None, description="Short description for the game")
    tags: list[str] | None = Field(default=None, description="List of tags for the game")
    buttons: dict[str, str] | None = Field(default=None, description="Mapping of button labels to key combinations")
    _metadata: "PackageMetadata | None" = PrivateAttr(None)

    def get_implementation(self) -> type:
        """Get the game implementation class from the metadata's entrypoint"""
        if not self._metadata:
            raise ValueError("Game metadata not set")
        from dweam.utils.entrypoint import load_game_implementation
        return load_game_implementation(self._metadata.entrypoint)


class PackageMetadata(StrictModel):
    """Metadata for a game package"""
    type: str
    entrypoint: str
    repo_link: str | None = None
    thumbnail_dir: str = Field(default="thumbnails", description="Directory containing thumbnail videos (gif/webm/mp4)")
    games: dict[str, GameInfo]
    _module_dir: Path | None = PrivateAttr(None)


class SourceConfig(StrictModel):
    """Main configuration file model for managing game sources.
    This configuration lives in dweam-sources.toml and defines where to find game packages."""
    packages: Mapping[str, Sequence[GameSource]]


class ParamsUpdate(BaseModel):
    """Parameter update request"""
    session_id: str
    params: dict


class StatusResponse(BaseModel):
    is_loading: bool


if __name__ == "__main__":
    # Save the schemas
    sources_schema = pydantic.TypeAdapter(SourceConfig).json_schema()
    with open("dweam-sources-schema.json", "w") as f:
        json.dump(sources_schema, f)

    metadata_schema = pydantic.TypeAdapter(GameInfo).json_schema()
    with open("dweam-metadata-schema.json", "w") as f:
        json.dump(metadata_schema, f)
