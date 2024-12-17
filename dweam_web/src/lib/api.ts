const getBaseUrl = () => {
  return process.env.INTERNAL_BACKEND_URL || 'http://localhost:8080';
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
    const url = new URL(`${this.getBaseUrl()}${endpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    try {
      const response = await fetch(url.toString(), {
        ...fetchOptions,
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
}

export const api = new ApiClient(); 