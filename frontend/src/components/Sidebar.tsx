"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, FileText, Eye, Brain, Settings, LayoutDashboard, LogOut } from "lucide-react";
import { useAuthStore } from "@/hooks/useAuth";
import { clsx } from "clsx";

const NAV = [
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/documents", icon: FileText, label: "Documents" },
  { href: "/vision", icon: Eye, label: "Vision" },
  { href: "/memory", icon: Brain, label: "Memory" },
  { href: "/settings", icon: Settings, label: "Settings" },
  { href: "/admin", icon: LayoutDashboard, label: "Admin" },
];

export default function Sidebar() {
  const path = usePathname();
  const { logout } = useAuthStore();

  return (
    <aside className="w-16 lg:w-56 bg-gray-900 border-r border-gray-800 flex flex-col h-screen sticky top-0">
      <div className="p-4 border-b border-gray-800">
        <span className="hidden lg:block font-bold text-blue-400 truncate">MCP Assistant</span>
        <span className="lg:hidden text-blue-400 text-xl font-bold">M</span>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {NAV.map(({ href, icon: Icon, label }) => (
          <Link key={href} href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              path.startsWith(href) ? "bg-blue-600 text-white" : "text-gray-400 hover:bg-gray-800 hover:text-white"
            )}>
            <Icon size={18} />
            <span className="hidden lg:block">{label}</span>
          </Link>
        ))}
      </nav>
      <button onClick={logout}
        className="flex items-center gap-3 px-5 py-4 text-gray-400 hover:text-white text-sm border-t border-gray-800">
        <LogOut size={18} />
        <span className="hidden lg:block">Logout</span>
      </button>
    </aside>
  );
}
