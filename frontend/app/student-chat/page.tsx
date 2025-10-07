"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getSocket } from "@/lib/socket";
import { api } from "@/lib/api";
import { Chat, Message } from "@/lib/types";
import { Plus, Send } from "lucide-react";

export default function StudentChatPage() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isAdminConnected, setIsAdminConnected] = useState(false);
  const [isHumanEnabled, setIsHumanEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socket = getSocket();
    socket.connect();

    // Load all chats
    loadChats();

    // Socket event listeners
    socket.on("chat_created", (data: { chat_id: number }) => {
      setCurrentChatId(data.chat_id);
      loadChats();
    });

    socket.on("student_connected", (data: { chat_id: number; chat: Chat; history: Message[]; is_admin_connected: boolean }) => {
      setMessages(data.history || []);
      setIsAdminConnected(data.is_admin_connected);
      if (data.chat) {
        setIsHumanEnabled(data.chat.is_human_enabled);
      }
    });

    socket.on("new_message", (data: Message) => {
      if (data.chat_id === currentChatId) {
        setMessages((prev) => [...prev, data]);
      }
    });

    socket.on("escalation_triggered", (data: { chat_id: number; is_human_enabled: boolean }) => {
      if (data.chat_id === currentChatId) {
        setIsHumanEnabled(data.is_human_enabled);
      }
    });

    socket.on("admin_status_changed", (data: { chat_id: number; is_admin_connected: boolean }) => {
      if (data.chat_id === currentChatId) {
        setIsAdminConnected(data.is_admin_connected);
      }
    });

    socket.on("human_enabled_changed", (data: { chat_id: number; is_human_enabled: boolean }) => {
      if (data.chat_id === currentChatId) {
        setIsHumanEnabled(data.is_human_enabled);
      }
    });

    return () => {
      socket.off("chat_created");
      socket.off("student_connected");
      socket.off("new_message");
      socket.off("escalation_triggered");
      socket.off("admin_status_changed");
      socket.off("human_enabled_changed");
    };
  }, [currentChatId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadChats = async () => {
    const result = await api.getAllChats();
    if (result.success) {
      setChats(result.chats);
    }
  };

  const handleNewChat = () => {
    const socket = getSocket();
    socket.emit("student_connect", {});
  };

  const handleSelectChat = (chatId: number) => {
    setCurrentChatId(chatId);
    const socket = getSocket();
    socket.emit("student_connect", { chat_id: chatId });
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !currentChatId) return;

    const socket = getSocket();
    socket.emit("student_message", {
      chat_id: currentChatId,
      message: inputMessage,
    });

    setInputMessage("");
  };

  const getRoleLabel = (role: string) => {
    if (role === "human") return "You";
    if (role === "ai") return "AI Assistant";
    if (role === "human_operator") return "Admin";
    return role;
  };

  const getRoleStyle = (role: string) => {
    if (role === "human") return "bg-blue-100 dark:bg-blue-900 ml-auto";
    if (role === "ai") return "bg-gray-100 dark:bg-gray-800 mr-auto";
    if (role === "human_operator") return "bg-green-100 dark:bg-green-900 mr-auto";
    return "";
  };

  return (
    <div className="flex h-full">
      {/* Chat Interface */}
      <div className="flex-1 flex flex-col p-4">
        <div className="mb-4">
          <h1 className="text-2xl font-bold">Student Chat</h1>
          <p className="text-sm text-muted-foreground">
            Chat with our AI assistant to learn about Havana University
          </p>
        </div>

        {currentChatId ? (
          <>
            {/* Status Bar */}
            {isHumanEnabled && (
              <Card className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-950">
                <p className="text-sm font-medium">
                  {isAdminConnected ? "✓ Admin connected" : "⏳ Finding next available admin..."}
                </p>
              </Card>
            )}

            {/* Messages */}
            <ScrollArea className="flex-1 mb-4 h-[calc(100vh-300px)]">
              <div className="space-y-4 pr-4">
                {messages.map((msg, index) => (
                  <Card key={index} className={`max-w-[80%] ${getRoleStyle(msg.role)}`}>
                    <CardContent className="p-3">
                      <p className="text-xs font-semibold mb-1">{getRoleLabel(msg.role)}</p>
                      <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                    </CardContent>
                  </Card>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="flex gap-2">
              <Textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Type your message..."
                className="flex-1 min-h-[60px] max-h-[120px]"
              />
              <Button onClick={handleSendMessage} size="icon" className="h-[60px] w-[60px]">
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <Card className="p-8 text-center">
              <p className="text-muted-foreground mb-4">No chat selected</p>
              <Button onClick={handleNewChat}>
                <Plus className="mr-2 h-4 w-4" />
                Start New Chat
              </Button>
            </Card>
          </div>
        )}
      </div>

      {/* Chat List */}
      <div className="w-80 border-l p-4">
        <Button onClick={handleNewChat} className="w-full mb-4">
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>

        <ScrollArea className="h-[calc(100vh-120px)]">
          <div className="space-y-2">
            {chats.map((chat) => (
              <Card
                key={chat.id}
                className={`cursor-pointer hover:bg-accent transition-colors ${
                  currentChatId === chat.id ? "border-primary" : ""
                }`}
                onClick={() => handleSelectChat(chat.id)}
              >
                <CardContent className="p-3">
                  <p className="font-medium">Chat #{chat.id}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(chat.created_at).toLocaleString()}
                  </p>
                  {chat.is_human_enabled && (
                    <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                      Human assistance active
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

