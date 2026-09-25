import axios from "axios";

const API_BASE = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/api/v1`;

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------- Types ----------

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
}

export interface DocumentItem {
  id: string;
  filename: string;
  status: "uploaded" | "processing" | "chunked" | "embedded" | "failed";
  num_chunks: number;
  file_size_bytes: number;
  error_message?: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface SourceChunk {
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  latency_ms?: number;
  created_at: string;
}

// ---------- Auth ----------

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const res = await apiClient.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data.access_token as string;
}

export async function register(
  email: string,
  password: string,
  full_name?: string
): Promise<User> {
  const res = await apiClient.post("/auth/register", { email, password, full_name });
  return res.data as User;
}

export async function getMe(): Promise<User> {
  const res = await apiClient.get("/auth/me");
  return res.data as User;
}

// ---------- Documents ----------

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await apiClient.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data as DocumentItem;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const res = await apiClient.get("/documents");
  return res.data.documents as DocumentItem[];
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}`);
}

// ---------- Chat ----------

export async function createSession(title = "New Chat"): Promise<ChatSession> {
  const res = await apiClient.post("/chat/sessions", { title });
  return res.data as ChatSession;
}

export async function listSessions(): Promise<ChatSession[]> {
  const res = await apiClient.get("/chat/sessions");
  return res.data as ChatSession[];
}

export async function getMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
  return res.data as ChatMessage[];
}

export async function sendMessage(
  sessionId: string,
  message: string,
  documentIds?: string[]
): Promise<ChatMessage> {
  const res = await apiClient.post("/chat/message", {
    session_id: sessionId,
    message,
    document_ids: documentIds,
  }, { timeout: 120000 });
  return res.data.message as ChatMessage;
}

export async function streamMessage(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  documentIds?: string[]
): Promise<SourceChunk[]> {
  const token = localStorage.getItem("access_token");
  const res = await fetch(
    `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/api/v1/chat/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, message, document_ids: documentIds }),
    }
  );

  if (!res.ok) throw new Error(`Stream error: ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let sources: SourceChunk[] = [];
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const sourcesIdx = buffer.indexOf("\n__SOURCES__");
    if (sourcesIdx !== -1) {
      const text = buffer.slice(0, sourcesIdx);
      if (text) onToken(text);
      const raw = buffer.slice(sourcesIdx + 12, buffer.indexOf("__END__"));
      sources = JSON.parse(raw);
      break;
    } else {
      onToken(buffer);
      buffer = "";
    }
  }

  return sources;
}