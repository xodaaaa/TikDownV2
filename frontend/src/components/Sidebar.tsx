import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Image,
  Settings,
  Info,
  Moon,
  Sun,
} from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/gallery", icon: Image, label: "Gallery" },
  { to: "/accounts", icon: Users, label: "Accounts" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar() {
  const { theme, toggle } = useTheme();

  return (
    <aside
      role="navigation"
      className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col border-r border-gray-800 bg-gray-900 lg:w-56"
    >
      <div className="flex h-14 items-center justify-center border-b border-gray-800 lg:justify-start lg:px-4">
        <span className="text-accent-500 text-lg font-bold lg:text-xl">
          <span className="lg:hidden">T</span>
          <span className="hidden lg:inline">TikDown</span>
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-2" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            aria-current="page"
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "border-l-2 border-accent-500 bg-accent-500/10 text-accent-400"
                  : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
              }`
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            <span className="hidden lg:inline">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto border-t border-gray-800 p-2">
        <button
          onClick={toggle}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-400 transition-colors hover:bg-gray-800/50 hover:text-gray-200"
          aria-label={theme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
        >
          {theme === "dark" ? (
            <Sun className="h-5 w-5 shrink-0" />
          ) : (
            <Moon className="h-5 w-5 shrink-0" />
          )}
          <span className="hidden lg:inline">
            {theme === "dark" ? "Light" : "Dark"}
          </span>
        </button>

        <NavLink
          to="/about"
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
              isActive
                ? "border-l-2 border-accent-500 bg-accent-500/10 text-accent-400"
                : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
            }`
          }
        >
          <Info className="h-5 w-5 shrink-0" />
          <span className="hidden lg:inline">About</span>
        </NavLink>
      </div>
    </aside>
  );
}
