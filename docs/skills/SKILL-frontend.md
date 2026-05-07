---
name: frontend-nextjs
description: "Next.js 14 frontend development for DevOnboard AI. Use this skill for ALL frontend tasks: React components, pages, layouts, API client, auth context, TypeScript types, shadcn/ui components, Tailwind styling, dark mode, chat interface, document upload UI, dashboard, and any browser-side code. Triggers on any mention of frontend, UI, component, page, Next.js, React, TypeScript, Tailwind, shadcn, chat interface, upload, dashboard, or styling."
---

# Frontend Next.js Development — DevOnboard AI

## Stack
- Next.js 14 (App Router), TypeScript strict, Tailwind CSS, shadcn/ui
- Dark mode first. Engineers prefer dark themes.
- No `any` types. Ever.

## Project Init Commands

```bash
npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
npx shadcn@latest init    # Choose: New York style, Zinc color, CSS variables: yes
npx shadcn@latest add button card input label textarea dialog dropdown-menu avatar badge separator scroll-area tabs toast skeleton
npm install axios lucide-react react-markdown remark-gfm react-dropzone
```

## TypeScript Types — Single Source of Truth

```typescript
// frontend/src/lib/types.ts

export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "lead" | "developer" | "viewer";
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  title: string;
  source_type: "pdf" | "markdown" | "confluence" | "github" | "text";
  source_url: string | null;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface SourceCitation {
  document_id: string;
  section_title: string;
  source_url: string | null;
  page_number: number | null;
  relevance_score: number;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  document_count: number;
  chunk_count: number;
  query_count: number;
  member_count: number;
  source_types: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: string | null;
}
```

## API Client with JWT Interceptor

```typescript
// frontend/src/lib/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Auth Context

```typescript
// frontend/src/lib/auth.tsx
"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "./api";
import type { User } from "./types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      api.get("/api/auth/me")
        .then((res) => setUser(res.data.user || res.data))
        .catch(() => localStorage.removeItem("token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/api/auth/login", { email, password });
    localStorage.setItem("token", res.data.access_token);
    setUser(res.data.user);
  };

  const register = async (email: string, name: string, password: string) => {
    const res = await api.post("/api/auth/register", { email, name, password });
    localStorage.setItem("token", res.data.access_token);
    setUser(res.data.user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

## Layout Pattern — Dark Mode First

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DevOnboard AI",
  description: "AI-powered developer onboarding assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-background text-foreground min-h-screen`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

## Chat Interface — The Core Component

```tsx
// frontend/src/components/chat/ChatInterface.tsx
"use client";
import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import MessageBubble from "./MessageBubble";
import api from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ChatInterfaceProps {
  projectId: string;
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.data.answer,
        sources: res.data.sources || [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (res.data.session_id) setSessionId(res.data.session_id);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Sorry, I encountered an error processing your question. Please try again.",
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
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground mt-20">
            <h3 className="text-lg font-medium mb-2">Ask anything about this project</h3>
            <p className="text-sm">Try: &quot;How is the tech stack structured?&quot;</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {loading && (
          <div className="flex items-center gap-2 p-4 text-muted-foreground">
            <div className="animate-pulse">Thinking...</div>
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
          <Button onClick={sendMessage} disabled={!input.trim() || loading} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

## Citation Pill Component

```tsx
// frontend/src/components/chat/CitationPill.tsx
"use client";
import { FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SourceCitation } from "@/lib/types";

interface CitationPillProps {
  source: SourceCitation;
  onClick?: () => void;
}

export default function CitationPill({ source, onClick }: CitationPillProps) {
  return (
    <Badge
      variant="secondary"
      className="cursor-pointer hover:bg-accent gap-1 text-xs"
      onClick={onClick}
    >
      <FileText className="h-3 w-3" />
      {source.section_title}
      {source.page_number && ` — p.${source.page_number}`}
    </Badge>
  );
}
```

## Document Upload Zone

```tsx
// frontend/src/components/documents/UploadZone.tsx
"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Globe, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";

interface UploadZoneProps {
  projectId: string;
  onUploadComplete: () => void;
}

export default function UploadZone({ projectId, onUploadComplete }: UploadZoneProps) {
  const [uploading, setUploading] = useState(false);
  const [confluenceUrl, setConfluenceUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true);
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        await api.post(`/api/projects/${projectId}/documents/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } catch (err) {
        console.error(`Failed to upload ${file.name}:`, err);
      }
    }
    setUploading(false);
    onUploadComplete();
  }, [projectId, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/markdown": [".md"],
      "text/plain": [".txt"],
    },
  });

  const addConfluence = async () => {
    if (!confluenceUrl) return;
    setUploading(true);
    try {
      await api.post(`/api/projects/${projectId}/documents/confluence`, { url: confluenceUrl });
      setConfluenceUrl("");
      onUploadComplete();
    } finally { setUploading(false); }
  };

  const addGithub = async () => {
    if (!githubUrl) return;
    setUploading(true);
    try {
      await api.post(`/api/projects/${projectId}/documents/github`, { repo_url: githubUrl });
      setGithubUrl("");
      onUploadComplete();
    } finally { setUploading(false); }
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"}`}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          {uploading ? "Uploading..." : "Drop PDF, Markdown, or text files here"}
        </p>
      </div>

      <div className="flex gap-2">
        <Globe className="h-4 w-4 mt-3 text-muted-foreground" />
        <Input
          value={confluenceUrl}
          onChange={(e) => setConfluenceUrl(e.target.value)}
          placeholder="Paste Confluence page URL..."
          className="flex-1"
        />
        <Button onClick={addConfluence} disabled={!confluenceUrl || uploading} size="sm">
          Add
        </Button>
      </div>

      <div className="flex gap-2">
        <GitBranch className="h-4 w-4 mt-3 text-muted-foreground" />
        <Input
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          placeholder="GitHub repository URL..."
          className="flex-1"
        />
        <Button onClick={addGithub} disabled={!githubUrl || uploading} size="sm">
          Connect
        </Button>
      </div>
    </div>
  );
}
```

## Design Rules

1. **Dark mode by default** — add `className="dark"` to `<html>` tag
2. **shadcn/ui for everything** — never write custom form inputs, buttons, or dialogs
3. **Tailwind only** — no CSS modules, no styled-components, no inline style objects
4. **Responsive** — but optimize for desktop first (this is a developer tool)
5. **Loading skeletons** — use shadcn Skeleton for all async data
6. **Toast notifications** — use shadcn toast for success/error feedback
7. **Keyboard shortcuts** — Cmd+K for search, Enter to send, Escape to close
