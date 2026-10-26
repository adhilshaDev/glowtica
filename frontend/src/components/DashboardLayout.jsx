import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import "./DashboardLayout.css";

import { API_BASE } from "../config";

const navItems = [
  { label: "Dashboard", to: "/home", icon: "▦" },
  { label: "My Products", to: "/products", icon: "◈" },
  { label: "Routine", to: "/routine", icon: "▤" },
  { label: "Tips", to: "/tips", icon: "✎" },
  { label: "My Profile", to: "/profile", icon: "◍" },
];

function DashboardLayout({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    async function getCurrentUser() {
      try {
        const response = await fetch(`${API_BASE}/api/me`, {
          method: "GET",
          credentials: "include",
        });
        const data = await response.json();
        if (!response.ok) {
          window.location.replace("/");
          return;
        }
        setUser(data);
      } catch {
        window.location.replace("/");
      }
    }
    getCurrentUser();
  }, []);

  async function handleLogout() {
    try {
      await fetch(`${API_BASE}/api/logout`, {
        method: "POST",
        credentials: "include",
      });
    } finally {
      window.location.replace("/");
    }
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">✎</span>
          <div>
            <p className="brand-title">Glow Tica</p>
            <p className="brand-subtitle">Skin Essentials</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "nav-item nav-item-active" : "nav-item"
              }
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button className="sidebar-user" onClick={handleLogout} title="Log out">
          <span className="user-avatar" style={{ overflow: "hidden" }}>
            {user?.avatar_base64 ? (
              <img
                src={user.avatar_base64}
                alt={user.name || "User avatar"}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : user?.name ? (
              user.name.charAt(0).toUpperCase()
            ) : (
              "?"
            )}
          </span>
          <span className="user-info">

            <span className="user-name">{user?.name || "Loading..."}</span>
            <span className="user-plan">Premium Plan</span>
          </span>
        </button>
      </aside>

      <main className="dashboard-main">{children}</main>
    </div>
  );
}

export default DashboardLayout;