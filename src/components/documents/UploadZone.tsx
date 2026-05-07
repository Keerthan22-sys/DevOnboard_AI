"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Globe, GitBranch } from "lucide-react";
import { toast } from "sonner";
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
  const [gitlabUrl, setGitlabUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true);
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        await api.post(`/api/projects/${projectId}/documents/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success(`Uploaded ${file.name}`);
      } catch {
        toast.error(`Failed to upload ${file.name}`);
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
    setError(null);
    try {
      await api.post(`/api/projects/${projectId}/documents/confluence`, { url: confluenceUrl });
      setConfluenceUrl("");
      toast.success("Confluence page indexed");
      onUploadComplete();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const message = axiosErr?.response?.data?.detail || "Failed to scrape Confluence page";
      setError(message);
      toast.error(message);
    } finally { setUploading(false); }
  };

  const addGithub = async () => {
    if (!githubUrl) return;
    setUploading(true);
    setError(null);
    try {
      await api.post(`/api/projects/${projectId}/documents/github`, { repo_url: githubUrl, platform: "github" });
      setGithubUrl("");
      toast.success("GitHub repository indexed");
      onUploadComplete();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const message = axiosErr?.response?.data?.detail || "Failed to index GitHub repository";
      setError(message);
      toast.error(message);
    } finally { setUploading(false); }
  };

  const addGitlab = async () => {
    if (!gitlabUrl) return;
    setUploading(true);
    setError(null);
    try {
      await api.post(`/api/projects/${projectId}/documents/github`, { repo_url: gitlabUrl, platform: "gitlab" });
      setGitlabUrl("");
      toast.success("GitLab repository indexed");
      onUploadComplete();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const message = axiosErr?.response?.data?.detail || "Failed to index GitLab repository";
      setError(message);
      toast.error(message);
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
          onChange={(e) => { setConfluenceUrl(e.target.value); setError(null); }}
          placeholder="https://confluence.example.com/display/SPACE/Page"
          className="flex-1"
        />
        <Button onClick={addConfluence} disabled={!confluenceUrl || uploading} size="sm">
          {uploading && confluenceUrl ? "Scraping..." : "Add"}
        </Button>
      </div>

      <div className="flex gap-2">
        <GitBranch className="h-4 w-4 mt-3 text-muted-foreground" />
        <Input
          value={githubUrl}
          onChange={(e) => { setGithubUrl(e.target.value); setError(null); }}
          placeholder="https://github.com/owner/repo"
          className="flex-1"
        />
        <Button onClick={addGithub} disabled={!githubUrl || uploading} size="sm">
          {uploading && githubUrl ? "Indexing..." : "Connect"}
        </Button>
      </div>

      <div className="flex gap-2">
        <GitBranch className="h-4 w-4 mt-3 text-muted-foreground" />
        <Input
          value={gitlabUrl}
          onChange={(e) => { setGitlabUrl(e.target.value); setError(null); }}
          placeholder="https://gitlab.com/owner/repo"
          className="flex-1"
        />
        <Button onClick={addGitlab} disabled={!gitlabUrl || uploading} size="sm">
          {uploading && gitlabUrl ? "Indexing..." : "GitLab"}
        </Button>
      </div>
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
