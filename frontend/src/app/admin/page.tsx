"use client";
import { useEffect, useState } from "react";
import { adminApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Users, MessageSquare, Wrench, FileText, Activity, Coins, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [tokenStats, setTokenStats] = useState<any>(null);
  const [errors, setErrors] = useState<any[]>([]);

  useEffect(() => {
    adminApi.dashboard().then(({ data }) => setStats(data)).catch(() => null);
    adminApi.auditLogs(20).then(({ data }) => setLogs(data)).catch(() => null);
    adminApi.tokenStats().then(({ data }) => setTokenStats(data)).catch(() => null);
    adminApi.errorLogs(10).then(({ data }) => setErrors(data)).catch(() => null);
  }, []);

  const STAT_CARDS = stats ? [
    { label: "Users", value: stats.total_users, icon: Users, color: "text-blue-400" },
    { label: "Conversations", value: stats.total_conversations, icon: MessageSquare, color: "text-green-400" },
    { label: "Tool Calls", value: stats.total_tool_calls, icon: Wrench, color: "text-yellow-400" },
    { label: "Documents", value: stats.total_documents, icon: FileText, color: "text-purple-400" },
    { label: "Messages", value: stats.total_messages, icon: Activity, color: "text-red-400" },
  ] : [];

  const chartData = STAT_CARDS.map((s) => ({ name: s.label, value: s.value }));

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <h1 className="text-xl font-semibold">Admin Dashboard</h1>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {STAT_CARDS.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card">
              <Icon className={`${color} mb-2`} size={20} />
              <p className="text-2xl font-bold">{value?.toLocaleString()}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          ))}
        </div>

        {/* Token monitoring */}
        {tokenStats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Total Tokens", value: tokenStats.total_tokens, icon: Coins, color: "text-yellow-400" },
              { label: "Prompt Tokens", value: tokenStats.prompt_tokens, icon: Coins, color: "text-blue-400" },
              { label: "Completion Tokens", value: tokenStats.completion_tokens, icon: Coins, color: "text-green-400" },
              { label: "Requests Tracked", value: tokenStats.requests_tracked, icon: Activity, color: "text-purple-400" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="card">
                <Icon className={`${color} mb-2`} size={18} />
                <p className="text-xl font-bold">{value?.toLocaleString()}</p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="card">
            <h2 className="font-medium mb-4">Overview</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Error tracking */}
        {errors.length > 0 && (
          <div className="card overflow-hidden">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={16} className="text-red-400" />
              <h2 className="font-medium">Recent Errors</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-400 text-left">
                    <th className="pb-2 pr-4">Path</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {errors.map((e, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 font-mono text-xs text-red-300">{e.path}</td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">{e.error_type}</td>
                      <td className="py-2 pr-4 text-gray-500 text-xs">{e.status_code}</td>
                      <td className="py-2 text-gray-500 text-xs">{new Date(e.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Audit Logs */}
        <div className="card overflow-hidden">
          <h2 className="font-medium mb-4">Recent Audit Logs</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 text-left">
                  <th className="pb-2 pr-4">Action</th>
                  <th className="pb-2 pr-4">Resource</th>
                  <th className="pb-2 pr-4">IP</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-800/50">
                    <td className="py-2 pr-4 font-mono text-xs text-blue-300">{log.action}</td>
                    <td className="py-2 pr-4 text-gray-400">{log.resource_type || "-"}</td>
                    <td className="py-2 pr-4 text-gray-500 text-xs">{log.ip_address || "-"}</td>
                    <td className="py-2 text-gray-500 text-xs">{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr><td colSpan={4} className="py-4 text-center text-gray-500">No logs yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
