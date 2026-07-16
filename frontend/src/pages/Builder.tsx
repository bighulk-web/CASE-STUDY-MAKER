import { PageHeader } from "@/components/page-header";

export function Builder() {
  return (
    <div>
      <PageHeader
        title="Presentation Builder"
        description="Generate polished decks from your case studies."
      />
      <div className="p-8 text-sm text-muted-foreground">
        Presentation builder coming online…
      </div>
    </div>
  );
}
