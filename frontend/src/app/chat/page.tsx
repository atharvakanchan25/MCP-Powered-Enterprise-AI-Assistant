"use client";
import { useState, useRef, useEffect } from "react";
import { agentApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import Sidebar from "@/components/Sidebar";
import { Send, Loader2, ChevronDown, ChevronRight, Wrench, BookOpen } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  plan?: string;
  reasoning?: string[];
  toolResults?: object[];
  citations?: object[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState<string | undefined>();
  const [showTrace, setShowTrace] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const { data } = await agentApi.query(userMsg, convId);
      setConvId(data.conversation_id);
      setMessages((m) => [...m, {
        role: "assistant",
        content: data.answer,
        plan: data.plan,
        reasoning: data.reasoning,
        toolResults: data.tool_results,
        citations: data.citations,
      }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "An error occurred. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="border-b border-gray-800 px-6 py-4">
          <h1 className="font-semibold">AI Chat</h1>
          {convId && <p className="text-xs text-gray-500">Conversation: {convId.slice(0, 8)}...</p>}
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg mb-2">Ask anything</p>
              <p className="text-sm">Powered by MCP agents, RAG, and tool calling</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-3xl w-full ${msg.role === "user" ? "ml-12" : "mr-12"}`}>
                <div className={`rounded-xl px-4 py-3 ${msg.role === "user" ? "bg-blue-600 ml-auto max-w-xl" : "bg-gray-800"}`}>
                  <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                    {msg.content}
                  </ReactMarkdown>
                </div>

                {/* Reasoning Trace */}
                {msg.role === "assistant" && (msg.reasoning?.length || msg.toolResults?.length || msg.citations?.length) ? (
                  <div className="mt-2">
                    <button onClick={() => setShowTrace(showTrace === i ? null : i)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300">
                      {showTrace === i ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      View reasoning & sources
                    </button>
                    {showTrace === i && (
                      <div className="mt-2 space-y-2 text-xs">
                        {msg.plan && (
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <p className="text-blue-400 font-medium mb-1">Plan</p>
                            <p className="text-gray-300">{msg.plan}</p>
                          </div>
                        )}
                        {msg.toolResults && msg.toolResults.length > 0 && (
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <p className="text-yellow-400 font-medium mb-2 flex items-center gap-1">
                              <Wrench size={11} /> Tool Calls
                            </p>
                            {msg.toolResults.map((tr: any, j) => (
                              <div key={j} className={`mb-1 px-2 py-1 rounded ${tr.success ? "bg-green-900/30" : "bg-red-900/30"}`}>
                                <span className="font-mono">{tr.tool}</span>
                                <span className={`ml-2 ${tr.success ? "text-green-400" : "text-red-400"}`}>
                                  {tr.success ? "✓" : "✗"} {tr.duration_ms}ms
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <p className="text-purple-400 font-medium mb-2 flex items-center gap-1">
                              <BookOpen size={11} /> Sources
                            </p>
                            {msg.citations.map((c: any, j) => (
                              <div key={j} className="mb-1 text-gray-400">
                                📄 {c.filename} {c.page && `p.${c.page}`} — score: {c.score}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 rounded-xl px-4 py-3 flex items-center gap-2 text-gray-400">
                <Loader2 size={16} className="animate-spin" /> Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={sendMessage} className="border-t border-gray-800 p-4 flex gap-3">
          <input className="input flex-1" placeholder="Ask anything..." value={input}
            onChange={(e) => setInput(e.target.value)} disabled={loading} />
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading || !input.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
