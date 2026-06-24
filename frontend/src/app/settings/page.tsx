"use client";
import { useEffect, useState } from "react";
import { agentApi } from "@/lib/api";
import { useAuthStore } from "@/hooks/useAuth";
import Sidebar from "@/components/Sidebar";
import { Brain, Plus } from "lucide-react";

export default function SettingsPage() {
  const { user, fetchMe } = useAuthStore();
  const [memories, setMemories] = useState<any[]>([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");

  useEffect(() => {
    fetchMe();
    agentApi.getMemory().then(({ data }) => setMemories(data)).catch(() => null);
  }, []);

  async function addMemory(e: React.FormEvent) {
    e.preventDefault();
    await agentApi.storeMemory(key, value);
    const { data } = await agentApi.getMemory();
    setMemories(data);
    setKey("");
    setValue("");
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <h1 className="text-xl font-semibold">Settings</h1>

        {/* Profile */}
        {user && (
          <div className="card">
            <h2 className="font-medium mb-4">Profile</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {[["Username", user.username], ["Email", user.email], ["Role", user.role], ["ID", user.id.slice(0, 8) + "..."]].map(([label, val]) => (
                <div key={label}>
                  <p className="text-gray-500">{label}</p>
                  <p className="font-medium">{val}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Memory Viewer */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={18} className="text-purple-400" />
            <h2 className="font-medium">Agent Memory</h2>
          </div>
          <form onSubmit={addMemory} className="flex gap-2 mb-4">
            <input className="input flex-1" placeholder="Key" value={key} onChange={(e) => setKey(e.target.value)} />
            <input className="input flex-1" placeholder="Value" value={value} onChange={(e) => setValue(e.target.value)} />
            <button type="submit" className="btn-primary flex items-center gap-1">
              <Plus size={16} />
            </button>
          </form>
          <div className="space-y-2">
            {memories.map((m) => (
              <div key={m.id} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg text-sm">
                <span className="font-mono text-blue-300 shrink-0">{m.key}</span>
                <span className="text-gray-400">{m.value}</span>
                {m.relevance_score && <span className="ml-auto text-xs text-gray-600">{m.relevance_score.toFixed(2)}</span>}
              </div>
            ))}
            {memories.length === 0 && <p className="text-gray-500 text-sm text-center py-4">No memories stored yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
