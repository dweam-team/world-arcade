import { atom } from 'nanostores';

export interface GameInfo {
  type: string;
  id: string;
  title: string | null;
  description: string | null;
  tags: string[] | null;
  author: string | null;
  build_date: string | null;
  repo_link: string | null;
  buttons: Record<string, string> | null;
}

export type GameStore = Record<string, Record<string, GameInfo>>;

export const games = atom<GameStore>({});
export const isLoading = atom<boolean>(true);

export interface ParamsSchema {
  schema: Record<string, any>;
  uiSchema: Record<string, any>;
}

export const paramsSchema = atom<ParamsSchema | null>(null);

// Initialize store
export async function initializeStore() {
  try {
    const statusResponse = await fetch('/status');
    const status = await statusResponse.json();
    isLoading.set(status.is_loading);

    // Get initial games
    const gamesResponse = await fetch('/game_info');
    if (gamesResponse.ok) {
      const gamesData = await gamesResponse.json();
      games.set(gamesData);
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
        games.set(gamesData);
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

// Listen for game session end to clear params schema
if (typeof window !== 'undefined') {
  window.addEventListener('gameSessionEnd', () => {
    paramsSchema.set(null);
  });
  
  initializeStore();
} 