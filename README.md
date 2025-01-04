# ☁️ World Arcade

[![Discord](https://img.shields.io/badge/Join%20our%20Discord-purple)](https://discord.gg/aY3GAqMqBf) [![Windows Application](https://img.shields.io/badge/Windows%20Application-grey)](https://github.com/dweam-team/world-arcade/releases)

Run generative games on your own GPU.

Unlike traditional games, that run on a deterministic game engine, generative games use an interactive video model to generate every frame of the game in real-time, reacting to your button presses.

Currently, the models are dispersed across Github and hard to find. Even when you find one, it takes technical knowledge and time to run them yourself. So we're bringing them together for you to play.

World Arcade is an open-source platform that makes it easy to play them locally, or stream from a server. 

## Features

- **Browse open-source game models**
     
     Collecting together all the available games made open-source by [Diamond](https://github.com/eloialonso/diamond) and other world creators!
  
<img src="https://github.com/user-attachments/assets/18c5949d-5dc6-4068-a253-d0015ecea0d9" width="800"/>
<br> </br>

- **Play Games**

    Jump into Yume Nikki, CS:GO, Minecraft, Atari Arcade Games or Mario Kart 64.

<img src="https://github.com/user-attachments/assets/700d205e-d337-4cf2-bcf7-163b148f4b03" width="407"/> <img src="https://github.com/user-attachments/assets/0e50a802-1369-4ebb-9632-e11b9032f78f" width="393"/>
<br> </br>

- **Change Parameters**

   Adjust settings to allow higher FPS on lower-end GPUs (at the expense of game stability/quality).

<img src="https://github.com/user-attachments/assets/0d643748-0414-4b30-b5f6-bc36f1491f19" width="800"/>
<br> </br>

## Requirements

- An NVIDIA GPU (ideally >8GB VRAM)
- OS: Windows (via exe, see [Windows Setup](#Windows)) or Linux (via Docker, see [Linux Setup](#Linux))

The Minecraft games are only supported on Linux; you can use [WSL](https://docs.microsoft.com/en-us/windows/wsl/install) on Windows to play them.

## Let's Play!

### Windows

1. Download dweam-windows.zip from the [latest release](https://github.com/dweam-team/world-arcade/releases).
2. Unzip the file using [7Zip](https://www.7-zip.org/).
3. Double-click dweam.exe, wait for the games to install, and start playing!

<img src="https://github.com/user-attachments/assets/79378c28-5e48-46fe-b6df-770bc4c79068" width="800"/>

### Linux

#### Installing

Install and run [Docker](https://www.docker.com/),

Install [Docker compose](https://docs.docker.com/compose/install/).

Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

#### Running

```
git clone ssh://git@github.com/dweam-team/world-arcade
cd world-arcade
docker compose up --build
```

Once it's running, visit [localhost:4321](http://localhost:4321).

#### Exposing to the internet/local network

If you're exposing the app to the internet, you should set a `TURN_SECRET_KEY` environment variable when running the app:

```
export TURN_SECRET_KEY=$(openssl rand -base64 32)
docker compose up --build
```

Forward the following ports:
- 4321 TCP (app)
- 3478 TCP/UDP (WebRTC)
- 5349 TCP/UDP (WebRTC)
- 50000-50010 UDP (WebRTC)

By default, the app only binds to `localhost`.
You may change this in the [`docker-compose.yaml`](docker-compose.yaml#L10-L11) file, 
but we suggest the use of a reverse proxy to expose port 4321 TCP.

For example, with [caddy](https://caddyserver.com/):

```
# Caddyfile

example.com {
        # Optionally add basic authentication
        basic_auth {
                [username] [password-hash]
        }

        reverse_proxy localhost:4321
}
```

## Adding a game

Each set of games is implemented as a standalone python package that:

1. Implements a `Game` class that subclasses `dweam.Game`.
2. Provides a `dweam.toml` file with the game's metadata.

See [diamond-yumenikki](https://github.com/dweam-team/diamond-yumenikki) or [diamond-csgo](https://github.com/dweam-team/diamond-csgo) for an example.

### Implement it

Subclass `dweam.Game`, and implement the `step` method.

```python
# my_game/dweam_game.py

from dweam import Game
import pygame


class MyGame(Game):
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

### Add Metadata

Add a `dweam.toml` file with the game's metadata.

```toml
# my_game/dweam.toml

type = "Awesome Games"
entrypoint = "my_game.dweam_game:MyGame"
repo_link = "https://github.com/awesome-games/my-game"

[games.my_game]
title = "My Game"
tags = ["First Person"]
description = "A game made by me"

[games.my_game.buttons]
"⬆️ Forward" = "W"
"⬇️ Back" = "S"
"⬅️ Left" = "A"
"➡️ Right" = "D"
"🆙 Jump" = "Space"
```

### Share it

For now we're hardcoding the game packages in the [`entrypoint.py`](dweam/utils/entrypoint.py#L30) file – please submit a pull request to add your game, in the form of a GitHub repo URL or python package.

Soon we'll make this a local configuration file ^w^"

## Get Involved

Love any contributions from the community!

Open a GitHub issue or join our [Discord server](https://discord.gg/aY3GAqMqBf) to chat.

Leave a star if you'd like to see this project grow! ❤️ ⭐️
