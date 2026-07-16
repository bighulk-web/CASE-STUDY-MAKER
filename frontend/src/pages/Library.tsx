import { PageHeader } from "@/components/page-header";

export function Library() {
  return (
    <div>
      <PageHeader
        title="Document Library"
        description="Upload and manage your case study documents."
      />
      <div className="p-8 text-sm text-muted-foreground">
        Document library coming online…
      </div>
    </div>
  );
}
