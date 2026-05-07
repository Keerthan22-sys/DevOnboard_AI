"use client";
import { useCallback, useEffect, useState } from "react";
import { GitBranch, Globe, Key, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import api from "@/lib/api";
import type { IntegrationCredential } from "@/lib/types";

interface IntegrationCredentialsProps {
  projectId: string;
}

const INTEGRATIONS = [
  {
    type: "github" as const,
    name: "GitHub",
    icon: GitBranch,
    description: "Access private GitHub repositories with a Personal Access Token.",
    tokenPlaceholder: "ghp_xxxxxxxxxxxxxxxxxxxx",
    needsEmail: false,
    needsBaseUrl: false,
  },
  {
    type: "gitlab" as const,
    name: "GitLab",
    icon: GitBranch,
    description: "Access private GitLab repositories with a Personal Access Token.",
    tokenPlaceholder: "glpat-xxxxxxxxxxxxxxxxxxxx",
    needsEmail: false,
    needsBaseUrl: true,
    baseUrlPlaceholder: "https://gitlab.com (or self-hosted URL)",
  },
  {
    type: "confluence" as const,
    name: "Confluence",
    icon: Globe,
    description: "Access private Confluence pages with an API token and email.",
    tokenPlaceholder: "Your Confluence API token",
    needsEmail: true,
    needsBaseUrl: true,
    baseUrlPlaceholder: "https://yourteam.atlassian.net/wiki",
  },
];

export default function IntegrationCredentials({ projectId }: IntegrationCredentialsProps) {
  const [credentials, setCredentials] = useState<IntegrationCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<"github" | "gitlab" | "confluence" | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formLabel, setFormLabel] = useState("");
  const [formToken, setFormToken] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formBaseUrl, setFormBaseUrl] = useState("");

  const fetchCredentials = useCallback(async () => {
    try {
      const res = await api.get(`/api/projects/${projectId}/credentials`);
      setCredentials(res.data.data || res.data);
    } catch {
      toast.error("Failed to load integration credentials");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const getCredentialForType = (type: string) =>
    credentials.find((c) => c.integration_type === type);

  const openAddDialog = (type: "github" | "gitlab" | "confluence") => {
    setSelectedType(type);
    setFormLabel("");
    setFormToken("");
    setFormEmail("");
    setFormBaseUrl("");
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!selectedType || !formToken.trim()) return;

    const integration = INTEGRATIONS.find((i) => i.type === selectedType);
    if (integration?.needsEmail && !formEmail.trim()) {
      toast.error("Email is required for Confluence");
      return;
    }

    setSaving(true);
    try {
      const existing = getCredentialForType(selectedType);
      const payload = {
        integration_type: selectedType,
        label: formLabel || `${integration?.name} Token`,
        token: formToken,
        email: formEmail || null,
        base_url: formBaseUrl || null,
      };

      if (existing) {
        await api.put(`/api/projects/${projectId}/credentials/${existing.id}`, {
          label: payload.label,
          token: payload.token,
          email: payload.email,
          base_url: payload.base_url,
        });
        toast.success(`${integration?.name} credentials updated`);
      } else {
        await api.post(`/api/projects/${projectId}/credentials`, payload);
        toast.success(`${integration?.name} credentials saved`);
      }

      setDialogOpen(false);
      fetchCredentials();
    } catch {
      toast.error("Failed to save credentials");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = (id: string) => {
    setDeletingId(id);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await api.delete(`/api/projects/${projectId}/credentials/${deletingId}`);
      toast.success("Credentials removed");
      setDeleteDialogOpen(false);
      setDeletingId(null);
      fetchCredentials();
    } catch {
      toast.error("Failed to remove credentials");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Integrations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 w-24 bg-muted rounded mb-3" />
              <div className="h-3 w-full bg-muted rounded mb-2" />
              <div className="h-3 w-2/3 bg-muted rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const selectedIntegration = INTEGRATIONS.find((i) => i.type === selectedType);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Integrations</h2>
        <p className="text-sm text-muted-foreground">
          Configure credentials to access private repositories and Confluence pages.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {INTEGRATIONS.map((integration) => {
          const cred = getCredentialForType(integration.type);
          const Icon = integration.icon;

          return (
            <Card key={integration.type} className="p-6 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium">{integration.name}</span>
                </div>
                {cred ? (
                  <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                    Configured
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-muted-foreground">
                    Not set
                  </Badge>
                )}
              </div>

              <p className="text-sm text-muted-foreground flex-1">
                {integration.description}
              </p>

              {cred && (
                <div className="text-xs text-muted-foreground space-y-1">
                  <p className="flex items-center gap-1">
                    <Key className="h-3 w-3" />
                    {cred.label}
                  </p>
                  {cred.email && <p>Email: {cred.email}</p>}
                  {cred.base_url && <p>URL: {cred.base_url}</p>}
                </div>
              )}

              <div className="flex gap-2 mt-auto">
                <Button
                  size="sm"
                  variant={cred ? "outline" : "default"}
                  className="flex-1"
                  onClick={() => openAddDialog(integration.type)}
                >
                  {cred ? "Update" : (
                    <>
                      <Plus className="h-3 w-3 mr-1" />
                      Add
                    </>
                  )}
                </Button>
                {cred && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-destructive hover:text-destructive"
                    onClick={() => confirmDelete(cred.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {getCredentialForType(selectedType || "") ? "Update" : "Add"}{" "}
              {selectedIntegration?.name} Credentials
            </DialogTitle>
            <DialogDescription>
              Your token is encrypted before storage and never exposed in API responses.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="label">Label</Label>
              <Input
                id="label"
                value={formLabel}
                onChange={(e) => setFormLabel(e.target.value)}
                placeholder={`e.g. My ${selectedIntegration?.name} token`}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="token">
                {selectedIntegration?.type === "confluence" ? "API Token" : "Personal Access Token"}
              </Label>
              <Input
                id="token"
                type="password"
                value={formToken}
                onChange={(e) => setFormToken(e.target.value)}
                placeholder={selectedIntegration?.tokenPlaceholder}
              />
            </div>

            {selectedIntegration?.needsEmail && (
              <div className="space-y-2">
                <Label htmlFor="email">Email (required)</Label>
                <Input
                  id="email"
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="your-email@company.com"
                />
              </div>
            )}

            {selectedIntegration?.needsBaseUrl && (
              <div className="space-y-2">
                <Label htmlFor="base_url">Base URL (optional for cloud)</Label>
                <Input
                  id="base_url"
                  value={formBaseUrl}
                  onChange={(e) => setFormBaseUrl(e.target.value)}
                  placeholder={selectedIntegration.baseUrlPlaceholder}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formToken.trim() || saving}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove credentials?</DialogTitle>
            <DialogDescription>
              This will delete the stored token. You can re-add credentials later.
              Existing indexed documents will not be affected.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
