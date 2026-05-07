"use client";
import { X, ExternalLink, FileText, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { SourceCitation } from "@/lib/types";

interface SourceViewerProps {
  source: SourceCitation | null;
  onClose: () => void;
}

export default function SourceViewer({ source, onClose }: SourceViewerProps) {
  if (!source) return null;

  return (
    <div className="border-l flex flex-col h-full w-80 shrink-0">
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="text-sm font-medium truncate">Source Details</span>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Section</p>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-sm font-medium">{source.section_title}</p>
            </div>
          </div>

          {source.page_number && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Page</p>
              <p className="text-sm">{source.page_number}</p>
            </div>
          )}

          {source.source_url && (
            <>
              <Separator />
              <div>
                <p className="text-xs text-muted-foreground mb-2">Original Source</p>
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  View original
                </a>
              </div>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
