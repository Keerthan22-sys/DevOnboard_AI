"use client";
import { FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SourceCitation } from "@/lib/types";

interface CitationPillProps {
  source: SourceCitation;
  index: number;
  onClick?: () => void;
}

export default function CitationPill({ source, index, onClick }: CitationPillProps) {
  return (
    <Badge
      variant="secondary"
      className="cursor-pointer hover:bg-accent gap-1 text-xs"
      onClick={onClick}
    >
      <FileText className="h-3 w-3" />
      [{index}] {source.section_title}
      {source.page_number && ` \u2014 p.${source.page_number}`}
    </Badge>
  );
}
