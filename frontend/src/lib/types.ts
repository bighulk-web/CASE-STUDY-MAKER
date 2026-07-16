export interface DocumentItem {
  id: number;
  original_filename: string;
  doc_type: string;
  sha256: string;
  size_bytes: number;
  title: string;
  folder_id: number | null;
  status: string;
  error_message: string | null;
  is_duplicate_of: number | null;
  uploaded_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: DocumentItem[];
  total: number;
}

export interface Folder {
  id: number;
  name: string;
  parent_id: number | null;
}

export interface DocumentVersion {
  id: number;
  version_no: number;
  sha256: string;
  note: string;
  created_at: string;
}

export interface Placeholder {
  name: string;
  kind: string;
  arg: string;
  slides: number[];
}

export interface Template {
  id: number;
  name: string;
  category: string;
  placeholders: Placeholder[];
  slide_count: number;
  thumbnail_path: string | null;
  created_at: string;
}

export interface SearchResultItem {
  case_study_id: number;
  document_id: number;
  title: string;
  customer: string;
  industry: string;
  region: string;
  technology: string[];
  one_line_summary: string;
  confidence_score: number;
  score: number;
  signals: string[];
}

export interface SearchIntent {
  query: string;
  industries: string[];
  sectors: string[];
  technologies: string[];
  products: string[];
  business_functions: string[];
  keywords: string[];
  regions: string[];
  year: number | null;
  num_slides: number | null;
  max_case_studies: number;
  sort_order: string;
  template_hint: string;
  layout: string;
  include_executive_summary: boolean;
  include_contents: boolean;
  include_agenda: boolean;
  include_thank_you: boolean;
}

export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
  intent: SearchIntent | null;
}

export interface Facets {
  industries: string[];
  technologies: string[];
  regions: string[];
  customers: string[];
  products: string[];
  business_functions: string[];
  years: number[];
  tags: string[];
}

export interface Job {
  id: number;
  type: string;
  ref_id: number | null;
  status: string;
  progress: number;
  message: string;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface Presentation {
  id: number;
  name: string;
  prompt: string;
  template_id: number | null;
  intent: Record<string, unknown> | null;
  selected_case_study_ids: number[];
  options: Record<string, unknown> | null;
  output_pptx_path: string | null;
  output_pdf_path: string | null;
  status: string;
  created_at: string;
}

export interface AppSettings {
  llm_provider: string;
  llm_model: string;
  embedding_provider: string;
  embedding_model: string;
  vectorstore_provider: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  gemini_api_key?: string;
  openai_api_key_configured?: boolean;
  anthropic_api_key_configured?: boolean;
  gemini_api_key_configured?: boolean;
  theme: string;
}

export interface Capabilities {
  chromadb: boolean;
  sentence_transformers: boolean;
  openai: boolean;
  anthropic: boolean;
  gemini: boolean;
  tesseract: boolean;
  libreoffice: boolean;
}
