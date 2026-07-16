import { beforeEach, describe, expect, it } from "vitest";
import type { SearchResultItem } from "@/lib/types";
import { useBuilderStore } from "@/store/builder";

function item(id: number): SearchResultItem {
  return {
    case_study_id: id,
    document_id: id,
    title: `CS ${id}`,
    customer: "",
    industry: "",
    region: "",
    technology: [],
    one_line_summary: "",
    confidence_score: 0,
    score: 0,
    signals: [],
  };
}

describe("builder store", () => {
  beforeEach(() => useBuilderStore.getState().reset());

  it("adds and dedupes selections", () => {
    const s = useBuilderStore.getState();
    s.addSelected(item(1));
    s.addSelected(item(1));
    s.addSelected(item(2));
    expect(useBuilderStore.getState().selected.map((x) => x.case_study_id)).toEqual([1, 2]);
  });

  it("removes and supports undo", () => {
    const s = useBuilderStore.getState();
    s.addSelected(item(1));
    s.addSelected(item(2));
    s.removeSelected(1);
    expect(useBuilderStore.getState().selected.map((x) => x.case_study_id)).toEqual([2]);
    useBuilderStore.getState().undo();
    expect(useBuilderStore.getState().selected.map((x) => x.case_study_id)).toEqual([1, 2]);
  });

  it("reorders selections", () => {
    const s = useBuilderStore.getState();
    s.addSelected(item(1));
    s.addSelected(item(2));
    s.addSelected(item(3));
    s.moveSelected(0, 2);
    expect(useBuilderStore.getState().selected.map((x) => x.case_study_id)).toEqual([2, 3, 1]);
  });

  it("updates options", () => {
    useBuilderStore.getState().setOptions({ layout: "two_per_slide" });
    expect(useBuilderStore.getState().options.layout).toBe("two_per_slide");
  });
});
