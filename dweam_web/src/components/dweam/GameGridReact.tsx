import { useStore } from '@nanostores/react';
import { games, isLoading } from '~/stores/gameStore';
import { useEffect, useRef } from 'react';
import GameInfo from './GameInfo';

export default function GameGridReact() {
  const gamesList = useStore(games);
  const $isLoading = useStore(isLoading);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleSearch = () => {
      const query = searchInputRef.current?.value.toLowerCase() || '';
      const containers = document.querySelectorAll<HTMLElement>('.game-container');
      
      containers.forEach(container => {
        const gameName = container.dataset.gamename;
        if (!gameName) return;
        
        container.style.display = gameName.toLowerCase().includes(query) ? '' : 'none';
      });
    };

    searchInputRef.current?.addEventListener('input', handleSearch);
    return () => {
      searchInputRef.current?.removeEventListener('input', handleSearch);
    };
  }, []);

  // Return loading state for both SSR and initial client render
  if (gamesList.length === 0) {
    if ($isLoading) {
      return <div className="text-center py-8">Loading games...</div>;
    } else {
      return <div className="text-center py-8">No games found</div>;
    }
  }

  return (
    <div className="container mx-auto px-4">
      <div className="mb-6">
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Search games..."
          className="w-full max-w-md border border-gray-800 dark:border-gray-300 rounded px-4 py-2 bg-white text-black dark:bg-gray-800 dark:text-white mx-auto block"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {gamesList.map(game => (
          <div
            key={game.id}
            className="game-container relative rounded-lg shadow-md overflow-hidden"
            data-gamename={game.title || game.name || game.id}
          >
            <a href={`/game/${game.type}/${game.id}`}>
              <video
                muted
                preload="metadata"
                className="w-full h-64 object-cover video-thumb"
                onMouseEnter={e => e.currentTarget.play()}
                onMouseLeave={e => {
                  e.currentTarget.pause();
                  e.currentTarget.currentTime = 0;
                }}
              >
                <source src={`/thumbnails/${game.type}_${game.id}.webm`} type="video/webm" />
                <source src={`/thumbnails/${game.type}_${game.id}.mp4`} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
              <GameInfo game={game} />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
} 