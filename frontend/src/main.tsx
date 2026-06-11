import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import "./index.css";
import { Layout } from "@/components/Layout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ArticlesPage } from "@/features/articles/ArticlesPage";
import { BatchZeroPage } from "@/features/batch-zero/BatchZeroPage";
import { BrandSpecsPage } from "@/features/brand-specs/BrandSpecsPage";
import { LedgerPage } from "@/features/certificate-ledger/LedgerPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { DevicesPage } from "@/features/devices/DevicesPage";
import { MethodsPage } from "@/features/methods/MethodsPage";
import { ValidationPage } from "@/features/validation/ValidationPage";
import { VerifyPage } from "@/features/verify/VerifyPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { TestJobsPage } from "@/features/test-jobs/TestJobsPage";
import { AuthProvider } from "@/lib/auth";
import { queryClient } from "@/lib/queryClient";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/verify/:id" element={<VerifyPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route index element={<DashboardPage />} />
                <Route path="/brand-specs" element={<BrandSpecsPage />} />
                <Route path="/articles" element={<ArticlesPage />} />
                <Route path="/batch-zero" element={<BatchZeroPage />} />
                <Route path="/test-jobs" element={<TestJobsPage />} />
                <Route path="/methods" element={<MethodsPage />} />
                <Route path="/validation" element={<ValidationPage />} />
                <Route path="/ledger" element={<LedgerPage />} />
                <Route path="/devices" element={<DevicesPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
