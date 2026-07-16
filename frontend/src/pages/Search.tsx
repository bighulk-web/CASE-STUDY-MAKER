import { useState } from "react";
import { Plus, Search as SearchIcon, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useFacets, useIntentSearch, useSearch } from "@/lib/queries";
import type { SearchResultItem } from "@/lib/types";
import { useBuilderStore } from "@/store/builder";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [industries, setIndustries] = useState<string[]>([]);
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [intentInfo, setIntentInfo] = useState<string | null>(null);

  const facets = useFacets();
  const search = useSearch();
  const intentSearch = useIntentSearch();
  const addSelected = useBuilderStore((s) => s.addSelected);
  const navigate = useNavigate();

  const toggle = (list: string[], set: (v: string[]) => void, val: string) =>
    set(list.includes(val) ? list.filter((v) => v !== val) : [...list, val]);

  const runStructured = () => {
    search.mutate(
      { query, industries, technologies, regions, max_results: 30 },
      {
        onSuccess: (data) => {
          setResults(data.items);
          setIntentInfo(null);
        },
      },
    );
  };

  const runNL = () => {
    if (!query.trim()) return;
    intentSearch.mutate(query, {
      onSuccess: (data) => {
        setResults(data.items);
        if (data.intent) {
          const bits = [
            data.intent.industries.join(", "),
            data.intent.technologies.join(", "),
            data.intent.regions.join(", "),
          ].filter(Boolean);
          setIntentInfo(bits.join(" · ") || "parsed prompt");
        }
      },
    });
  };

  const FacetGroup = ({
    title,
    values,
    selected,
    onToggle,
  }: {
    title: string;
    values: string[];
    selected: string[];
    onToggle: (v: string) => void;
  }) =>
    values.length ? (
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">{title}</p>
        <div className="flex flex-wrap gap-1">
          {values.map((v) => (
            <button key={v} onClick={() => onToggle(v)}>
              <Badge variant={selected.includes(v) ? "default" : "outline"}>{v}</Badge>
            </button>
          ))}
        </div>
      </div>
    ) : null;

  return (
    <div>
      <PageHeader
        title="Search"
        description="Natural-language and filtered search across case studies."
      />
      <div className="grid grid-cols-[260px_1fr] gap-6 p-8">
        <div className="space-y-4">
          <FacetGroup
            title="Industry"
            values={facets.data?.industries ?? []}
            selected={industries}
            onToggle={(v) => toggle(industries, setIndustries, v)}
          />
          <FacetGroup
            title="Technology"
            values={facets.data?.technologies ?? []}
            selected={technologies}
            onToggle={(v) => toggle(technologies, setTechnologies, v)}
          />
          <FacetGroup
            title="Region"
            values={facets.data?.regions ?? []}
            selected={regions}
            onToggle={(v) => toggle(regions, setRegions, v)}
          />
        </div>

        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder='e.g. "Manufacturing projects using SAP S/4HANA"'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runNL()}
            />
            <Button onClick={runNL} disabled={intentSearch.isPending}>
              <Sparkles className="h-4 w-4" /> AI Search
            </Button>
            <Button variant="outline" onClick={runStructured} disabled={search.isPending}>
              <SearchIcon className="h-4 w-4" /> Filter
            </Button>
          </div>

          {intentInfo && (
            <p className="text-xs text-muted-foreground">
              AI understood: <span className="text-foreground">{intentInfo}</span>
            </p>
          )}

          <div className="space-y-3">
            {results.map((r) => (
              <Card key={r.case_study_id}>
                <CardContent className="flex items-start gap-3 p-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{r.title || "Untitled"}</span>
                      {r.customer && <Badge variant="secondary">{r.customer}</Badge>}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {r.one_line_summary}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {r.industry && <Badge variant="outline">{r.industry}</Badge>}
                      {r.region && <Badge variant="outline">{r.region}</Badge>}
                      {r.technology.slice(0, 4).map((t) => (
                        <Badge key={t}>{t}</Badge>
                      ))}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      relevance {(r.score * 100).toFixed(0)}% · {r.signals.join(", ")}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      addSelected(r);
                      toast.success("Added to builder");
                    }}
                  >
                    <Plus className="h-4 w-4" /> Add
                  </Button>
                </CardContent>
              </Card>
            ))}
            {results.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Run a search to see matching case studies.
              </p>
            )}
            {results.length > 0 && (
              <Button variant="link" onClick={() => navigate("/builder")}>
                Go to Presentation Builder →
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
