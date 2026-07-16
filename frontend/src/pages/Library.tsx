import { useRef, useState } from "react";
import { Trash2, Upload, Copy, History, Pencil } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import {
  useDeleteDocument,
  useDocuments,
  useDocumentVersions,
  useRenameDocument,
  useUploadDocuments,
} from "@/lib/queries";
import type { DocumentItem } from "@/lib/types";

const DOC_TYPES = ["", "pptx", "docx", "pdf", "txt"];

export function Library() {
  const [q, setQ] = useState("");
  const [docType, setDocType] = useState("");
  const [preview, setPreview] = useState<DocumentItem | null>(null);
  const [versionsFor, setVersionsFor] = useState<DocumentItem | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useDocuments({ q, doc_type: docType || undefined });
  const upload = useUploadDocuments();
  const del = useDeleteDocument();
  const rename = useRenameDocument();
  const versions = useDocumentVersions(versionsFor?.id ?? null);

  const onFiles = (files: FileList | null) => {
    if (!files || !files.length) return;
    upload.mutate(
      { files: Array.from(files) },
      {
        onSuccess: (docs) => toast.success(`Uploaded ${docs.length} document(s)`),
        onError: () => toast.error("Upload failed"),
      },
    );
  };

  return (
    <div>
      <PageHeader
        title="Document Library"
        description="Upload and manage your case study documents."
        actions={
          <>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pptx,.docx,.pdf,.txt"
              className="hidden"
              onChange={(e) => onFiles(e.target.files)}
            />
            <Button onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
              <Upload className="h-4 w-4" /> Upload
            </Button>
          </>
        }
      />
      <div className="space-y-4 p-8">
        <div className="flex gap-3">
          <Input
            placeholder="Search by title…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="max-w-xs"
          />
          <Select value={docType} onValueChange={(v) => setDocType(v === "all" ? "" : v)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              {DOC_TYPES.map((t) => (
                <SelectItem key={t || "all"} value={t || "all"}>
                  {t ? t.toUpperCase() : "All types"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            onFiles(e.dataTransfer.files);
          }}
          className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground"
        >
          Drag & drop PPTX, DOCX, PDF, or TXT files here to upload.
        </div>

        <Card className="divide-y">
          {isLoading && <div className="p-6 text-sm text-muted-foreground">Loading…</div>}
          {data?.items.map((doc) => (
            <div key={doc.id} className="flex items-center gap-3 p-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium">{doc.title}</span>
                  <Badge variant="outline">{doc.doc_type.toUpperCase()}</Badge>
                  {doc.is_duplicate_of && (
                    <Badge variant="warning">
                      <Copy className="mr-1 h-3 w-3" /> Duplicate
                    </Badge>
                  )}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {doc.original_filename} · {(doc.size_bytes / 1024).toFixed(0)} KB
                </div>
              </div>
              <StatusBadge status={doc.status} />
              <Button variant="ghost" size="sm" onClick={() => setPreview(doc)}>
                Preview
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Version history"
                onClick={() => setVersionsFor(doc)}
              >
                <History className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Rename"
                onClick={() => {
                  const title = window.prompt("New title", doc.title);
                  if (title) rename.mutate({ id: doc.id, title });
                }}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Delete"
                onClick={() => {
                  if (window.confirm(`Delete "${doc.title}"?`)) del.mutate(doc.id);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          {data && data.items.length === 0 && (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No documents yet. Upload some to get started.
            </div>
          )}
        </Card>
      </div>

      <Dialog open={!!preview} onOpenChange={(o) => !o && setPreview(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{preview?.title}</DialogTitle>
          </DialogHeader>
          {preview && (
            <img
              src={`${api.defaults.baseURL}/documents/${preview.id}/preview`}
              alt="preview"
              className="max-h-[60vh] w-full rounded-md border object-contain"
              onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
            />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!versionsFor} onOpenChange={(o) => !o && setVersionsFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Version history — {versionsFor?.title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            {(versions.data ?? []).map((v) => (
              <div key={v.id} className="flex justify-between text-sm">
                <span>v{v.version_no} · {v.note}</span>
                <span className="text-muted-foreground">
                  {new Date(v.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
