import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Dashboard() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your case study library and activity."
      />
      <div className="grid gap-4 p-8 md:grid-cols-2 lg:grid-cols-4">
        {["Documents", "Case Studies", "Templates", "Presentations"].map((t) => (
          <Card key={t}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">{t}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">—</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
