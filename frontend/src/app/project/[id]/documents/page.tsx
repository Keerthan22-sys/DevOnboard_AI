"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import UploadZone from "@/components/documents/UploadZone";
import DocumentList from "@/components/documents/DocumentList";
import { useAuth } from "@/lib/auth";
import api from "@/lib/api";
import type { Project, Document } from "@/lib/types";

export default function DocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingDocs, setLoadingDocs] = useState(true);

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
    } catch (err) {
      console.error("Failed to fetch project:", err);
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
    } catch (err) {
      console.error("Failed to fetch documents:", err);
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
          <Link href={`/project/${projectId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Project
            </Button>
          </Link>
          <Separator orientation="vertical" className="h-6" />
          <div>
            <h1 className="text-lg font-semibold">{project.name} — Documents</h1>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold">Upload Sources</h2>
            <p className="text-sm text-muted-foreground">
              Add PDFs, Markdown files, Confluence pages, or GitHub repositories.
            </p>
            <UploadZone
              projectId={projectId}
              onUploadComplete={fetchDocuments}
            />
          </div>

          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                All Documents ({documents.length})
              </h2>
            </div>
            <DocumentList documents={documents} loading={loadingDocs} projectId={projectId} onDeleted={fetchDocuments} />
          </div>
        </div>
      </main>
    </div>
  );
}
