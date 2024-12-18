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
    console.log('Cleanup completed');
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
      document.removeEventListener('keydown', handleKeydown);
      document.removeEventListener('keyup', handleKeyup);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('pointerlockchange', handlePointerLockChange);
    };
  }, [isPointerLocked]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const startPlayback = async () => {
    if (connectionState === 'connecting') return;
    
    setConnectionState('connecting');

    let iceServers: RTCIceServer[] = [];
    
    const turnCredentials = await api.getTurnCredentials();
    if (turnCredentials.turn_urls.length > 0 || turnCredentials.stun_urls.length > 0) {
      // Production mode with ICE servers
      if (turnCredentials.turn_urls.length > 0) {
        iceServers.push({
          urls: turnCredentials.turn_urls,
          username: turnCredentials.username,
          credential: turnCredentials.credential
        });
      }
      if (turnCredentials.stun_urls.length > 0) {
        iceServers.push({
          urls: turnCredentials.stun_urls
        });
      }
    } else {
      console.log('Running in local mode without ICE servers');
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
      console.log('Received track:', event);
      const track = event.track;
      console.log('Track state:', track.readyState);
      
      if (event.streams?.[0] && videoRef.current) {
        videoRef.current.srcObject = event.streams[0];
        console.log('Video stream set to video element.');
        
        videoRef.current.onloadeddata = () => {
          console.log('First frame received, video ready to play');
          setConnectionState('connected');
        };
      } else {
        console.error('No streams found in the track event.');
      }
    };

    pc.oniceconnectionstatechange = () => {
      console.log('ICE Connection State:', pc.iceConnectionState);
      if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'closed') {
        cleanup();
      }
    };

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        console.log('New ICE candidate:', event.candidate);
      } else {
        console.log('All ICE candidates have been sent.');
      }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    try {
      const response = await api.createOffer(gameType, gameId, {
        sdp: pc.localDescription!.sdp,
        type: pc.localDescription!.type
      });

      const answer = response;
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
      
      window.dispatchEvent(new CustomEvent('gameSessionReady', {
        detail: { sessionId: answer.sessionId }
      }));
    } catch (error) {
      console.error('Connection failed:', error);
      cleanup();
    }
  };

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
            ref={playOverlayRef}
            className="absolute top-0 left-0 w-full h-full bg-black/50 text-white 
              flex items-center justify-center cursor-pointer text-5xl"
            onClick={() => startPlayback()}
          >
            {connectionState === 'connecting' ? (
              <div className="w-10 h-10 border-4 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '▶'
            )}
          </div>
        )}
      </div>
    </div>
  );
} 