"use client";
import { useState } from "react";
import { FileText, CheckCircle, AlertCircle, Loader2, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import api from "@/lib/api";
import type { Document } from "@/lib/types";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  projectId: string;
  onDeleted: () => void;
}

function StatusBadge({ status }: { status: Document["status"] }) {
  switch (status) {
    case "ready":
      return (
        <Badge variant="default" className="gap-1">
          <CheckCircle className="h-3 w-3" />
          Ready
        </Badge>
      );
    case "processing":
      return (
        <Badge variant="secondary" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Processing
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="destructive" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
  }
}

function SourceTypeBadge({ sourceType }: { sourceType: Document["source_type"] }) {
  const labels: Record<Document["source_type"], string> = {
    pdf: "PDF",
    markdown: "Markdown",
    confluence: "Confluence",
    github: "GitHub",
    gitlab: "GitLab",
    text: "Text",
  };

  return (
    <Badge variant="outline" className="text-xs">
      {labels[sourceType]}
    </Badge>
  );
}

export default function DocumentList({ documents, loading, projectId, onDeleted }: DocumentListProps) {
  const [confirmDoc, setConfirmDoc] = useState<Document | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirmDoc) return;
    setDeleting(true);
    try {
      await api.delete(`/api/projects/${projectId}/documents/${confirmDoc.id}`);
      toast.success(`Deleted "${confirmDoc.title}"`);
      setConfirmDoc(null);
      onDeleted();
    } catch {
      toast.error("Failed to delete document");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
            <Skeleton className="h-8 w-8 rounded" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p className="text-sm">No documents yet. Upload files or connect a source above.</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
          >
            <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{doc.title}</p>
              <div className="flex items-center gap-2 mt-1">
                <SourceTypeBadge sourceType={doc.source_type} />
                {doc.chunk_count > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {doc.chunk_count} chunks
                  </span>
                )}
              </div>
            </div>
            <StatusBadge status={doc.status} />
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive shrink-0"
              onClick={() => setConfirmDoc(doc)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      <Dialog open={!!confirmDoc} onOpenChange={(open) => !open && setConfirmDoc(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{confirmDoc?.title}</strong>? All
              associated chunks and embeddings will be permanently removed. This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="ghost" onClick={() => setConfirmDoc(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? "Deleting..." : "Delete Document"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
