import type { CSSProperties } from 'react';
import type { GameInfo as GameInfoType } from '~/stores/gameStore';
import { useEffect } from 'react';

interface GameInfoProps {
  type: string;
  game: GameInfoType;
}

// Define styles as a CSS-in-JS object
const styles = {
  gameInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    width: '100%',
    background: 'rgba(0, 0, 0, 0.8)',
    color: '#fff',
    padding: '12px',
    transform: 'translateY(calc(100% - 50px))',
    transition: 'transform 0.3s ease',
    pointerEvents: 'none',
  } satisfies CSSProperties,

  gameName: {
    fontSize: '1.2rem',
    textAlign: 'left',
    margin: 0,
    fontWeight: 'bold',
    lineHeight: 1.2,
    overflowWrap: 'break-word',
  } satisfies CSSProperties,

  gameTags: {
    fontSize: '0.875rem',
    textAlign: 'left',
    marginTop: '8px',
    opacity: 0,
    transition: 'opacity 0.3s ease',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  } satisfies CSSProperties,

  tag: {
    background: 'rgba(255, 255, 255, 0.3)',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '0.75rem',
    backdropFilter: 'blur(4px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    color: '#ffffff',
    fontWeight: 500,
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
  } satisfies CSSProperties,

  typeTag: {
    background: 'rgba(255, 165, 0, 0.3)',
    boxShadow: '0 0 8px rgba(255, 165, 0, 0.2)',
    borderColor: 'rgba(255, 165, 0, 0.4)',
  } satisfies CSSProperties,
} as const;

export default function GameInfo({ type, game }: GameInfoProps) {
  // Add styles to document when component mounts
  useEffect(() => {
    const styleId = 'game-info-styles';
    
    // Only add if not already present
    if (!document.getElementById(styleId)) {
      const styleSheet = document.createElement('style');
      styleSheet.id = styleId;
      styleSheet.textContent = `
        .carousel-slide .game-info {
          transform: translateY(calc(100% - 70px)) !important;
        }
        
        .game-container:hover .game-info {
          transform: translateY(0) !important;
        }
        
        .carousel-slide .game-name {
          font-size: 2rem !important;
        }
        
        .game-container:hover .game-tags {
          opacity: 1 !important;
          transition-delay: 0.1s !important;
        }
      `;
      document.head.appendChild(styleSheet);
    }

    // Cleanup not strictly necessary but good practice
    return () => {
      // Don't remove on unmount as other components might need these styles
    };
  }, []);

  return (
    <div style={styles.gameInfo} className="game-info">
      <h2 style={styles.gameName} className="game-name">{game.title || game.id}</h2>
      <div style={styles.gameTags} className="game-tags">
        {type && (
          <span style={{ ...styles.tag, ...styles.typeTag }}>{type}</span>
        )}
        {game.tags?.map((tag) => (
          <span key={tag} style={styles.tag}>{tag}</span>
        ))}
      </div>
    </div>
  );
} 