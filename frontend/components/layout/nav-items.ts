import { MessageSquare, FileText, Search, Settings } from "lucide-react";

// Deliberately just these four - Dashboard/History/Collections/Analytics
// were cut from v1 because the backend has no aggregate stats,
// conversation-listing, or collection endpoints to back them (see
// frontend/docs/API-INTEGRATION.md).
export const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/search", label: "Search", icon: Search },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;
