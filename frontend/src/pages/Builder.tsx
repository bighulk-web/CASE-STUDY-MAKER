import { useState } from "react";
import { Download, FileText, Sparkles, Trash2, Undo2, Wand2, X } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
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
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import {
  useBuildPresentation,
  usePresentations,
  useTemplates,
} from "@/lib/queries";
import { useBuilderStore } from "@/store/builder";

export function Builder() {
  const templates = useTemplates();
  const presentations = usePresentations();
  const build = useBuildPresentation();

  const store = useBuilderStore();
  const [mode, setMode] = useState<"selection" | "prompt">("selection");

  const opt = store.options;
  const canBuild =
    store.templateId != null &&
    (mode === "prompt" ? store.prompt.trim().length > 0 : store.selected.length > 0);

  const onBuild = () => {
    if (store.templateId == null) {
      toast.error("Choose a template first");
      return;
    }
    build.mutate(
      {
        name: store.name || "Untitled Deck",
        template_id: store.templateId,
        prompt: mode === "prompt" ? store.prompt : "",
        case_study_ids:
          mode === "selection" ? store.selected.map((s) => s.case_study_id) : [],
        options: opt as unknown as Record<string, unknown>,
      },
      {
        onSuccess: (p) =>
          p.status === "ready"
            ? toast.success("Presentation generated")
            : toast.info("Building presentation…"),
        onError: (e: any) =>
          toast.error(e?.response?.data?.detail ?? "Build failed"),
      },
    );
  };

  return (
    <div>
      <PageHeader
        title="Presentation Builder"
        description="Generate polished decks from your case studies. Autosaved."
        actions={
          <Button onClick={onBuild} disabled={!canBuild || build.isPending}>
            <Wand2 className="h-4 w-4" /> Generate
          </Button>
        }
      />
      <div className="grid grid-cols-[1fr_360px] gap-6 p-8">
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Deck settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label>Deck name</Label>
                <Input
                  value={store.name}
                  onChange={(e) => store.setName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Template</Label>
                <Select
                  value={store.templateId ? String(store.templateId) : ""}
                  onValueChange={(v) => store.setTemplateId(Number(v))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {(templates.data ?? []).map((t) => (
                      <SelectItem key={t.id} value={String(t.id)}>
                        {t.name} ({t.category})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={mode === "selection" ? "default" : "outline"}
                  onClick={() => setMode("selection")}
                >
                  Use selected ({store.selected.length})
                </Button>
                <Button
                  size="sm"
                  variant={mode === "prompt" ? "default" : "outline"}
                  onClick={() => setMode("prompt")}
                >
                  <Sparkles className="h-4 w-4" /> AI prompt
                </Button>
              </div>

              {mode === "prompt" && (
                <div className="space-y-1.5">
                  <Label>Prompt</Label>
                  <Textarea
                    placeholder="Create a manufacturing deck showing our SAP projects…"
                    value={store.prompt}
                    onChange={(e) => store.setPrompt(e.target.value)}
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Layout</Label>
                  <Select
                    value={opt.layout}
                    onValueChange={(v) =>
                      store.setOptions({ layout: v as typeof opt.layout })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="one_per_slide">One case study / slide</SelectItem>
                      <SelectItem value="two_per_slide">Two case studies / slide</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Max case studies</Label>
                  <Input
                    type="number"
                    min={1}
                    value={opt.max_case_studies}
                    onChange={(e) =>
                      store.setOptions({ max_case_studies: Number(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {(
                  [
                    ["include_title", "Title slide"],
                    ["include_agenda", "Agenda slide"],
                    ["include_executive_summary", "Executive summary"],
                    ["include_thank_you", "Thank-you slide"],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} className="flex items-center gap-2 text-sm">
                    <Switch
                      checked={opt[key]}
                      onCheckedChange={(c) => store.setOptions({ [key]: c })}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent presentations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(presentations.data ?? []).slice(0, 8).map((p) => (
                <div key={p.id} className="flex items-center justify-between text-sm">
                  <span className="truncate pr-2">{p.name}</span>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={p.status} />
                    {p.output_pptx_path && (
                      <a
                        href={`${api.defaults.baseURL}/presentations/${p.id}/download`}
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                      >
                        <Download className="h-3.5 w-3.5" /> PPTX
                      </a>
                    )}
                    {p.output_pdf_path && (
                      <a
                        href={`${api.defaults.baseURL}/presentations/${p.id}/download.pdf`}
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                      >
                        <FileText className="h-3.5 w-3.5" /> PDF
                      </a>
                    )}
                  </div>
                </div>
              ))}
              {(presentations.data ?? []).length === 0 && (
                <p className="text-sm text-muted-foreground">No presentations yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Selected case studies</CardTitle>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                title="Undo"
                onClick={() => store.undo()}
              >
                <Undo2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Clear"
                onClick={() => store.setSelected([])}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {store.selected.map((s, i) => (
              <div
                key={s.case_study_id}
                className="flex items-center gap-2 rounded-md border p-2 text-sm"
              >
                <span className="text-muted-foreground">{i + 1}.</span>
                <div className="flex-1 min-w-0">
                  <div className="truncate font-medium">{s.title || "Untitled"}</div>
                  <div className="flex gap-1">
                    {s.industry && <Badge variant="outline">{s.industry}</Badge>}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => store.removeSelected(s.case_study_id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            {store.selected.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Add case studies from the Search page, or use an AI prompt.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
