"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/hooks/useAuth";

export default function HomePage() {
  const { login } = useAuthStore();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/chat");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-2">MCP AI Assistant</h1>
        <p className="text-gray-400 text-center mb-8 text-sm">Enterprise-grade AI powered by MCP</p>
        <form onSubmit={handleLogin} className="space-y-4">
          <input className="input" type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} required />
          <input className="input" type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
