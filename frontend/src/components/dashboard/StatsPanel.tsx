"use client";
import { useEffect, useState } from "react";
import {
  FileText,
  MessageSquare,
  Layers,
  Users,
  Clock,
  Search,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import api from "@/lib/api";
import type { ProjectStats } from "@/lib/types";

interface StatsPanelProps {
  projectId: string;
}

interface RecentQuery {
  id: string;
  question: string;
  created_at: string;
  user_name: string;
}

const SOURCE_LABELS: Record<string, string> = {
  pdf: "PDF",
  markdown: "Markdown",
  confluence: "Confluence",
  github: "GitHub",
  text: "Text",
};

export default function StatsPanel({ projectId }: StatsPanelProps) {
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [recentQueries, setRecentQueries] = useState<RecentQuery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [statsRes, queriesRes] = await Promise.all([
          api.get(`/api/projects/${projectId}/stats`),
          api.get(`/api/projects/${projectId}/recent-queries`),
        ]);
        setStats(statsRes.data.data || statsRes.data);
        setRecentQueries(queriesRes.data.data || queriesRes.data);
      } catch {
        toast.error("Failed to load project stats");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-4 w-20 mb-2" />
                <Skeleton className="h-8 w-12" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6 space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!stats) return null;

  const statCards = [
    {
      label: "Documents",
      value: stats.document_count,
      icon: FileText,
    },
    {
      label: "Chunks",
      value: stats.chunk_count,
      icon: Layers,
    },
    {
      label: "Queries",
      value: stats.query_count,
      icon: MessageSquare,
    },
    {
      label: "Members",
      value: stats.member_count,
      icon: Users,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <stat.icon className="h-4 w-4" />
                <span className="text-xs font-medium">{stat.label}</span>
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {Object.keys(stats.source_types).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Source Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(stats.source_types).map(([type, count]) => (
                <Badge key={type} variant="secondary" className="gap-1">
                  {SOURCE_LABELS[type] || type}
                  <span className="text-muted-foreground ml-1">{count}</span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Search className="h-4 w-4" />
            Recent Queries
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentQueries.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No queries yet. Start a chat to see activity here.
            </p>
          ) : (
            <div className="space-y-3">
              {recentQueries.map((q) => (
                <div key={q.id} className="flex items-start gap-3">
                  <MessageSquare className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{q.question}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-muted-foreground">{q.user_name}</span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(q.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
