import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  AppSettings,
  Capabilities,
  DocumentList,
  DocumentVersion,
  Facets,
  Folder,
  Job,
  Presentation,
  SearchResponse,
  Template,
} from "./types";

export interface SearchRequestBody {
  query?: string;
  industries?: string[];
  technologies?: string[];
  regions?: string[];
  products?: string[];
  business_functions?: string[];
  keywords?: string[];
  tags?: string[];
  customer?: string;
  year?: number | null;
  sort_order?: string;
  max_results?: number;
}

// ---- Documents ----
export function useDocuments(params: {
  folder_id?: number | null;
  doc_type?: string;
  status?: string;
  q?: string;
}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (params.folder_id != null) search.set("folder_id", String(params.folder_id));
      if (params.doc_type) search.set("doc_type", params.doc_type);
      if (params.status) search.set("status", params.status);
      if (params.q) search.set("q", params.q);
      const { data } = await api.get<DocumentList>(`/documents?${search.toString()}`);
      return data;
    },
    refetchInterval: (query) =>
      query.state.data?.items.some((d) =>
        ["uploaded", "extracting", "analyzing", "indexing"].includes(d.status),
      )
        ? 1500
        : false,
  });
}

export function useUploadDocuments() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { files: File[]; folderId?: number | null }) => {
      const form = new FormData();
      vars.files.forEach((f) => form.append("files", f));
      if (vars.folderId != null) form.append("folder_id", String(vars.folderId));
      const { data } = await api.post("/documents", form);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => (await api.delete(`/documents/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useRenameDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: number; title: string }) =>
      (await api.patch(`/documents/${vars.id}`, { title: vars.title })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDocumentVersions(id: number | null) {
  return useQuery({
    queryKey: ["versions", id],
    queryFn: async () =>
      (await api.get<DocumentVersion[]>(`/documents/${id}/versions`)).data,
    enabled: id != null,
  });
}

// ---- Folders ----
export function useFolders() {
  return useQuery({
    queryKey: ["folders"],
    queryFn: async () => (await api.get<Folder[]>("/folders")).data,
  });
}

export function useCreateFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (name: string) => (await api.post("/folders", { name })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["folders"] }),
  });
}

// ---- Templates ----
export function useTemplates() {
  return useQuery({
    queryKey: ["templates"],
    queryFn: async () => (await api.get<Template[]>("/templates")).data,
  });
}

export function useUploadTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { file: File; name: string; category: string }) => {
      const form = new FormData();
      form.append("file", vars.file);
      form.append("name", vars.name);
      form.append("category", vars.category);
      return (await api.post("/templates", form)).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => (await api.delete(`/templates/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

// ---- Search ----
export function useFacets() {
  return useQuery({
    queryKey: ["facets"],
    queryFn: async () => (await api.get<Facets>("/search/facets")).data,
  });
}

export function useSearch() {
  return useMutation({
    mutationFn: async (body: SearchRequestBody) =>
      (await api.post<SearchResponse>("/search", body)).data,
  });
}

export function useIntentSearch() {
  return useMutation({
    mutationFn: async (prompt: string) =>
      (await api.post<SearchResponse>("/search/intent", { prompt })).data,
  });
}

// ---- Builder ----
export interface BuildBody {
  name: string;
  template_id: number;
  prompt?: string;
  case_study_ids?: number[];
  options?: Record<string, unknown>;
}

export function usePresentations() {
  return useQuery({
    queryKey: ["presentations"],
    queryFn: async () => (await api.get<Presentation[]>("/presentations")).data,
  });
}

export function useBuildPresentation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: BuildBody) =>
      (await api.post<Presentation>("/presentations", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["presentations"] }),
  });
}

// ---- Jobs ----
export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await api.get<Job[]>("/jobs")).data,
    refetchInterval: 2000,
  });
}

// ---- Settings ----
export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await api.get<AppSettings>("/settings")).data,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<AppSettings>) =>
      (await api.put<AppSettings>("/settings", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: ["capabilities"],
    queryFn: async () => (await api.get<Capabilities>("/capabilities")).data,
  });
}
