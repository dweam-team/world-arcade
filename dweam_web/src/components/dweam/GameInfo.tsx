import pkg from 'react';
const {CSSProperties} = pkg;

interface GameInfoProps {
  game: {
    id: string;
    name: string;
    type?: string;
    tags?: string[];
    title?: string;
  };
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
  } as CSSProperties,

  gameName: {
    fontSize: '1.2rem',
    textAlign: 'left',
    margin: 0,
    fontWeight: 'bold',
    lineHeight: 1.2,
    overflowWrap: 'break-word',
  } as CSSProperties,

  gameTags: {
    fontSize: '0.875rem',
    textAlign: 'left',
    marginTop: '8px',
    opacity: 0,
    transition: 'opacity 0.3s ease',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  } as CSSProperties,

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
  } as CSSProperties,

  typeTag: {
    background: 'rgba(255, 165, 0, 0.1)',
  } as CSSProperties,
} as const;

// Add global styles to handle hover states
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
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

export default function GameInfo({ game }: GameInfoProps) {
  return (
    <div style={styles.gameInfo} className="game-info">
      <h2 style={styles.gameName} className="game-name">{game.title || game.id}</h2>
      <div style={styles.gameTags} className="game-tags">
        {game.type && (
          <span style={{ ...styles.tag, ...styles.typeTag }}>{game.type}</span>
        )}
        {game.tags?.map((tag) => (
          <span key={tag} style={styles.tag}>{tag}</span>
        ))}
      </div>
    </div>
  );
} 