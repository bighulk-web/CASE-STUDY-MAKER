import { Badge } from "@/components/ui/badge";

const MAP: Record<string, { label: string; variant: "default" | "success" | "warning" | "destructive" | "secondary" }> = {
  uploaded: { label: "Queued", variant: "secondary" },
  extracting: { label: "Extracting", variant: "warning" },
  analyzing: { label: "Analyzing", variant: "warning" },
  indexing: { label: "Indexing", variant: "warning" },
  building: { label: "Building", variant: "warning" },
  ready: { label: "Ready", variant: "success" },
  done: { label: "Done", variant: "success" },
  error: { label: "Error", variant: "destructive" },
};

export function StatusBadge({ status }: { status: string }) {
  const s = MAP[status] ?? { label: status, variant: "secondary" as const };
  return <Badge variant={s.variant}>{s.label}</Badge>;
}
