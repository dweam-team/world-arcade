import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
import pydantic


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GameInfo(BaseModel):
    _implementation: Any = PrivateAttr(None)

    type: str = Field(description="Used to group games. Shows up in the `{type}/{id}` URL slug.")
    id: str = Field(description="Unique identifier for the game. Shows up in the `{type}/{id}` URL slug.")
    title: str | None = Field(default=None, description="Display name for the game")
    description: str | None = Field(default=None, description="Short description for the game")
    tags: list[str] | None = Field(default=None, description="List of tags for the game")
    author: str | None = Field(default=None, description="Author of the game")
    build_date: str | None = Field(default=None, description="Build date of the game")
    repo_link: str | None = Field(default=None, description="Link to the repository of the game")
    buttons: dict[str, str] | None = Field(default=None, description="Mapping of button labels to key combinations")


if __name__ == "__main__":
    # Save the schema to a file
    schema = pydantic.TypeAdapter(list[GameInfo]).json_schema()
    with open("game_list_schema.json", "w") as f:
        json.dump(schema, f)
