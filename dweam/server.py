import asyncio
import json
import os
import uuid
import torch
from typing_extensions import assert_never
from time import time
import hmac
import hashlib
import base64
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any

from structlog.stdlib import BoundLogger
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Path
from fastapi.responses import JSONResponse
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceServer, RTCConfiguration
import numpy as np
from av.video.frame import VideoFrame
from av.frame import Frame
import pygame
from fastapi.staticfiles import StaticFiles
import yaml
from dweam.constants import JS_TO_PYGAME_KEY_MAP, JS_TO_PYGAME_BUTTON_MAP
from fastapi.middleware.cors import CORSMiddleware
from dweam.game import Game, GameInfo
from dweam.log_config import get_logger
from dweam.utils.entrypoint import load_games
from contextlib import asynccontextmanager

from dweam.utils.turn import create_turn_credentials

log = get_logger()
pcs = set()

# load game entrypoints
games = load_games(log)

def logger_dependency() -> BoundLogger:
    global log
    return log


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # Close peer connections on shutdown
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Development
        "http://localhost",       # Production
        # Add other allowed origins as needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Video stream track to capture Pygame output
class GameVideoTrack(VideoStreamTrack):
    """
    A video stream track that captures frames from a Pygame application.
    """
    def __init__(self, game: Game):
        super().__init__()
        self.game = game

    async def recv(self) -> Frame:
        # Control frame rate
        # TODO don't hardcode 30 FPS
        await asyncio.sleep(1 / 30)  # 30 FPS

        # Capture the frame from Pygame
        # TODO allow numpy arrays/PIL images directly
        surface = await self.game.get_next_frame()
        frame = pygame.surfarray.array3d(surface)
        frame = np.fliplr(frame)
        frame = np.rot90(frame)
        new_frame = VideoFrame.from_ndarray(frame, format='rgb24')

        # Assign timestamp
        new_frame.pts, new_frame.time_base = await self.next_timestamp()
        return new_frame


# Endpoint to serve the entire games list
@app.get('/game_info')
async def get_games() -> list[GameInfo]:
    return list(game 
                for game_list in games.values() 
                for game in game_list.values())

# Endpoint to serve the entire games list
@app.get('/game_info/{type}')
async def get_games_by_type(type: str) -> list[GameInfo]:
    if type not in games:
        raise HTTPException(status_code=404, detail="Game type not found")
    return list(games[type].values())


# Endpoint to serve a singular game based on query parameter
@app.get('/game_info/{type}/{id}')
async def get_game(type: str, id: str) -> GameInfo:
    if type not in games:
        raise HTTPException(status_code=404, detail="Game type not found")
    if id not in games[type]:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[type][id]


@dataclass
class GameHeartbeat:
    """Tracks when a game was last active"""
    game: Game
    last_heartbeat: datetime
    peer_connection: RTCPeerConnection
    cleanup_scheduled: bool = False

    @property
    def is_stale(self) -> bool:
        """Check if the session hasn't received a heartbeat recently"""
        return datetime.now() - self.last_heartbeat > timedelta(seconds=5)

# Global session management
active_games: dict[str, GameHeartbeat] = {}

async def cleanup_game(session_id: str, log: BoundLogger) -> None:
    """Clean up a game and its resources"""
    if session_id not in active_games:
        log.warning("Received cleanup request for unknown session", 
                    session_id=session_id)
        return

    heartbeat = active_games[session_id]
    if heartbeat.cleanup_scheduled:
        return
    
    heartbeat.cleanup_scheduled = True
    log.info("Cleaning up game", session_id=session_id)
    
    try:
        heartbeat.game.stop()  # Uses Game's built-in stop method
        if heartbeat.peer_connection.connectionState != "closed":
            await asyncio.wait_for(heartbeat.peer_connection.close(), timeout=3.0)
    except Exception as e:
        log.error("Error during game cleanup", 
                 session_id=session_id, 
                 error=str(e))
    finally:
        active_games.pop(session_id, None)
        pcs.discard(heartbeat.peer_connection)
        log.debug("Removed peer connection", session_id=session_id)

# WebRTC server endpoint
@app.post("/offer/{type}/{id}")
async def offer(
    request: Request,
    type: str = Path(...),
    id: str = Path(...),
    log: BoundLogger = Depends(logger_dependency),
):
    if type not in games:
        raise HTTPException(status_code=404, detail="Game type not found")
    if id not in games[type]:
        raise HTTPException(status_code=404, detail="Game not found")
    game_info = games[type][id]
    if game_info._implementation is None:
        log.error("Game implementation not found", type=type, id=id)
        raise HTTPException(status_code=500, detail="Game implementation not found")

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # Generate temporary credentials same as /turn-credentials endpoint
    turn_credentials = create_turn_credentials(os.environ['TURN_SECRET_KEY'])
    username = turn_credentials["username"]
    password = turn_credentials["credential"]

    # Use the same URL for both STUN and TURN
    turn_base_url = os.environ.get('INTERNAL_TURN_URL', 'localhost:3478')
    turn_url = f'turn:{turn_base_url}'
    stun_url = f'stun:{turn_base_url}'
    ice_servers = [
        RTCIceServer(
            urls=[stun_url],
            username=username,
            credential=password
        ),
        RTCIceServer(
            urls=[turn_url],
            username=username,
            credential=password
        )
    ]
    config = RTCConfiguration(iceServers=ice_servers)
    pc = RTCPeerConnection(configuration=config)
    session_id = str(uuid.uuid4())[:8]
    log = log.bind(session_id=session_id)

    device = torch.device("cuda" if torch.cuda.is_available() else 
                          "mps" if torch.backends.mps.is_available() else 
                          "cpu")

    game_app = game_info._implementation(
        log=log,
        game=game_info,
        fps=30,  # TODO unhardcode
        device=device,
    )
    
    # Start the game using its built-in method
    game_app.start()
    
    heartbeat = GameHeartbeat(
        game=game_app,
        peer_connection=pc,
        last_heartbeat=datetime.now()
    )
    active_games[session_id] = heartbeat
    pcs.add(pc)  # Keep this for backward compatibility

    # Add Pygame video track to the peer connection
    log.debug("Adding video track to peer connection")
    pc.addTrack(GameVideoTrack(game_app))

    # Handle data channel for controls
    @pc.on("datachannel")
    def on_datachannel(channel):
        log.debug("Data channel opened", channel=channel.label)
        
        @channel.on("message")
        async def on_message(message):
            if session_id not in active_games:
                log.warning("Received message for inactive session", 
                            session_id=session_id)
                return
                
            data = json.loads(message)
            if data['type'] == 'heartbeat':
                active_games[session_id].last_heartbeat = datetime.now()
            else:
                handle_game_input(log, data)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log.debug("Connection state change", 
                 state=pc.connectionState, 
                 session_id=session_id)
                 
        if pc.connectionState in ("failed", "closed"):
            await cleanup_game(session_id, log)

    # Set remote description and create answer
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()

    # Log the SDP answer before setting it
    log.debug("Generated SDP answer", sdp=answer.sdp)

    await pc.setLocalDescription(answer)

    # Return the answer
    return JSONResponse(content={
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/turn-credentials")
async def get_turn_credentials(request: Request):
    # Get credentials from environment variables
    turn_credentials = create_turn_credentials(os.environ['TURN_SECRET_KEY'])

    url = request.base_url.hostname
    turn_url = f"turn:{url}:3478"
    stun_url = f"stun:{url}:3478"
    
    return {
        "username": turn_credentials["username"],
        "credential": turn_credentials["credential"],
        "ttl": turn_credentials["ttl"],
        "turn_urls": [turn_url],
        "stun_urls": [stun_url]
    }

# Background cleanup task
async def cleanup_stale_sessions() -> None:
    """Periodically check for and cleanup stale games"""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            stale_sessions = [
                session_id for session_id, heartbeat in active_games.items()
                if heartbeat.is_stale and not heartbeat.cleanup_scheduled
            ]
            
            for session_id in stale_sessions:
                log.info("Cleaning up stale game", session_id=session_id)
                await cleanup_game(session_id, log)
                
        except Exception as e:
            log.error("Error in cleanup task", error=str(e))

@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(cleanup_stale_sessions())

# Move input handling to a separate function
def handle_game_input(log: BoundLogger, data: dict) -> None:
    """Handle game input events
    
    Args:
        data: The input event data
        game_app: The game instance
        log: Logger instance
    """
    # TODO instead of statically pushing inputs via pygame.event.post, 
    #  stick them in the game app's input queue (implement it first)
    if data['type'] == 'keydown':
        pygame_key = JS_TO_PYGAME_KEY_MAP.get(data['key'])
        if pygame_key is not None:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame_key))
        else:
            log.warning("Unmapped key code", key=data['key'])
    elif data['type'] == 'keyup':
        pygame_key = JS_TO_PYGAME_KEY_MAP.get(data['key'])
        if pygame_key is not None:
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame_key))
    elif data['type'] == 'mousemove':
        # Create a pygame MOUSEMOTION event
        movement = (data['movementX'], data['movementY'])
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, rel=movement))
    elif data['type'] == 'mousedown':
        # Map JavaScript mouse button to Pygame button
        pygame_button = JS_TO_PYGAME_BUTTON_MAP.get(data['button'])
        if pygame_button is not None:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame_button))
        else:
            log.warning("Unmapped mouse button", button=data['button'])
    elif data['type'] == 'mouseup':
        pygame_button = JS_TO_PYGAME_BUTTON_MAP.get(data['button'])
        if pygame_button is not None:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame_button))
        else:
            log.warning("Unmapped mouse button", button=data['button'])
    else:
        log.error("Unknown message type", type=data['type'])
        raise ValueError(f"Unknown message type: {data['type']}")
