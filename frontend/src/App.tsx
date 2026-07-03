import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/hooks/useTheme";
import { AuthProvider } from "@/hooks/useAuth";
import ProtectedRoute from "@/routes/ProtectedRoute";
import Sidebar from "@/components/Sidebar";
import DashboardPage from "@/pages/Dashboard/DashboardPage";
import AccountsPage from "@/pages/Accounts/AccountsPage";
import GalleryPage from "@/pages/Gallery/GalleryPage";
import SettingsPage from "@/pages/Settings/SettingsPage";
import SetupWizard from "@/pages/Setup/SetupWizard";
import LoginPage from "@/pages/Login/LoginPage";
import AboutPage from "@/pages/About/AboutPage";
import NotFound from "@/pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/setup" element={<SetupWizard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <div className="flex h-screen bg-gray-950 text-gray-200">
                    <Sidebar />
                    <main className="ml-16 flex-1 overflow-y-auto p-6 lg:ml-56 lg:p-8">
                      <Routes>
                        <Route path="/" element={<DashboardPage />} />
                        <Route path="/accounts" element={<AccountsPage />} />
                        <Route path="/gallery" element={<GalleryPage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/about" element={<AboutPage />} />
                        <Route path="*" element={<NotFound />} />
                      </Routes>
                    </main>
                  </div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
