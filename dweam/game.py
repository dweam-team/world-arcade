import asyncio
import threading
from typing import ClassVar, Protocol
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
import pygame
from structlog import BoundLogger
import torch

from dweam.models import GameInfo


class Game:
    game_info: ClassVar[GameInfo | list[GameInfo]]

    def __init__(
        self, 
        *,
        log: BoundLogger, 
        game: GameInfo,
        fps: int,
        device: torch.device,
    ):
        """Initialize game instance
        
        Args:
            log: Structured logger instance
            game_id: Specific game identifier (one of the ids from `game_info`)
            fps: Game's target FPS, managed by `pygame.time.Clock`
            size: Game's window size
            device: Device to run the game on
        """
        self.log = log
        self.game = game
        self.fps = fps
        self.device = device

        pygame.init()
        self.clock = pygame.time.Clock()

        self.keys_pressed: set[int] = set()
        self.mouse_pressed: set[int] = set()
        self.mouse_motion: tuple[int, int] = (0, 0)

        self.paused = False
        self.one_step_queued = False

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._frame_buffer: asyncio.Queue[pygame.Surface] = asyncio.Queue(maxsize=1)

    def step(self) -> pygame.Surface:
        """
        Render the next frame and handle game events, 
        using `self.keys_pressed`, `self.mouse_pressed` and `self.mouse_motion`
        """
        raise NotImplementedError
    
    def on_key_down(self, key: int) -> None:
        """
        Handle a key being pressed
        """
        pass

    def on_key_up(self, key: int) -> None:
        """
        Handle a key being released
        """
        pass

    def on_mouse_down(self, button: int) -> None:
        """
        Handle a mouse button being pressed
        """
        pass

    def on_mouse_up(self, button: int) -> None:
        """
        Handle a mouse button being released
        """
        pass

    def on_mouse_motion(self, motion: tuple[int, int]) -> None:
        """
        Handle mouse motion
        """
        pass

    def start(self) -> None:
        """
        Start the game in a new thread
        """
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._stop_event.clear()
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the game
        """
        self.log.debug("Stopping game thread", thread_id=self._thread)
        self._stop_event.set()
        # Wait for the thread to finish, 3s timeout
        if self._thread is None:
            return  
        self.log.debug("Joining game thread", thread_id=self._thread.ident)
        self._thread.join(timeout=3.0)
        if not self._thread.is_alive():
            self._thread = None
            return
        self.log.warning("Game thread did not finish in 3s; thread is still running", 
                         thread_id=self._thread.ident)
        self._thread = None

    def run(self) -> None:
        """
        Main game loop, runs in a separate thread
        """
        # pygame.init()

        while not self._stop_event.is_set():
            mouse_x, mouse_y = 0, 0
            pygame.event.pump()

            for event in pygame.event.get():
                if event.type == pygame.MOUSEMOTION:
                    mouse_x += event.rel[0]
                    mouse_y += event.rel[1]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in self.mouse_pressed:
                        continue
                    self.on_mouse_down(event.button)
                    self.mouse_pressed.add(event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button not in self.mouse_pressed:
                        continue
                    self.mouse_pressed.remove(event.button)
                    self.on_mouse_up(event.button)
                elif event.type == pygame.KEYDOWN:
                    if event.key in self.keys_pressed:
                        continue
                    self.keys_pressed.add(event.key)
                    self.on_key_down(event.key)
                elif event.type == pygame.KEYUP:
                    if event.key not in self.keys_pressed:
                        continue
                    self.keys_pressed.remove(event.key)
                    self.on_key_up(event.key)
            
            self.mouse_motion = (mouse_x, mouse_y)
            if self.mouse_motion != (0, 0):
                self.on_mouse_motion(self.mouse_motion)

            if not self.paused and not self.one_step_queued:
                surface = self.step()
                
                # Put new frame in buffer
                while not self._frame_buffer.empty():
                    self._frame_buffer.get_nowait()
                self._frame_buffer.put_nowait(surface)
            self.one_step_queued = False

            self.clock.tick(self.fps)

        # pygame.quit()

    def do_one_step(self) -> None:
        """
        When paused, perform a single step once
        """
        self.one_step_queued = True

    async def get_next_frame(self) -> pygame.Surface:
        return await self._frame_buffer.get()
