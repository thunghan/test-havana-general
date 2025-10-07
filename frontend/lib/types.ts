export interface Chat {
  id: number;
  is_human_enabled: boolean;
  created_at: string;
}

export interface Message {
  id?: number;
  chat_id: number;
  role: 'ai' | 'human' | 'human_operator';
  message: string;
  created_at?: string;
}

export interface BookingSlot {
  id: number;
  date: string;
  time: string;
}

