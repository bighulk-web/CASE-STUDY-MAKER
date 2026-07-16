import { PageHeader } from "@/components/page-header";

export function Templates() {
  return (
    <div>
      <PageHeader
        title="Templates"
        description="Upload PowerPoint templates with {{placeholders}}."
      />
      <div className="p-8 text-sm text-muted-foreground">
        Template manager coming online…
      </div>
    </div>
  );
}
