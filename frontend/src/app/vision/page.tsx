"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { visionApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Eye, Upload, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

const TASKS = [
  { value: "general", label: "Describe Image" },
  { value: "ocr", label: "Extract Text (OCR)" },
  { value: "diagram", label: "Analyze Chart/Graph" },
  { value: "error_analysis", label: "Debug Screenshot" },
  { value: "understand", label: "Deep Understanding" },
];

export default function VisionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [task, setTask] = useState("general");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp"] },
    maxFiles: 1,
  });

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await visionApi.analyze(file, task);
      setResult(data.analysis || data.result || "");
    } catch {
      setError("Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="flex items-center gap-3">
          <Eye size={22} className="text-blue-400" />
          <h1 className="text-xl font-semibold">Vision Analysis</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload + controls */}
          <div className="space-y-4">
            <div {...getRootProps()} className={`card border-2 border-dashed cursor-pointer transition-colors ${isDragActive ? "border-blue-500 bg-blue-900/20" : "border-gray-700 hover:border-gray-600"}`}>
              <input {...getInputProps()} />
              {preview ? (
                <img src={preview} alt="preview" className="w-full rounded-lg max-h-64 object-contain" />
              ) : (
                <div className="text-center py-12">
                  <Upload className="mx-auto mb-2 text-gray-400" size={32} />
                  <p className="text-gray-400">{isDragActive ? "Drop image here" : "Drag & drop or click to upload"}</p>
                  <p className="text-xs text-gray-600 mt-1">PNG, JPG, GIF, WebP</p>
                </div>
              )}
            </div>

            <form onSubmit={analyze} className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Analysis Task</label>
                <div className="grid grid-cols-2 gap-2">
                  {TASKS.map((t) => (
                    <button key={t.value} type="button" onClick={() => setTask(t.value)}
                      className={`px-3 py-2 rounded-lg text-sm text-left transition-colors ${task === t.value ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2"
                disabled={!file || loading}>
                {loading ? <><Loader2 size={16} className="animate-spin" /> Analyzing...</> : <><Eye size={16} /> Analyze Image</>}
              </button>
            </form>
          </div>

          {/* Result */}
          <div className="card">
            <h2 className="font-medium mb-3 text-sm text-gray-400">Result</h2>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            {!result && !error && !loading && (
              <p className="text-gray-600 text-sm">Upload an image and select a task to begin.</p>
            )}
            {loading && (
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <Loader2 size={16} className="animate-spin" /> Processing image...
              </div>
            )}
            {result && (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{result}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
