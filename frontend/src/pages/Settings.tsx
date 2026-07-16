import { PageHeader } from "@/components/page-header";

export function SettingsPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure AI providers, embeddings, and appearance."
      />
      <div className="p-8 text-sm text-muted-foreground">
        Settings coming online…
      </div>
    </div>
  );
}
