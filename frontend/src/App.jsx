import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import LandingPage from "./pages/LandingPage";
import DashboardPage from "./pages/DashboardPage";
import InspectionPage from "./pages/InspectionPage";
import ReportsPage from "./pages/ReportsPage";
import SettingsPage from "./pages/SettingsPage";
import AdaptationPage from "./pages/AdaptationPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/inspection" element={<InspectionPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/adaptation" element={<AdaptationPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
