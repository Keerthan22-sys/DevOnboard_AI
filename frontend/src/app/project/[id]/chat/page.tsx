"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import ChatInterface from "@/components/chat/ChatInterface";
import { useAuth } from "@/lib/auth";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading } = useAuth();
  const projectId = params.id as string;

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="h-screen flex flex-col">
        <header className="border-b">
          <div className="max-w-6xl mx-auto px-6 py-4">
            <Skeleton className="h-6 w-48" />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <Skeleton className="h-64 w-96" />
        </main>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b shrink-0">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-4">
          <Link href={`/project/${projectId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Project
            </Button>
          </Link>
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-sm font-semibold">AI Chat</h1>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <ChatInterface projectId={projectId} />
      </main>
    </div>
  );
}
