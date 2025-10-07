"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getSocket } from "@/lib/socket";
import { api } from "@/lib/api";
import { Chat, Message } from "@/lib/types";
import { Send, Bot } from "lucide-react";

export default function AdminPage() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isHumanEnabled, setIsHumanEnabled] = useState(false);
  const [currentModel, setCurrentModel] = useState<"openai" | "gemini">("gemini");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socket = getSocket();
    socket.connect();

    // Load all chats
    loadChats();
    
    // Load current model
    loadCurrentModel();

    // Socket event listeners
    socket.on("admin_connected", (data: { chat_id: number; chat: Chat; history: Message[] }) => {
      setMessages(data.history || []);
      if (data.chat) {
        setIsHumanEnabled(data.chat.is_human_enabled);
      }
    });

    socket.on("new_message", (data: Message) => {
      if (data.chat_id === currentChatId) {
        setMessages((prev) => [...prev, data]);
      }
    });

    socket.on("human_enabled_changed", (data: { chat_id: number; is_human_enabled: boolean }) => {
      if (data.chat_id === currentChatId) {
        setIsHumanEnabled(data.is_human_enabled);
      }
      // Update in chats list
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === data.chat_id ? { ...chat, is_human_enabled: data.is_human_enabled } : chat
        )
      );
    });

    return () => {
      if (currentChatId) {
        socket.emit("admin_disconnect_from_chat", { chat_id: currentChatId });
      }
      socket.off("admin_connected");
      socket.off("new_message");
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

  const loadCurrentModel = async () => {
    const result = await api.getCurrentModel();
    if (result.success) {
      setCurrentModel(result.model);
    }
  };

  const handleSelectChat = (chatId: number) => {
    const socket = getSocket();
    
    // Disconnect from previous chat
    if (currentChatId) {
      socket.emit("admin_disconnect_from_chat", { chat_id: currentChatId });
    }

    setCurrentChatId(chatId);
    
    // Connect to new chat
    socket.emit("admin_connect", { chat_id: chatId });
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !currentChatId || !isHumanEnabled) return;

    const socket = getSocket();
    socket.emit("admin_message", {
      chat_id: currentChatId,
      message: inputMessage,
    });

    setInputMessage("");
  };

  const handleToggleHumanEnabled = (enabled: boolean) => {
    if (!currentChatId) return;

    const socket = getSocket();
    socket.emit("toggle_human_enabled", {
      chat_id: currentChatId,
      is_enabled: enabled,
    });
  };

  const handleToggleModel = async (checked: boolean) => {
    const newModel = checked ? "openai" : "gemini";
    const result = await api.setModel(newModel);
    if (result.success) {
      setCurrentModel(newModel);
    }
  };

  const getRoleLabel = (role: string) => {
    if (role === "human") return "Student";
    if (role === "ai") return "AI Assistant";
    if (role === "human_operator") return "You (Admin)";
    return role;
  };

  const getRoleStyle = (role: string) => {
    if (role === "human") return "bg-blue-100 dark:bg-blue-900 ml-auto";
    if (role === "ai") return "bg-gray-100 dark:bg-gray-800 mr-auto";
    if (role === "human_operator") return "bg-green-100 dark:bg-green-900 ml-auto";
    return "";
  };

  return (
    <div className="flex h-full">
      {/* Chat Interface */}
      <div className="flex-1 flex flex-col p-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            <p className="text-sm text-muted-foreground">Monitor and intervene in student chats</p>
          </div>
          
          {/* Model Toggle */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <Bot className="h-5 w-5" />
              <span className="text-sm font-medium">Gemini 2.5 Pro</span>
              <Switch checked={currentModel === "openai"} onCheckedChange={handleToggleModel} />
              <span className="text-sm font-medium">GPT-4o</span>
            </div>
          </Card>
        </div>

        {currentChatId ? (
          <>
            {/* Control Bar */}
            <Card className="mb-4 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Human Intervention</p>
                  <p className="text-xs text-muted-foreground">
                    Toggle to disable AI and take over the conversation
                  </p>
                </div>
                <Switch checked={isHumanEnabled} onCheckedChange={handleToggleHumanEnabled} />
              </div>
            </Card>

            {/* Messages */}
            <ScrollArea className="flex-1 mb-4 h-[calc(100vh-350px)]">
              <div className="space-y-4 pr-4">
                {messages.map((msg, index) => (
                  <Card key={index} className={`max-w-[80%] ${getRoleStyle(msg.role)}`}>
                    <CardContent className="p-3">
                      <p className="text-xs font-semibold mb-1">{getRoleLabel(msg.role)}</p>
                      <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                      {msg.created_at && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </p>
                      )}
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
                placeholder={
                  isHumanEnabled
                    ? "Type your message..."
                    : "Enable human intervention to send messages"
                }
                disabled={!isHumanEnabled}
                className="flex-1 min-h-[60px] max-h-[120px]"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!isHumanEnabled}
                size="icon"
                className="h-[60px] w-[60px]"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <Card className="p-8 text-center">
              <p className="text-muted-foreground">Select a chat to monitor or intervene</p>
            </Card>
          </div>
        )}
      </div>

      {/* Chat List */}
      <div className="w-80 border-l p-4">
        <CardHeader className="px-0 pt-0">
          <CardTitle>All Chats</CardTitle>
        </CardHeader>

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
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                      ✓ Human intervention active
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
            {chats.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">No chats yet</p>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

