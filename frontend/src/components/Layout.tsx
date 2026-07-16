import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { Icon, type IconName } from "@/components/icons";
import { useAuth } from "@/lib/auth";

type NavItem = { to: string; label: string; icon: IconName; end?: boolean };

// Full navigation (desktop sidebar shows all of it).
const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/brand-specs", label: "Brand", icon: "tag" },
  { to: "/articles", label: "Articoli", icon: "layers" },
  { to: "/batch-zero", label: "Batch", icon: "beaker" },
  { to: "/test-jobs", label: "Prove", icon: "clipboard" },
  { to: "/methods", label: "Norme", icon: "book" },
  { to: "/validation", label: "Validazione", icon: "check" },
  { to: "/spectral", label: "Spettro (R&D)", icon: "sun" },
  { to: "/colorimetry", label: "Colorimetria", icon: "drop" },
  { to: "/ledger", label: "Report", icon: "doc" },
  { to: "/devices", label: "Device", icon: "device" },
];

// Mobile bottom bar shows the 4 most-used, ordered to mirror the workflow
// (input → test → output); the rest live behind "Altro".
const PRIMARY: NavItem[] = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/articles", label: "Articoli", icon: "layers" },
  { to: "/test-jobs", label: "Prove", icon: "clipboard" },
  { to: "/ledger", label: "Report", icon: "doc" },
];
const PRIMARY_PATHS = new Set(PRIMARY.map((n) => n.to));
const SECONDARY: NavItem[] = [
  ...NAV.filter((n) => !PRIMARY_PATHS.has(n.to)),
  { to: "/billing", label: "Abbonamento", icon: "tag" },
];
// Visible to admin + lab_manager only (the API denies operators anyway).
const TEAM_ITEM: NavItem = { to: "/team", label: "Team", icon: "device" };

export function Layout() {
  const { profile, logout } = useAuth();
  const location = useLocation();
  const [moreOpen, setMoreOpen] = useState(false);

  const canSeeTeam = profile?.role === "company_admin" || profile?.role === "lab_manager";
  const nav = canSeeTeam ? [...NAV, TEAM_ITEM] : NAV;
  const secondary = canSeeTeam ? [...SECONDARY, TEAM_ITEM] : SECONDARY;

  const moreActive = secondary.some((n) => location.pathname.startsWith(n.to));

  return (
    <div className="min-h-screen bg-slate-100 text-ink">
      {/* top app bar */}
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            S
          </span>
          <div className="leading-tight">
            <div className="text-sm font-semibold">Solidità 4.0</div>
            <div className="hidden text-[11px] text-steel sm:block">Controllo Qualità Tessile</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <NavLink
            to="/billing"
            title="Abbonamento"
            className="hidden rounded-lg px-2 py-1 text-xs font-medium text-steel hover:bg-slate-100 sm:block"
          >
            Piano
          </NavLink>
          <div className="text-right leading-tight">
            <div className="max-w-[40vw] truncate text-sm font-medium">
              {profile?.companyName ?? "—"}
            </div>
            <div className="text-[11px] uppercase text-steel">{profile?.role ?? ""}</div>
          </div>
          <button
            onClick={logout}
            title="Logout"
            className="grid h-11 w-11 place-items-center rounded-lg text-steel hover:bg-slate-100"
          >
            <Icon name="logout" />
          </button>
        </div>
      </header>

      <div className="md:flex">
        {/* desktop sidebar */}
        <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white p-3 md:block">
          <nav className="space-y-1">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    isActive ? "bg-brand-600 text-white" : "text-steel hover:bg-slate-100"
                  }`
                }
              >
                <Icon name={n.icon} />
                {n.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* content — extra bottom padding on mobile to clear the fixed nav + safe area */}
        <main className="mx-auto w-full max-w-5xl flex-1 p-4 pb-28 md:p-6 md:pb-8">
          <Outlet />
        </main>
      </div>

      {/* mobile "Altro" sheet */}
      {moreOpen && (
        <div className="fixed inset-0 z-30 md:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMoreOpen(false)} />
          <div className="absolute inset-x-0 bottom-0 rounded-t-2xl border-t border-slate-200 bg-white p-4 pb-safe shadow-2xl">
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-slate-300" />
            <div className="mb-3 text-sm font-semibold text-ink">Altro — impostazioni e anagrafiche</div>
            <div className="grid grid-cols-3 gap-2">
              {secondary.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  onClick={() => setMoreOpen(false)}
                  className={({ isActive }) =>
                    `flex flex-col items-center gap-1.5 rounded-xl border px-2 py-3 text-xs font-medium ${
                      isActive
                        ? "border-brand-200 bg-brand-50 text-brand-600"
                        : "border-slate-200 text-steel hover:bg-slate-50"
                    }`
                  }
                >
                  <Icon name={n.icon} width={22} height={22} />
                  <span className="text-center leading-tight">{n.label}</span>
                </NavLink>
              ))}
            </div>
            <button
              onClick={() => setMoreOpen(false)}
              className="mt-3 w-full rounded-lg border border-slate-200 py-2.5 text-sm font-medium text-steel"
            >
              Chiudi
            </button>
          </div>
        </div>
      )}

      {/* mobile bottom nav: 4 primary + Altro */}
      <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-slate-200 bg-white pb-safe md:hidden">
        {PRIMARY.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            onClick={() => setMoreOpen(false)}
            className={({ isActive }) =>
              `flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-[11px] font-medium ${
                isActive ? "text-brand-600" : "text-steel"
              }`
            }
          >
            <Icon name={n.icon} width={22} height={22} />
            {n.label}
          </NavLink>
        ))}
        <button
          onClick={() => setMoreOpen((v) => !v)}
          className={`flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-[11px] font-medium ${
            moreActive || moreOpen ? "text-brand-600" : "text-steel"
          }`}
        >
          <Icon name="more" width={22} height={22} />
          Altro
        </button>
      </nav>
    </div>
  );
}
