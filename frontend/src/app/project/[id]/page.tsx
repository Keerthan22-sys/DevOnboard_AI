"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, BarChart3, FileText, MessageSquare, Pencil, Settings, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import DocumentList from "@/components/documents/DocumentList";
import UploadZone from "@/components/documents/UploadZone";
import { toast } from "sonner";
import ChatInterface from "@/components/chat/ChatInterface";
import StatsPanel from "@/components/dashboard/StatsPanel";
import IntegrationCredentials from "@/components/settings/IntegrationCredentials";
import { useAuth } from "@/lib/auth";
import api from "@/lib/api";
import type { Project, Document } from "@/lib/types";

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  const fetchProject = useCallback(async () => {
    setLoadingProject(true);
    try {
      const res = await api.get(`/api/projects/${projectId}`);
      setProject(res.data.data || res.data);
    } catch {
      toast.error("Failed to load project");
      router.push("/dashboard");
    } finally {
      setLoadingProject(false);
    }
  }, [projectId, router]);

  const fetchDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const res = await api.get(`/api/projects/${projectId}/documents`);
      setDocuments(res.data.data || res.data);
    } catch {
      toast.error("Failed to load documents");
    } finally {
      setLoadingDocs(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (user && projectId) {
      fetchProject();
      fetchDocuments();
    }
  }, [user, projectId, fetchProject, fetchDocuments]);

  const startEditing = () => {
    if (project) {
      setNameInput(project.name);
      setEditingName(true);
    }
  };

  const cancelEditing = () => {
    setEditingName(false);
    setNameInput("");
  };

  const saveProjectName = async () => {
    const trimmed = nameInput.trim();
    if (!trimmed || !project || trimmed === project.name) {
      cancelEditing();
      return;
    }
    try {
      const res = await api.put(`/api/projects/${projectId}`, { name: trimmed });
      setProject(res.data.data || res.data);
      toast.success("Project renamed");
    } catch {
      toast.error("Failed to rename project");
    }
    setEditingName(false);
  };

  if (authLoading || loadingProject) {
    return (
      <div className="min-h-screen">
        <header className="border-b">
          <div className="max-w-6xl mx-auto px-6 py-4">
            <Skeleton className="h-6 w-48" />
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
          <Skeleton className="h-64 w-full" />
        </main>
      </div>
    );
  }

  if (!user || !project) return null;

  return (
    <div className="min-h-screen">
      <header className="border-b">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex-1 min-w-0">
            {editingName ? (
              <div className="flex items-center gap-2">
                <Input
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveProjectName();
                    if (e.key === "Escape") cancelEditing();
                  }}
                  className="h-8 text-lg font-semibold max-w-xs"
                  autoFocus
                />
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={saveProjectName}>
                  <Check className="h-4 w-4 text-green-500" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={cancelEditing}>
                  <X className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2 group">
                <h1 className="text-lg font-semibold truncate">{project.name}</h1>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={startEditing}
                >
                  <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                </Button>
              </div>
            )}
            {!editingName && project.description && (
              <p className="text-sm text-muted-foreground truncate">{project.description}</p>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview" className="gap-1">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="documents" className="gap-1">
              <FileText className="h-4 w-4" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-1">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-1">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <StatsPanel projectId={projectId} />
          </TabsContent>

          <TabsContent value="documents">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <h3 className="text-sm font-medium mb-3">Add Documents</h3>
                <UploadZone
                  projectId={projectId}
                  onUploadComplete={fetchDocuments}
                />
              </div>
              <div className="lg:col-span-2">
                <h3 className="text-sm font-medium mb-3">
                  Documents ({documents.length})
                </h3>
                <DocumentList documents={documents} loading={loadingDocs} projectId={projectId} onDeleted={fetchDocuments} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="chat" forceMount className={activeTab !== "chat" ? "hidden" : ""}>
            <div className="h-[calc(100vh-220px)] border rounded-lg overflow-hidden">
              <ChatInterface projectId={projectId} />
            </div>
          </TabsContent>

          <TabsContent value="settings">
            <IntegrationCredentials projectId={projectId} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
