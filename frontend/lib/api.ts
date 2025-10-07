const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export const api = {
  async getAllChats() {
    const response = await fetch(`${API_URL}/api/chats`);
    return response.json();
  },

  async getChatById(chatId: number) {
    const response = await fetch(`${API_URL}/api/chats/${chatId}`);
    return response.json();
  },

  async getCurrentModel() {
    const response = await fetch(`${API_URL}/api/model`);
    return response.json();
  },

  async setModel(model: string) {
    const response = await fetch(`${API_URL}/api/model`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ model }),
    });
    return response.json();
  },
};

