import { atom } from 'nanostores';

export interface Game {
  id: string;
  name: string;
  type: string;
  title?: string;
  tags?: string[];
}

export const games = atom<Game[]>([]);
export const isLoading = atom<boolean>(true);


// Initialize store
export async function initializeStore() {
  try {
    const statusResponse = await fetch('/status');
    const status = await statusResponse.json();
    isLoading.set(status.is_loading);
    console.log('Status:', status);

    // Get initial games
    const gamesResponse = await fetch('/game_info');
    if (gamesResponse.ok) {
        const gamesData = await gamesResponse.json();
        if (Array.isArray(gamesData)) {
            console.log('Setting games:', gamesData);
            games.set(gamesData);
        }
    }
    

    if (status.is_loading) {
        startPolling();
    }
  } catch (error) {
    console.error('Error initializing store:', error);
    startPolling();
  }
}

function startPolling() {
  let pollInterval = setInterval(async () => {
    try {
      const statusResponse = await fetch('/status');
      const status = await statusResponse.json();
      isLoading.set(status.is_loading);
      const response = await fetch('/game_info');
      if (response.ok) {
        const gamesData = await response.json();
        if (Array.isArray(gamesData)) {
          games.set(gamesData);
        }
      }

      // Stop polling when status is running
      if (!status.is_loading) {
        clearInterval(pollInterval);
      }
    } catch (error) {
      console.error('Error polling:', error);
    }
  }, 500);
}

// Initialize store if we're in the browser
if (typeof window !== 'undefined') {
  initializeStore();
} 