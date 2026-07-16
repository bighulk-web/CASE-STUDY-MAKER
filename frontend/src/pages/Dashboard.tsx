import { FileText, LayoutTemplate, Presentation, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  useDocuments,
  useJobs,
  usePresentations,
  useTemplates,
} from "@/lib/queries";

export function Dashboard() {
  const docs = useDocuments({});
  const templates = useTemplates();
  const presentations = usePresentations();
  const jobs = useJobs();

  const activeJobs = (jobs.data ?? []).filter(
    (j) => j.status === "running" || j.status === "pending",
  );

  const stats = [
    { label: "Documents", value: docs.data?.total ?? 0, icon: FileText },
    {
      label: "Case Studies",
      value: (docs.data?.items ?? []).filter((d) => d.status === "ready").length,
      icon: Sparkles,
    },
    { label: "Templates", value: templates.data?.length ?? 0, icon: LayoutTemplate },
    { label: "Presentations", value: presentations.data?.length ?? 0, icon: Presentation },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your case study library and activity."
      />
      <div className="space-y-6 p-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon }) => (
            <Card key={label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Processing</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeJobs.length === 0 && (
                <p className="text-sm text-muted-foreground">No active jobs.</p>
              )}
              {activeJobs.map((j) => (
                <div key={j.id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{j.type}</span>
                    <span className="text-muted-foreground">{j.message}</span>
                  </div>
                  <Progress value={j.progress} />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(docs.data?.items ?? []).slice(0, 6).map((d) => (
                <div key={d.id} className="flex items-center justify-between text-sm">
                  <span className="truncate pr-2">{d.title}</span>
                  <StatusBadge status={d.status} />
                </div>
              ))}
              {(docs.data?.items ?? []).length === 0 && (
                <p className="text-sm text-muted-foreground">No documents yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
