import { useEffect, useState } from "react";
import { RefreshCw, Save } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { useTheme } from "@/components/theme-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { useCapabilities, useSettings, useUpdateSettings } from "@/lib/queries";
import type { AppSettings } from "@/lib/types";

export function SettingsPage() {
  const { data } = useSettings();
  const caps = useCapabilities();
  const update = useUpdateSettings();
  const { theme, setTheme } = useTheme();
  const [form, setForm] = useState<Partial<AppSettings>>({});

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const set = (k: keyof AppSettings, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const save = () => {
    const payload: Partial<AppSettings> = { ...form };
    // Don't send empty key fields (would clear existing keys).
    (["openai_api_key", "anthropic_api_key", "gemini_api_key"] as const).forEach((k) => {
      if (!payload[k]) delete payload[k];
    });
    update.mutate(payload, {
      onSuccess: () => toast.success("Settings saved"),
      onError: () => toast.error("Failed to save settings"),
    });
  };

  const reindex = async () => {
    await api.post("/settings/reindex");
    toast.info("Reindexing started");
  };

  const CapBadge = ({ ok, label }: { ok?: boolean; label: string }) => (
    <Badge variant={ok ? "success" : "secondary"}>{label}</Badge>
  );

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure AI providers, embeddings, and appearance."
        actions={
          <Button onClick={save} disabled={update.isPending}>
            <Save className="h-4 w-4" /> Save
          </Button>
        }
      />
      <div className="grid max-w-3xl gap-4 p-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI Provider</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>LLM provider</Label>
                <Select
                  value={form.llm_provider ?? "offline"}
                  onValueChange={(v) => set("llm_provider", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["offline", "openai", "anthropic", "gemini"].map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Model (optional)</Label>
                <Input
                  placeholder="provider default"
                  value={form.llm_model ?? ""}
                  onChange={(e) => set("llm_model", e.target.value)}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Offline mode uses built-in heuristics and needs no API key.
            </p>
            <div className="space-y-1.5">
              <Label>
                OpenAI API key{" "}
                {data?.openai_api_key_configured && <Badge variant="success">set</Badge>}
              </Label>
              <Input
                type="password"
                placeholder="sk-…"
                value={form.openai_api_key ?? ""}
                onChange={(e) => set("openai_api_key", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>
                  Anthropic key{" "}
                  {data?.anthropic_api_key_configured && (
                    <Badge variant="success">set</Badge>
                  )}
                </Label>
                <Input
                  type="password"
                  value={form.anthropic_api_key ?? ""}
                  onChange={(e) => set("anthropic_api_key", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>
                  Gemini key{" "}
                  {data?.gemini_api_key_configured && <Badge variant="success">set</Badge>}
                </Label>
                <Input
                  type="password"
                  value={form.gemini_api_key ?? ""}
                  onChange={(e) => set("gemini_api_key", e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Embeddings & Index</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Embedding provider</Label>
                <Select
                  value={form.embedding_provider ?? "auto"}
                  onValueChange={(v) => set("embedding_provider", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["auto", "hashing", "bge_local", "openai"].map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Vector store</Label>
                <Select
                  value={form.vectorstore_provider ?? "auto"}
                  onValueChange={(v) => set("vectorstore_provider", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["auto", "numpy", "chroma"].map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button variant="outline" onClick={reindex}>
              <RefreshCw className="h-4 w-4" /> Rebuild search index
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <Label>Theme</Label>
              <Select value={theme} onValueChange={(v) => setTheme(v as any)}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["dark", "light", "system"].map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Environment capabilities</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <CapBadge ok={caps.data?.libreoffice} label="LibreOffice (PDF)" />
            <CapBadge ok={caps.data?.tesseract} label="Tesseract (OCR)" />
            <CapBadge ok={caps.data?.chromadb} label="ChromaDB" />
            <CapBadge ok={caps.data?.sentence_transformers} label="BGE embeddings" />
            <CapBadge ok={caps.data?.openai} label="OpenAI SDK" />
            <CapBadge ok={caps.data?.anthropic} label="Anthropic SDK" />
            <CapBadge ok={caps.data?.gemini} label="Gemini SDK" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
