const getBaseUrl = () => {
  // In SSR context, use the environment variable
  if (typeof window === 'undefined') {
    // console.log('[API] SSR context, using process.env.INTERNAL_BACKEND_URL:', process.env.INTERNAL_BACKEND_URL);
    return process.env.INTERNAL_BACKEND_URL || 'http://localhost:8080';
  }
  
  // Check if we're in development mode (Astro dev server)
  const isDev = import.meta.env.DEV;
  if (isDev) {
    // console.log('[API] Development mode, using empty base URL (proxy)');
    return '';
  }

  // In production client-side context, use the backend URL from the environment
  if ((window as any)._env_?.INTERNAL_BACKEND_URL) {
    // console.log('[API] Production client context, using window._env_.INTERNAL_BACKEND_URL:', (window as any)._env_.INTERNAL_BACKEND_URL);
    return (window as any)._env_.INTERNAL_BACKEND_URL;
  }
  
  // Fallback for production without env
  // console.log('[API] Using fallback localhost URL');
  return 'http://localhost:8080';
};

type RequestOptions = RequestInit & {
  params?: Record<string, string>;
};

class ApiClient {
  private getBaseUrl: () => string;

  constructor() {
    this.getBaseUrl = getBaseUrl;
  }

  private async request<T>(endpoint: string, options: RequestOptions = { method: 'GET' }): Promise<T> {
    const { params, ...fetchOptions } = options;
    
    let urlString = this.getBaseUrl() + endpoint;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, value);
      });
      urlString += `?${searchParams.toString()}`;
    }

    try {
      const response = await fetch(urlString, {
        ...fetchOptions,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API request to ${endpoint} failed:`, error);
      throw error;
    }
  }

  // Game related endpoints
  async getStatus() {
    return this.request<{ is_loading: boolean }>('/status');
  }

  async getGameInfo() {
    return this.request<Record<string, Record<string, any>>>('/game_info');
  }

  async getGameDetails(type: string, id: string) {
    return this.request<{
      id: string;
      type: string;
      name: string;
      title: string;
      description: string | null;
      tags: string[] | null;
      author: string | null;
      buildDate: string | null;
      repo_link: string | null;
      buttons: Record<string, string> | null;
    }>(`/game_info/${type}/${id}`);
  }

  async getTurnCredentials() {
    return this.request<{
      stun_urls: string;
      turn_urls: string;
      username: string;
      credential: string;
    }>('/turn-credentials');
  }

  async createOffer(gameType: string, gameId: string, data: any) {
    return this.request<{ sessionId: string }>(`/offer/${gameType}/${gameId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Params related endpoints
  async getParamsSchema(sid: string) {
    return this.request<{
      schema: Record<string, any>;
      uiSchema: Record<string, any>;
    }>(`/params/${sid}/schema`);
  }

  async updateParams(sessionId: string, data: any) {
    return this.request<void>(`/params/${sessionId}`, {
      method: 'POST',
      body: JSON.stringify({
        params: data
      }),
    });
  }

  // Add this new method
  getGameThumbUrl(type: string, id: string, format: 'webm' | 'mp4'): string {
    return `${this.getBaseUrl()}/thumb/${type}/${id}.${format}`;
  }
}

export const api = new ApiClient(); 