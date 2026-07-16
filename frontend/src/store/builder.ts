import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SearchResultItem } from "@/lib/types";

export interface BuilderOptions {
  layout: "one_per_slide" | "two_per_slide";
  include_title: boolean;
  include_agenda: boolean;
  include_executive_summary: boolean;
  include_thank_you: boolean;
  max_case_studies: number;
}

interface BuilderState {
  name: string;
  prompt: string;
  templateId: number | null;
  options: BuilderOptions;
  selected: SearchResultItem[];
  // undo history of `selected` snapshots
  history: SearchResultItem[][];

  setName: (n: string) => void;
  setPrompt: (p: string) => void;
  setTemplateId: (id: number | null) => void;
  setOptions: (o: Partial<BuilderOptions>) => void;
  setSelected: (items: SearchResultItem[]) => void;
  addSelected: (item: SearchResultItem) => void;
  removeSelected: (id: number) => void;
  moveSelected: (from: number, to: number) => void;
  undo: () => void;
  reset: () => void;
}

const DEFAULT_OPTIONS: BuilderOptions = {
  layout: "one_per_slide",
  include_title: true,
  include_agenda: true,
  include_executive_summary: false,
  include_thank_you: true,
  max_case_studies: 10,
};

export const useBuilderStore = create<BuilderState>()(
  persist(
    (set, get) => {
      const pushHistory = (next: SearchResultItem[]) => {
        const { selected, history } = get();
        return { selected: next, history: [...history.slice(-49), selected] };
      };
      return {
        name: "Untitled Deck",
        prompt: "",
        templateId: null,
        options: DEFAULT_OPTIONS,
        selected: [],
        history: [],

        setName: (name) => set({ name }),
        setPrompt: (prompt) => set({ prompt }),
        setTemplateId: (templateId) => set({ templateId }),
        setOptions: (o) => set({ options: { ...get().options, ...o } }),
        setSelected: (items) => set(pushHistory(items)),
        addSelected: (item) => {
          if (get().selected.some((s) => s.case_study_id === item.case_study_id)) return;
          set(pushHistory([...get().selected, item]));
        },
        removeSelected: (id) =>
          set(pushHistory(get().selected.filter((s) => s.case_study_id !== id))),
        moveSelected: (from, to) => {
          const arr = [...get().selected];
          const [it] = arr.splice(from, 1);
          arr.splice(to, 0, it);
          set(pushHistory(arr));
        },
        undo: () => {
          const { history } = get();
          if (!history.length) return;
          const prev = history[history.length - 1];
          set({ selected: prev, history: history.slice(0, -1) });
        },
        reset: () =>
          set({
            name: "Untitled Deck",
            prompt: "",
            options: DEFAULT_OPTIONS,
            selected: [],
            history: [],
          }),
      };
    },
    { name: "csm-builder" },
  ),
);
