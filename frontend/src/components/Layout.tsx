import { NavLink, Outlet } from "react-router-dom";

import { Icon, type IconName } from "@/components/icons";
import { useAuth } from "@/lib/auth";

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/brand-specs", label: "Brand", icon: "tag" },
  { to: "/articles", label: "Articoli", icon: "layers" },
  { to: "/batch-zero", label: "Batch", icon: "beaker" },
  { to: "/test-jobs", label: "Prove", icon: "clipboard" },
  { to: "/methods", label: "Norme", icon: "book" },
  { to: "/validation", label: "Validazione", icon: "check" },
  { to: "/ledger", label: "Report", icon: "doc" },
  { to: "/devices", label: "Device", icon: "device" },
];

export function Layout() {
  const { profile, logout } = useAuth();

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
            className="grid h-9 w-9 place-items-center rounded-lg text-steel hover:bg-slate-100"
          >
            <Icon name="logout" />
          </button>
        </div>
      </header>

      <div className="md:flex">
        {/* desktop sidebar */}
        <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white p-3 md:block">
          <nav className="space-y-1">
            {NAV.map((n) => (
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

        {/* content */}
        <main className="mx-auto w-full max-w-5xl flex-1 p-4 pb-24 md:p-6 md:pb-8">
          <Outlet />
        </main>
      </div>

      {/* mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-9 border-t border-slate-200 bg-white md:hidden">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium ${
                isActive ? "text-brand-600" : "text-steel"
              }`
            }
          >
            <Icon name={n.icon} width={22} height={22} />
            {n.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
