import { PageHeader } from "@/components/page-header";

export function SearchPage() {
  return (
    <div>
      <PageHeader
        title="Search"
        description="Natural-language and filtered search across case studies."
      />
      <div className="p-8 text-sm text-muted-foreground">Search coming online…</div>
    </div>
  );
}
