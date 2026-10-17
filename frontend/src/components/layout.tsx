import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, Menu, Moon, Package, ShoppingBag, Sun, X } from "lucide-react";
import { useTheme } from "../hooks/use-theme";

const links = [
  { to: "/", label: "Order groceries", icon: ShoppingBag, end: true },
  { to: "/products", label: "The shelves", icon: Package },
  { to: "/orders", label: "Your orders", icon: ShoppingBag },
  { to: "/shopkeeper", label: "Shopkeeper", icon: LayoutDashboard },
];

export function Layout() {
  const { resolvedTheme, setTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const dark = resolvedTheme === "dark";

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <NavLink to="/" className="brand" aria-label="DukaanVoice home" onClick={() => setMenuOpen(false)}>
            <span className="brand-mark">d.</span>
            <span className="brand-copy"><strong>DukaanVoice</strong><small>Your neighbourhood, in good hands</small></span>
          </NavLink>
          <nav className={`main-nav ${menuOpen ? "nav-open" : ""}`} aria-label="Main navigation">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
                <Icon size={16} aria-hidden="true" /><span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="header-actions">
            <button className="icon-button theme-button" aria-label={`Switch to ${dark ? "light" : "dark"} mode`} title={`Switch to ${dark ? "light" : "dark"} mode`} onClick={() => setTheme(dark ? "light" : "dark")}>
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <NavLink to="/settings" className={({ isActive }) => `settings-link ${isActive ? "active" : ""}`}>Settings</NavLink>
            <button className="icon-button mobile-menu" aria-label={menuOpen ? "Close navigation" : "Open navigation"} onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X size={21} /> : <Menu size={21} />}
            </button>
          </div>
        </div>
      </header>
      <main className="main-content"><Outlet /></main>
      <footer className="site-footer">
        <span className="footer-mark">d.</span>
        <span>Made for the shops that make a neighbourhood.</span>
        <span className="footer-note">A small-shop kind of service.</span>
      </footer>
    </div>
  );
}
