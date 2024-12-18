import asyncio
from collections import defaultdict
import json
import os
import pathlib
import sys
import uuid
import yaml
from dweam.models import GameInfo, GitBranchSource, ParamsUpdate, PathSource, StatusResponse
from dweam.utils.turn import create_turn_credentials, get_turn_stun_urls
from pydantic import ValidationError
from typing_extensions import assert_never
from time import time
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional, Any

from structlog.stdlib import BoundLogger
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Path
from fastapi.responses import FileResponse, JSONResponse
from aiortc import RTCSessionDescription
import numpy as np
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dweam.log_config import get_logger
from dweam.utils.entrypoint import load_games, get_cache_dir
from dweam.worker import GameWorker
from contextlib import asynccontextmanager
from dweam.utils.venv import get_venv_path

log = get_logger()
is_loading = True
games: defaultdict[str, dict[str, GameInfo]] = defaultdict(dict)

def _load_games():
    global games
    global is_loading
    venv_path = get_venv_path(log)
    load_games(log, venv_path, games)
    is_loading = False

game_loading_thread = None

def logger_dependency() -> BoundLogger:
    global log
    return log

@asynccontextmanager
async def lifespan(app: FastAPI):
    global game_loading_thread
    game_loading_thread = threading.Thread(target=_load_games)
    game_loading_thread.start()
    yield
    # Clean up active games on shutdown
    await asyncio.gather(*[worker.cleanup() for worker in active_workers.values()])
    active_workers.clear()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",    # Development frontend
        "http://localhost:8080",    # Development API
        "http://localhost",         # Production
        "http://127.0.0.1:4321",   # Alternative development frontend
        "http://127.0.0.1:8080",   # Alternative development API
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Global worker management
active_workers: dict[str, GameWorker] = {}

@app.get('/status')
async def status() -> StatusResponse:
    return StatusResponse(is_loading=is_loading)

# Endpoint to serve the entire games list
@app.get('/game_info')
async def get_games() -> dict[str, dict[str, GameInfo]]:
    return games

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

async def cleanup_worker(session_id: str, log: BoundLogger) -> None:
    """Clean up a game worker and its resources"""
    if session_id not in active_workers:
        log.warning("Received cleanup request for unknown session", session_id=session_id)
        return

    worker = active_workers[session_id]
    await worker.cleanup()
    active_workers.pop(session_id, None)

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

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    session_id = str(uuid.uuid4())[:8]
    log = log.bind(session_id=session_id)

    # Create and start game worker
    worker = GameWorker(
        log=log,
        game_info=game_info,
        session_id=session_id,
        game_type=type,
        game_id=id,
        venv_path=get_venv_path(log)
    )
    active_workers[session_id] = worker
    
    try:
        answer = await worker.run(offer)
    except Exception as e:
        log.exception("Error starting game worker")
        await cleanup_worker(session_id, log)
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={
        "sdp": answer.sdp,
        "type": answer.type,
        "sessionId": session_id
    })

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/turn-credentials")
async def turn_credentials(
    request: Request,
    log: BoundLogger = Depends(logger_dependency),
):
    turn_secret = os.environ.get('TURN_SECRET_KEY')
    if turn_secret is None:
        return {
            "username": "",
            "credential": "",
            "ttl": 86400,
            "turn_urls": [],
            "stun_urls": []  # No STUN needed for localhost
        }

    credentials = create_turn_credentials(turn_secret)
    turn_base_url = request.base_url.hostname
    turn_url, stun_url = get_turn_stun_urls(turn_base_url)

    return {
        **credentials,  # Include username, credential, ttl
        "turn_urls": [turn_url],
        "stun_urls": [stun_url]
    }

# Background cleanup task
async def cleanup_stale_workers() -> None:
    """Periodically check for and cleanup stale game workers"""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            stale_sessions = [
                session_id for session_id, worker in active_workers.items()
                if (datetime.now() - worker.last_heartbeat > timedelta(seconds=5) 
                    and not worker.cleanup_scheduled)
            ]
            
            for session_id in stale_sessions:
                log.info("Cleaning up stale game worker", session_id=session_id)
                await cleanup_worker(session_id, log)
                
        except Exception as e:
            log.error("Error in cleanup task", error=str(e))

@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(cleanup_stale_workers())

@app.get('/game/{type}/{id}/params/schema')
async def get_params_schema(
    type: str,
    id: str,
    log: BoundLogger = Depends(logger_dependency)
) -> dict:
    """Get JSON schema for game parameters"""
    game_info = games.get(type, {}).get(id)
    if not game_info:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Create a temporary worker to get the schema
    session_id = str(uuid.uuid4())[:8]
    worker = GameWorker(
        log=log,
        game_info=game_info,
        session_id=session_id,
        venv_path=get_venv_path(log),
        game_type=type,
        game_id=id
    )
    try:
        schema = await worker.get_params_schema()
        return schema
    finally:
        await worker.cleanup()

@app.post("/params/{session_id}")
async def update_game_params(
    request: Request,
    session_id: str = Path(...),
    log: BoundLogger = Depends(logger_dependency),
):
    worker = active_workers.get(session_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Game session not found")

    params = await request.json()
    
    try:
        # Send params to worker for validation and update
        await worker.update_params(params['params'])
        return {"status": "success"}
    except ValidationError as e:
        log.error("Invalid game parameters", 
                 session_id=session_id, 
                 error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("Error updating game parameters", 
                 session_id=session_id, 
                 error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/thumb/{type}/{id}.{ext}')
async def get_thumbnail(
    type: str,
    id: str,
    ext: str,
    log: BoundLogger = Depends(logger_dependency),
) -> FileResponse:
    """Serve thumbnail files from the package's thumbnail directory"""
    if type not in games:
        raise HTTPException(status_code=404, detail="Game type not found")
    if id not in games[type]:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_info = games[type][id]
    if not game_info._metadata:
        raise HTTPException(status_code=404, detail="Game metadata not found")
    
    # FIXME instead of packaging thumbnails into the module, 
    #  make it so that the worker doesn't need to download them as part of installation
    local_dir = game_info._metadata._module_dir
    if local_dir is None:
        raise HTTPException(status_code=404, detail="Package not installed")
    if not local_dir.exists():
        raise HTTPException(status_code=404, detail="Package not installed")
    
    thumbnail_dir = local_dir / game_info._metadata.thumbnail_dir
    if not thumbnail_dir.exists():
        raise HTTPException(status_code=404, detail="Thumbnail directory not found")
    
    filename = f"{id}.{ext}"
    thumbnail_path = thumbnail_dir / filename
    
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(thumbnail_path)

@app.get('/params/{session_id}/schema')
async def get_params_schema_by_session(
    session_id: str = Path(...),
    log: BoundLogger = Depends(logger_dependency),
) -> dict:
    """Get JSON schema for game parameters by session ID"""
    worker = active_workers.get(session_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    try:
        schema = await worker.get_params_schema()
        return schema
    except Exception as e:
        log.error("Error getting game parameters schema", 
                 session_id=session_id, 
                 error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
