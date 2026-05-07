"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import MessageBubble from "./MessageBubble";
import SourceViewer from "./SourceViewer";
import SessionSidebar from "./SessionSidebar";
import api from "@/lib/api";
import type { ChatMessage, SourceCitation } from "@/lib/types";

interface ChatInterfaceProps {
  projectId: string;
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<SourceCitation | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSession = useCallback(async (sid: string) => {
    setLoadingHistory(true);
    setActiveSource(null);
    try {
      const res = await api.get(
        `/api/projects/${projectId}/chat/sessions/${sid}`
      );
      const data = res.data.data || res.data;
      setSessionId(sid);
      setMessages(data.messages || []);
    } catch (err) {
      console.error("Failed to load session:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, [projectId]);

  const startNewChat = useCallback(() => {
    setSessionId(null);
    setMessages([]);
    setActiveSource(null);
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      sources: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post(`/api/projects/${projectId}/chat`, {
        question: input,
        session_id: sessionId,
      });

      const data = res.data.data || res.data;

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (data.session_id) setSessionId(data.session_id);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Sorry, I encountered an error processing your question. Please try again.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-full">
      <SessionSidebar
        projectId={projectId}
        activeSessionId={sessionId}
        onSelectSession={loadSession}
        onNewChat={startNewChat}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <ScrollArea className="flex-1 p-4">
          {loadingHistory ? (
            <div className="space-y-4 py-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-3">
                  <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-muted-foreground mt-20">
              <h3 className="text-lg font-medium mb-2">
                Ask anything about this project
              </h3>
              <p className="text-sm">
                Try: &quot;How is the tech stack structured?&quot;
              </p>
              <p className="text-sm mt-1">
                or &quot;How do I set up the local dev environment?&quot;
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onCitationClick={(source) => setActiveSource(source)}
              />
            ))
          )}
          {loading && (
            <div className="flex items-center gap-2 p-4 text-muted-foreground">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-sm">Thinking...</span>
            </div>
          )}
          <div ref={scrollRef} />
        </ScrollArea>

        <div className="border-t p-4">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about this project..."
              className="min-h-[44px] max-h-[120px] resize-none"
              rows={1}
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      {activeSource && (
        <SourceViewer
          source={activeSource}
          onClose={() => setActiveSource(null)}
        />
      )}
    </div>
  );
}
