import { useStore } from '@nanostores/react';
import { games } from '~/stores/gameStore';
import GameInfo from './GameInfo';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/navigation';
import './GameCarousel.css';

export default function GameCarouselReact() {
  const $games = useStore(games);

  // Show loading state for both SSR and initial client render
  if ($games.length === 0) {
    return <div className="text-center py-8">Loading games...</div>;
  }

  // Sort games to ensure CS:GO is first, but only if it exists
  const sortedGames = [...$games];
  const csgoIndex = sortedGames.findIndex(game => game.id.toLowerCase() === 'csgo');
  if (csgoIndex > -1) {
    const csgoGame = sortedGames.splice(csgoIndex, 1)[0];
    sortedGames.unshift(csgoGame);
  }

  return (
    <div className="carousel-container relative m-auto flex items-center justify-center max-w-4xl">
      <div className="swiper-button-prev"></div>
      <div className="swiper-button-next"></div>
      <Swiper
        modules={[Navigation]}
        loop={sortedGames.length > 1}
        navigation={{
          nextEl: '.swiper-button-next',
          prevEl: '.swiper-button-prev',
        }}
        className="w-full h-[56.25vw] max-h-[480px]"
      >
        {sortedGames.map(game => (
          <SwiperSlide key={`${game.type}/${game.id}`}>
            <div className="relative game-container carousel-slide h-full">
              <a href={`/game/${game.type}/${game.id}`} className="block w-full h-full">
                <video 
                  muted 
                  preload="metadata" 
                  className="w-full h-full object-cover"
                  loop
                  autoPlay
                >
                  <source src={`/thumbnails/${game.type}_${game.id}.webm`} type="video/webm" />
                  <source src={`/thumbnails/${game.type}_${game.id}.mp4`} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
                <GameInfo game={game} />
              </a>
            </div>
          </SwiperSlide>
        ))}
      </Swiper>
    </div>
  );
} 