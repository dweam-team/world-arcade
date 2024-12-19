import { useStore } from '@nanostores/react';
import { games, isLoading } from '~/stores/gameStore';
import { useEffect, useRef, useState } from 'react';
import GameInfo from './GameInfo';
import { api } from '~/lib/api';

export default function GameGridReact() {
  const $games = useStore(games);
  const $isLoading = useStore(isLoading);
  const searchInputRef = useRef<HTMLInputElement>(null);
  // Track which sections are expanded
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [initialized, setInitialized] = useState(false);
  
  useEffect(() => {
    if (!initialized && Object.keys($games).length > 0) {
      // Initial setup when games first load
      const newExpanded = Object.keys($games).reduce((acc, type) => {
        acc[type] = true;
        return acc;
      }, {} as Record<string, boolean>);
      setExpandedSections(newExpanded);
      setInitialized(true);
    }
  }, [$games, initialized]);

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

  // Check if there are any games by checking if any type has any games
  const hasGames = Object.values($games).some(typeGames => Object.keys(typeGames).length > 0);

  if (!hasGames) {
    if ($isLoading) {
      return <div className="text-center py-8">Loading games...</div>;
    } else {
      return <div className="text-center py-8">No games found</div>;
    }
  }

  const toggleSection = (type: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

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

      <div className="space-y-8">
        {Object.entries($games).map(([type, gamesByType]) => {
          const gamesCount = Object.keys(gamesByType).length;
          if (gamesCount === 0) return null;
          
          return (
            <div key={type} className="game-type-section">
              <button 
                onClick={() => toggleSection(type)}
                className="w-full text-left flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded-lg mb-4"
              >
                <h2 className="text-xl font-bold capitalize">
                  {type} ({gamesCount})
                </h2>
                <span className="transform transition-transform duration-200" style={{
                  transform: expandedSections[type] ? 'rotate(180deg)' : 'rotate(0deg)'
                }}>
                  ▼
                </span>
              </button>
              
              {expandedSections[type] && (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                  {Object.entries(gamesByType).map(([id, game]) => (
                    <div
                      key={`${type}/${id}`}
                      className="game-container relative rounded-lg shadow-md overflow-hidden"
                      data-gamename={game.title || id}
                    >
                      <a href={`/game/${type}/${id}`}>
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
                          <source src={api.getGameThumbUrl(type, id, 'webm')} type="video/webm" />
                          <source src={api.getGameThumbUrl(type, id, 'mp4')} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                        <GameInfo type={type} game={game} />
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
} 