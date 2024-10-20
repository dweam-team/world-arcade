# ☁️ Dweamworld

Play world model games locally, or stream them from a server.

<img src="https://github.com/user-attachments/assets/ae4ac248-683b-4e76-b475-6c89db6bf596" width="500"/>

## Setup

### Requirements

An NVIDIA GPU.

[Docker](https://www.docker.com/) installed and running,

[Docker compose](https://docs.docker.com/compose/install/) installed.

[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed.

### Running

```
git clone ssh://git@github.com/dweam-team/dweamworld
cd dweamworld
docker compose up --build
```

Once it's running, visit [localhost:4321](http://localhost:4321).

### Exposing to the internet

By default, the backend and frontend will only bind to `localhost`.
Use a reverse proxy to forward the following ports:
- 8080 TCP
- 4321 TCP

Expose the following ports for WebRTC:
- 3478 TCP/UDP
- 5349 TCP/UDP
- 50000-50010 UDP

## Adding a game

Each set of games is implemented as a standalone python package that:
1. Implements a `Game` class that subclasses `dweam.Game`.
2. Exposes a python entrypoint that lets Dweamworld know where to find it.

### Implement it

Subclass `dweam.Game`, provide some metadata with `GameInfo`, and implement the `step` method.

```python
# my_game/dweam_game.py

from dweam import Game, GameInfo
import pygame


class MyGame(Game):
    game_info = GameInfo(
        type="my_game_type",
        id="my_game_id",
        title="My Game",
        ...  # other metadata
    )

    def step(self) -> pygame.Surface:
        """
        A step of your game loop, that runs in its own thread.
        Use `self.keys_pressed`, `self.mouse_pressed` and `self.mouse_motion` to generate the next frame,
        and return it as a pygame surface.
        """
        ...

    def on_key_down(self, key: int) -> None:
        """
        Optionally, implement logic via key presses directly
        Other methods like `on_key_up`, `on_mouse_down`, `on_mouse_up` and `on_mouse_motion` are also available.
        """
        ...
```

### Expose it

Expose an entrypoint under the `dweam` namespace group with the name `game`.

#### Using Poetry

<details>
<summary>Setting up Poetry</summary>

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Initialize a new project: `poetry init`
3. Add `dweam` to your dependencies: `poetry add dweam`

</details>

Add a `[tool.poetry.plugins."dweam"]` section to your `pyproject.toml` file, 
with the module path to your `Game` subclass.

```toml
[tool.poetry.plugins."dweam"]
game = "my_game.dweam_game:MyGame"
```

#### Using `uv`

Add the module path to your `Game` subclass to the `entry_points` section in your `pyproject.toml` file.

```toml
[project.entry-points."dweam"]
game = "my_game.dweam_game:MyGame"
```

<sub>(we haven't tested this but it should work, please [open an issue](https://github.com/dweam-team/dweamworld/issues/new) to let us know if it does or doesn't)</sub>

#### Using `setuptools`

Add the module path to your `Game` subclass to the `entry_points` section in your `setup.py` file.

```python
entry_points={
    "dweam": ["game = my_game.dweam_game:MyGame"]
}
```

<sub>(we haven't tested this but it should work, please [open an issue](https://github.com/dweam-team/dweamworld/issues/new) to let us know if it does or doesn't)</sub>

### Share it

Working on a simpler way, but for now we're collecting them in the [`pyproject.toml` file](pyproject.toml).

Create a repo on GitHub, push the code and a branch/tag, then add it to the requirements like:

```
[tool.poetry.dependencies]
...
diamond_atari = { git = "https://github.com/dweam-team/diamond", branch = "main" }
```

Please feel free to [edit the `pyproject.toml` file](https://github.com/dweam-team/dweamworld/edit/main/pyproject.toml) to add your game to the list! ^w^
