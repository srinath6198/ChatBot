import { useEffect, useRef, useState } from "react";
import type { DocumentItem } from "../api/client";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "../api/client";

export default function DocumentSidebar() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const refreshInFlightRef = useRef(false);

  async function refresh() {
    if (refreshInFlightRef.current) return;

    refreshInFlightRef.current = true;
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // Keep the last successful document list when the API is unavailable.
    } finally {
      refreshInFlightRef.current = false;
    }
  }

  useEffect(() => {
    refresh();
    // Poll periodically so in-progress embeddings update their status
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, []);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(file);
      await refresh();
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(id: string) {
    await deleteDocument(id);
    await refresh();
  }

  return (
    <div>
      <h3 style={{ fontSize: 14, marginBottom: 8 }}>Documents</h3>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md"
        onChange={handleFileChange}
        disabled={uploading}
        style={{ marginBottom: 12, fontSize: 12 }}
      />
      {uploading && <div style={{ fontSize: 12, color: "#9a9fae" }}>Uploading...</div>}
      <div className="doc-list">
        {documents.map((doc) => (
          <div key={doc.id} className="doc-item">
            <div>{doc.filename}</div>
            <div>
              <span className={`status status-${doc.status}`}>{doc.status}</span>
              <span style={{ marginLeft: 6, color: "#9a9fae" }}>
                {doc.num_chunks} chunks
              </span>
            </div>
            {doc.error_message && (
              <div className="error-text">{doc.error_message}</div>
            )}
            <button
              className="btn-secondary"
              style={{ marginTop: 6, fontSize: 11, padding: "4px 8px" }}
              onClick={() => handleDelete(doc.id)}
            >
              Delete
            </button>
          </div>
        ))}
        {documents.length === 0 && (
          <div style={{ fontSize: 12, color: "#9a9fae" }}>No documents yet.</div>
        )}
      </div>
    </div>
  );
}