import { useStore } from '@nanostores/react';
import { games, isLoading } from '~/stores/gameStore';
import GameInfo from './GameInfo';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/navigation';
import './GameCarousel.css';

export default function GameCarouselReact() {
  const $games = useStore(games);
  const $isLoading = useStore(isLoading);

  // Check if there are any games by checking if any type has any games
  const hasGames = Object.values($games).some(typeGames => Object.keys(typeGames).length > 0);

  if (!hasGames) {
    if ($isLoading) {
      return <div className="text-center py-8">Loading games...</div>;
    } else {
      return <div className="text-center py-8">No games found</div>;
    }
  }

  return (
    <div className="carousel-container relative m-auto flex items-center justify-center max-w-4xl">
      <div className="swiper-button-prev"></div>
      <div className="swiper-button-next"></div>
      <Swiper
        modules={[Navigation]}
        loop={hasGames}
        navigation={{
          nextEl: '.swiper-button-next',
          prevEl: '.swiper-button-prev',
        }}
        className="w-full h-[56.25vw] max-h-[480px]"
      >
        {Object.entries($games).map(([type, gamesByType]) => 
          Object.entries(gamesByType).map(([id, game]) => (
            <SwiperSlide key={`${type}/${id}`}>
              <div className="relative game-container carousel-slide h-full">
                <a href={`/game/${type}/${id}`} className="block w-full h-full">
                  <video 
                    muted 
                    preload="metadata" 
                    className="w-full h-full object-cover"
                    loop
                    autoPlay
                  >
                    <source src={`/thumb/${type}/${id}.webm`} type="video/webm" />
                    <source src={`/thumb/${type}/${id}.mp4`} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                  <GameInfo game={game} />
                </a>
              </div>
            </SwiperSlide>
          ))
        )}
      </Swiper>
    </div>
  );
} 