import { Route, Routes } from "react-router-dom";
import { Sidebar } from "@/components/sidebar";
import { Dashboard } from "@/pages/Dashboard";
import { Library } from "@/pages/Library";
import { Templates } from "@/pages/Templates";
import { SearchPage } from "@/pages/Search";
import { Builder } from "@/pages/Builder";
import { SettingsPage } from "@/pages/Settings";

export default function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/library" element={<Library />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/builder" element={<Builder />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
