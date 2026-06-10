import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/lib/auth";

export function ProtectedRoute() {
  const { isAuthed, hasTenant } = useAuth();
  if (!isAuthed || !hasTenant) return <Navigate to="/login" replace />;
  return <Outlet />;
}
