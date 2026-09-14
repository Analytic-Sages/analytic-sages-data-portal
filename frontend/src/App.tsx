import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { CatalogPage } from './pages/CatalogPage'
import { DashboardDetailPage } from './pages/DashboardDetailPage'
import { DashboardsPage } from './pages/DashboardsPage'
import { DatasetDetailPage } from './pages/DatasetDetailPage'
import { EarlyAccessPage } from './pages/EarlyAccessPage'
import { ExplorePage } from './pages/ExplorePage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { HomePage } from './pages/HomePage'
import { LabDetailPage } from './pages/LabDetailPage'
import { LabsPage } from './pages/LabsPage'
import { LoginPage } from './pages/LoginPage'
import { QueryPage } from './pages/QueryPage'
import { PublicSharePage } from './pages/PublicSharePage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { SignupPage } from './pages/SignupPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { VisualizationsPage } from './pages/VisualizationsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="datasets/:slug" element={<DatasetDetailPage />} />
        <Route path="labs" element={<LabsPage />} />
        <Route path="labs/:slug" element={<LabDetailPage />} />
        <Route path="explore" element={<ExplorePage />} />
        <Route path="query" element={<QueryPage />} />
        <Route path="visualizations" element={<VisualizationsPage />} />
        <Route path="dashboards" element={<DashboardsPage />} />
        <Route path="dashboards/:slug" element={<DashboardDetailPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="early-access" element={<EarlyAccessPage />} />
        <Route path="verify-email" element={<VerifyEmailPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password" element={<ResetPasswordPage />} />
        <Route path="charts" element={<Navigate to="/dashboards" replace />} />
        <Route path="library" element={<Navigate to="/visualizations" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
      <Route path="share/:token" element={<PublicSharePage />} />
    </Routes>
  )
}
