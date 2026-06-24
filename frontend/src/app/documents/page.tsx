"use client";
import { useEffect, useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { documentsApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Upload, Trash2, Search, Loader2 } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-900 text-yellow-300",
  processing: "bg-blue-900 text-blue-300",
  ready: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [searching, setSearching] = useState(false);

  const load = async () => {
    const { data } = await documentsApi.list();
    setDocs(data);
  };

  useEffect(() => { load(); }, []);

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true);
    for (const file of files) {
      await documentsApi.upload(file).catch(() => null);
    }
    await load();
    setUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  async function deleteDoc(id: string) {
    await documentsApi.delete(id);
    setDocs((d) => d.filter((x) => x.id !== id));
  }

  async function queryKB(e: React.FormEvent) {
    e.preventDefault();
    setSearching(true);
    const { data } = await documentsApi.queryKB(query);
    setAnswer(data.answer);
    setSearching(false);
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <h1 className="text-xl font-semibold">Knowledge Base</h1>

        {/* Upload zone */}
        <div {...getRootProps()} className={`card border-2 border-dashed cursor-pointer transition-colors ${isDragActive ? "border-blue-500 bg-blue-900/20" : "border-gray-700"}`}>
          <input {...getInputProps()} />
          <div className="text-center py-8">
            {uploading ? <Loader2 className="animate-spin mx-auto mb-2" /> : <Upload className="mx-auto mb-2 text-gray-400" />}
            <p className="text-gray-400">{isDragActive ? "Drop files here" : "Drag & drop or click to upload"}</p>
            <p className="text-xs text-gray-600 mt-1">PDF, DOCX, PPTX, XLSX, TXT</p>
          </div>
        </div>

        {/* Query KB */}
        <div className="card">
          <h2 className="font-medium mb-3">Query Knowledge Base</h2>
          <form onSubmit={queryKB} className="flex gap-2">
            <input className="input flex-1" placeholder="Ask a question about your documents..." value={query}
              onChange={(e) => setQuery(e.target.value)} />
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={searching}>
              {searching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            </button>
          </form>
          {answer && (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg text-sm text-gray-300 whitespace-pre-wrap">{answer}</div>
          )}
        </div>

        {/* Documents list */}
        <div className="card">
          <h2 className="font-medium mb-4">Uploaded Documents ({docs.length})</h2>
          <div className="space-y-2">
            {docs.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{doc.chunk_count} chunks · {new Date(doc.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[doc.status] || ""}`}>{doc.status}</span>
                  <button onClick={() => deleteDoc(doc.id)} className="text-gray-500 hover:text-red-400 transition-colors">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
            {docs.length === 0 && <p className="text-gray-500 text-sm text-center py-4">No documents uploaded yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
