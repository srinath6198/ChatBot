import { useEffect, useState } from "react";
import Auth from "./components/Auth";
import DocumentSidebar from "./components/DocumentSidebar";
import Chat from "./components/Chat";
import { getMe } from "./api/client";
import type { User } from "./api/client";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setChecked(true);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setChecked(true));
  }, []);

  function handleLogout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  if (!checked) return null;

  if (!user) {
    return (
      <Auth
        onAuthenticated={() => {
          getMe().then(setUser);
        }}
      />
    );
  }

  return (
    <div className="app-shell">
      <div className="sidebar">
        <div>
          <div style={{ fontWeight: 700 }}>{user.full_name ?? user.email}</div>
          <div style={{ fontSize: 12, color: "#9a9fae" }}>{user.role}</div>
        </div>
        <DocumentSidebar />
        <button className="btn-secondary" onClick={handleLogout}>
          Log out
        </button>
      </div>
      <div className="main">
        <div className="topbar">
          <h2 style={{ margin: 0, fontSize: 16 }}>Document Q&A</h2>
        </div>
        <Chat />
      </div>
    </div>
  );
}