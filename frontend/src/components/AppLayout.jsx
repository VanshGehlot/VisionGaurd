import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import TopStatusBar from "./TopStatusBar";

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    return localStorage.getItem("visionguard.sidebar.open") !== "false";
  });
  const [sidebarPinned, setSidebarPinned] = useState(() => {
    return localStorage.getItem("visionguard.sidebar.pinned") !== "false";
  });
  const [sidebarCompact, setSidebarCompact] = useState(() => {
    return localStorage.getItem("visionguard.sidebar.compact") === "true";
  });

  useEffect(() => {
    localStorage.setItem("visionguard.sidebar.open", String(sidebarOpen));
  }, [sidebarOpen]);

  useEffect(() => {
    localStorage.setItem("visionguard.sidebar.pinned", String(sidebarPinned));
  }, [sidebarPinned]);

  useEffect(() => {
    localStorage.setItem("visionguard.sidebar.compact", String(sidebarCompact));
  }, [sidebarCompact]);

  const shellClass = [
    "product-shell",
    sidebarOpen ? "sidebar-is-open" : "sidebar-is-closed",
    sidebarPinned ? "sidebar-is-pinned" : "sidebar-is-unpinned",
    sidebarCompact ? "sidebar-is-compact" : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={shellClass}>
      <Sidebar
        isOpen={sidebarOpen}
        isPinned={sidebarPinned}
        isCompact={sidebarCompact}
        onToggleOpen={() => setSidebarOpen((value) => !value)}
        onTogglePinned={() => {
          setSidebarPinned((value) => !value);
          setSidebarOpen(true);
        }}
        onToggleCompact={() => {
          setSidebarCompact((value) => !value);
          setSidebarOpen(true);
        }}
      />
      <div className="product-main">
        <TopStatusBar onToggleSidebar={() => setSidebarOpen((value) => !value)} />
        <main className="product-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
