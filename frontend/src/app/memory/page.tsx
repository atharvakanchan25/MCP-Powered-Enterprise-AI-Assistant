"use client";
import { useEffect, useState } from "react";
import { agentApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Brain, Plus, Trash2, Search } from "lucide-react";

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    agentApi.getMemory().then(({ data }) => setMemories(data)).catch(() => null).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function addMemory(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim() || !value.trim()) return;
    await agentApi.storeMemory(key.trim(), value.trim());
    setKey(""); setValue("");
    await load();
  }

  const TYPES = ["all", "agent", "conversation", "user_profile"];
  const [activeType, setActiveType] = useState("all");

  const filtered = memories.filter((m) => {
    const matchType = activeType === "all" || m.key.startsWith(activeType);
    const matchSearch = !filter || m.key.toLowerCase().includes(filter.toLowerCase()) || m.value.toLowerCase().includes(filter.toLowerCase());
    return matchType && matchSearch;
  });

  const TYPE_COLORS: Record<string, string> = {
    agent: "bg-blue-900 text-blue-300",
    conversation: "bg-green-900 text-green-300",
    user_profile: "bg-purple-900 text-purple-300",
  };

  function getType(key: string) {
    return TYPES.slice(1).find((t) => key.startsWith(t)) || "agent";
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="flex items-center gap-3">
          <Brain size={22} className="text-purple-400" />
          <h1 className="text-xl font-semibold">Memory Viewer</h1>
          <span className="ml-auto text-xs text-gray-500">{memories.length} entries</span>
        </div>

        {/* Add memory */}
        <div className="card">
          <h2 className="font-medium mb-3 text-sm">Store New Memory</h2>
          <form onSubmit={addMemory} className="flex gap-2">
            <input className="input flex-1" placeholder="Key" value={key} onChange={(e) => setKey(e.target.value)} />
            <input className="input flex-1" placeholder="Value" value={value} onChange={(e) => setValue(e.target.value)} />
            <button type="submit" className="btn-primary flex items-center gap-1" disabled={!key.trim() || !value.trim()}>
              <Plus size={16} />
            </button>
          </form>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-1">
            {TYPES.map((t) => (
              <button key={t} onClick={() => setActiveType(t)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${activeType === t ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
                {t}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 ml-auto bg-gray-800 rounded-lg px-3 py-1.5">
            <Search size={14} className="text-gray-500" />
            <input className="bg-transparent text-sm text-gray-100 placeholder-gray-500 outline-none w-40"
              placeholder="Search..." value={filter} onChange={(e) => setFilter(e.target.value)} />
          </div>
        </div>

        {/* Memory list */}
        <div className="card space-y-2">
          {loading && <p className="text-gray-500 text-sm text-center py-6">Loading...</p>}
          {!loading && filtered.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-6">No memories found</p>
          )}
          {filtered.map((m) => {
            const type = getType(m.key);
            const displayKey = m.key.replace(/^(agent|conversation|user_profile):/, "");
            return (
              <div key={m.id} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg text-sm group">
                <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 mt-0.5 ${TYPE_COLORS[type] || "bg-gray-700 text-gray-300"}`}>
                  {type}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-blue-300 truncate">{displayKey}</p>
                  <p className="text-gray-400 mt-0.5 break-words">{m.value}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {m.relevance_score != null && (
                    <span className="text-xs text-gray-600">{m.relevance_score.toFixed(2)}</span>
                  )}
                  <span className="text-xs text-gray-600 hidden group-hover:block">
                    {new Date(m.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
