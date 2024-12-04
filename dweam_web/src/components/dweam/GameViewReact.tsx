import { useEffect, useRef, useState } from 'react';

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
  const sessionIdRef = useRef<string | null>(null);

  // ... Rest of the game logic moved from GameView.astro, 
  // but using the refs and state instead of direct DOM manipulation

  return (
    <div className="flex-grow rounded-lg shadow-md overflow-hidden">
      <div id="videoContainer" className="w-full h-full relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-auto bg-black"
          onClick={() => videoRef.current?.requestPointerLock()}
        />
        <div 
          ref={playOverlayRef}
          className={`absolute top-0 left-0 w-full h-full bg-black/50 text-white 
            flex items-center justify-center cursor-pointer text-5xl
            ${connectionState === 'connecting' ? 'loading-spinner' : 'play-icon'}`}
          onClick={startPlayback}
        >
          {connectionState === 'disconnected' && '▶'}
          {connectionState === 'connecting' && ''}
        </div>
      </div>
    </div>
  );
} 