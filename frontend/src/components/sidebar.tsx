import {
  FileText,
  LayoutDashboard,
  LayoutTemplate,
  Moon,
  Presentation,
  Search,
  Settings,
  Sun,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/library", label: "Document Library", icon: FileText },
  { to: "/templates", label: "Templates", icon: LayoutTemplate },
  { to: "/search", label: "Search", icon: Search },
  { to: "/builder", label: "Presentation Builder", icon: Presentation },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const { theme, setTheme } = useTheme();
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r bg-card">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <Presentation className="h-5 w-5 text-primary" />
        <span className="font-semibold">Case Study Maker</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t p-3">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-3"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
          {theme === "dark" ? "Light Mode" : "Dark Mode"}
        </Button>
      </div>
    </aside>
  );
}
