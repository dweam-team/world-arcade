import { useEffect, useRef, useState } from 'react';
import { api } from '../../lib/api';

interface GameViewReactProps {
  gameType: string;
  gameId: string;
}

export default function GameViewReact({ gameType, gameId }: GameViewReactProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playOverlayRef = useRef<HTMLDivElement>(null);
  const [isPointerLocked, setIsPointerLocked] = useState(false);
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const heartbeatIntervalRef = useRef<number | null>(null);

  const cleanup = () => {
    console.log('Cleaning up game view...');
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }
    
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }

    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      videoRef.current.srcObject = null;
    }
    
    setConnectionState('disconnected');
    window.dispatchEvent(new CustomEvent('gameSessionEnd'));
  };

  const startPlayback = async () => {
    if (connectionState === 'connecting') return;
    
    setConnectionState('connecting');

    let iceServers: RTCIceServer[] = [];
    
    try {
      const turnCredentials = await api.getTurnCredentials();
      if (turnCredentials) {
        iceServers = [
          {
            urls: turnCredentials.stun_urls,
            username: turnCredentials.username,
            credential: turnCredentials.credential
          },
          {
            urls: turnCredentials.turn_urls,
            username: turnCredentials.username,
            credential: turnCredentials.credential
          }
        ];
      }
    } catch (error) {
      console.log('Running in local mode without TURN server');
    }

    pcRef.current = new RTCPeerConnection({ iceServers });
    const pc = pcRef.current;

    dataChannelRef.current = pc.createDataChannel('controls');
    const dataChannel = dataChannelRef.current;

    pc.addTransceiver('video', { direction: 'recvonly' });

    dataChannel.onopen = () => {
      heartbeatIntervalRef.current = window.setInterval(() => {
        if (dataChannel?.readyState === 'open') {
          dataChannel.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 1000);
    };

    pc.ontrack = (event) => {
      if (event.streams?.[0] && videoRef.current) {
        videoRef.current.srcObject = event.streams[0];
        videoRef.current.onloadeddata = () => {
          setConnectionState('connected');
        };
      }
    };

    pc.oniceconnectionstatechange = () => {
      if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'closed') {
        cleanup();
      }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    try {
      const response = await api.createOffer(gameType, gameId, {
        sdp: pc.localDescription!.sdp,
        type: pc.localDescription!.type
      });

      if (response.ok) {
        const answer = await response.json();
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
        
        window.dispatchEvent(new CustomEvent('gameSessionReady', {
          detail: { sessionId: answer.sessionId }
        }));
      } else {
        cleanup();
        throw new Error('Failed to fetch answer');
      }
    } catch (error) {
      console.error('Connection failed:', error);
      cleanup();
    }
  };

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        document.exitPointerLock();
      }
      
      if (isPointerLocked && ['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.code)) {
        event.preventDefault();
      }

      if (dataChannelRef.current?.readyState === 'open') {
        dataChannelRef.current.send(JSON.stringify({
          type: 'keydown',
          key: event.keyCode
        }));
      }
    };

    const handleKeyup = (event: KeyboardEvent) => {
      if (dataChannelRef.current?.readyState === 'open') {
        dataChannelRef.current.send(JSON.stringify({
          type: 'keyup',
          key: event.keyCode
        }));
      }
    };

    const handleMouseMove = (event: MouseEvent) => {
      if (isPointerLocked && dataChannelRef.current?.readyState === 'open') {
        dataChannelRef.current.send(JSON.stringify({
          type: 'mousemove',
          movementX: event.movementX,
          movementY: event.movementY
        }));
      }
    };

    const handleMouseDown = (event: MouseEvent) => {
      if (isPointerLocked && dataChannelRef.current?.readyState === 'open') {
        dataChannelRef.current.send(JSON.stringify({
          type: 'mousedown',
          button: event.button
        }));
      }
    };

    const handleMouseUp = (event: MouseEvent) => {
      if (isPointerLocked && dataChannelRef.current?.readyState === 'open') {
        dataChannelRef.current.send(JSON.stringify({
          type: 'mouseup',
          button: event.button
        }));
      }
    };

    const handlePointerLockChange = () => {
      setIsPointerLocked(document.pointerLockElement === videoRef.current);
    };

    document.addEventListener('keydown', handleKeydown);
    document.addEventListener('keyup', handleKeyup);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('pointerlockchange', handlePointerLockChange);

    return () => {
      cleanup();
      document.removeEventListener('keydown', handleKeydown);
      document.removeEventListener('keyup', handleKeyup);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('pointerlockchange', handlePointerLockChange);
    };
  }, [isPointerLocked, gameType, gameId]);

  return (
    <div className="flex-grow rounded-lg shadow-md overflow-hidden">
      <div className="w-full h-full relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-auto bg-black"
          onClick={() => videoRef.current?.requestPointerLock()}
        />
        {connectionState !== 'connected' && (
          <div 
            className={`absolute top-0 left-0 w-full h-full bg-black/50 text-white 
              flex items-center justify-center cursor-pointer text-5xl
              ${connectionState === 'connecting' ? 'loading-spinner' : 'play-icon'}`}
            onClick={() => startPlayback()}
          >
            {connectionState === 'disconnected' && '▶'}
          </div>
        )}
      </div>
    </div>
  );
} 