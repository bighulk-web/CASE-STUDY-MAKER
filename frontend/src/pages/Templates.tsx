import { useRef, useState } from "react";
import { LayoutTemplate, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useDeleteTemplate, useTemplates, useUploadTemplate } from "@/lib/queries";

const CATEGORIES = [
  "Manufacturing",
  "Healthcare",
  "BFSI",
  "Government",
  "Single Case Study",
  "Multi Case Study",
  "custom",
];

export function Templates() {
  const { data, isLoading } = useTemplates();
  const upload = useUploadTemplate();
  const del = useDeleteTemplate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [category, setCategory] = useState("custom");

  const onFile = (file: File | null) => {
    if (!file) return;
    upload.mutate(
      { file, name: file.name.replace(/\.pptx$/i, ""), category },
      {
        onSuccess: () => toast.success("Template uploaded & placeholders discovered"),
        onError: (e: any) =>
          toast.error(e?.response?.data?.detail ?? "Template upload failed"),
      },
    );
  };

  return (
    <div>
      <PageHeader
        title="Templates"
        description="Upload PowerPoint templates containing {{placeholders}}."
        actions={
          <>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="h-9 rounded-md border border-input bg-transparent px-2 text-sm"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <input
              ref={fileRef}
              type="file"
              accept=".pptx"
              className="hidden"
              onChange={(e) => onFile(e.target.files?.[0] ?? null)}
            />
            <Button onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
              <Upload className="h-4 w-4" /> Upload Template
            </Button>
          </>
        }
      />
      <div className="grid gap-4 p-8 md:grid-cols-2 lg:grid-cols-3">
        {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {data?.map((t) => (
          <Card key={t.id} className="overflow-hidden">
            <div className="flex h-40 items-center justify-center border-b bg-muted/40">
              {t.thumbnail_path ? (
                <img
                  src={`${api.defaults.baseURL}/templates/${t.id}/thumbnail`}
                  alt={t.name}
                  className="h-full w-full object-contain"
                  onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
                />
              ) : (
                <LayoutTemplate className="h-10 w-10 text-muted-foreground" />
              )}
            </div>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{t.name}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    if (window.confirm(`Delete template "${t.name}"?`)) del.mutate(t.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex flex-wrap gap-1">
                <Badge variant="secondary">{t.category}</Badge>
                <Badge variant="outline">{t.slide_count} slide(s)</Badge>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">
                  Placeholders ({t.placeholders.length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {t.placeholders.slice(0, 12).map((ph) => (
                    <Badge
                      key={ph.name}
                      variant={ph.kind === "text" ? "default" : "warning"}
                    >
                      {ph.name}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {data && data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No templates yet. Upload a .pptx with {"{{placeholders}}"}.
          </p>
        )}
      </div>
    </div>
  );
}
