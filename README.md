# ☁️ Dweamworld

[![Discord](https://img.shields.io/badge/Join%20our%20Discord-purple)](https://discord.gg/aY3GAqMqBf) [![Windows Application](https://img.shields.io/badge/Windows%20Application-grey)](https://github.com/dweam-team/dweamworld-internal/actions/runs/12452479607/artifacts/2353039390)

Fully generative games are here! You can now play these interactive video models at home using consumer hardware, with Dweamworld.

Dweamworld is an open-source platform where users can easily find, access and play these games locally, or stream them from a server. 

Currently, the models are hard to find: dispersed across Github, Hugging Face and various social media apps. Even when you find one, it takes technical knowledge and time to download and run them. 

So we're bringing them all together, for you to play.

## Features

- **Browse open source game models**
     
     Collecting together all the available games made open source by [Diamond](https://github.com/eloialonso/diamond), [Decart](https://github.com/XmYx/open-oasis) and other world creators!
  
<img src="https://github.com/user-attachments/assets/297dcd2a-373a-42d0-9296-33b781244a6a" width="1000"/>
<br> </br>

- **Play Games**

    Jump into CS:GO, Atari Games, Minecraft or Mario Kart. We are also the first platform to support Yume Nikki.

<img src="https://github.com/user-attachments/assets/5d2941ab-4373-49bc-bf2c-8fe5bf5fba86" height="335"/> <img src="https://github.com/user-attachments/assets/9e21dbb0-1d39-4b6c-963c-0f5cf3cd2dc7" height="334"/>


- **Change Parameters**

   Adjust settings to allow higher FPS on lower end GPUs (at the expense of game stability/quality) and toggle an AI player on/off.

<img src="https://github.com/user-attachments/assets/9e0b8c55-b846-41fd-89bc-2c948b938797" width="600"/>

## Requirements
- An NVIDIA GPU (ideally >8GB VRAM)
- OS: Windows (exe) or Linux (see [Linux Setup](#setup-for-linux-or-server))

Not supported but coming soon:
- [ ] Mac
- [ ] AMD GPU

## Quick Setup (for Windows)

1. Download the [Dweamworld Installer](https://github.com/dweam-team/dweamworld-internal/actions/runs/12452479607/artifacts/2353039390).
2. Unzip the file using [7Zip](https://www.7-zip.org/).
3. Click dweam.exe and start playing!

<img src="https://github.com/user-attachments/assets/a665618f-693c-4ee0-af9d-f5e653637d96" width="500"/>

## Setup For Linux or Server

### Prerequisites

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

We are working on a simpler way, but for now we're collecting them in the [`pyproject.toml` file](pyproject.toml).

Create a repo on GitHub, push the code and a branch/tag, then add it to the requirements like:

```
[tool.poetry.dependencies]
...
diamond_atari = { git = "https://github.com/dweam-team/diamond", branch = "main" }
```

Please feel free to [edit the `pyproject.toml` file](https://github.com/dweam-team/dweamworld/edit/main/pyproject.toml) to add your game to the list! ^w^

## Get Involved

We welcome contributions from the community!

Either add an issue here on Github, or join our [discord](https://discord.gg/aY3GAqMqBf) to chat with the team and other users. Remember to star this repository :star:.
