"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { clearAuth, getCurrentUser, STAFF_ROLES, ADMIN_ROLES } from "@/lib/auth";
import { useRouter } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  allowedRoles?: string[]; // undefined = all authenticated roles
}

const ALL_NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    allowedRoles: [...STAFF_ROLES],
  },
  {
    href: "/query",
    label: "Query",
    icon: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  {
    href: "/knowledge-bases",
    label: "Knowledge Bases",
    icon: "M4 6h16M4 10h16M4 14h16M4 18h16",
  },
  {
    href: "/admin",
    label: "Admin",
    icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
    allowedRoles: [...ADMIN_ROLES],
  },
];

function getRoleLabel(role: string | null): string {
  if (!role) return "User";
  const labels: Record<string, string> = {
    admin: "Administrator",
    psychologist: "Psychologist",
    rehab_staff: "Rehab Staff",
    hospital_admin: "Hospital Admin",
    researcher: "Researcher",
    doctor: "Doctor",
    student: "Student",
  };
  return labels[role] ?? role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getCurrentUser();
  const userRole = user?.role ?? null;

  const visibleItems = ALL_NAV_ITEMS.filter((item) => {
    if (!item.allowedRoles) return true;
    return userRole && item.allowedRoles.includes(userRole);
  });

  const displayName = user?.username ?? user?.full_name ?? "User";

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-gray-100">
        <Link href={STAFF_ROLES.includes(userRole ?? "") ? "/dashboard" : "/knowledge-bases"}>
          <Image
            src="/curamind-logo.png"
            alt="CuraMind"
            width={148}
            height={50}
            className="object-contain mix-blend-multiply"
            priority
          />
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {visibleItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                ${isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={item.icon} />
              </svg>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info + logout */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-blue-700 text-sm font-bold uppercase">
              {displayName.charAt(0)}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-gray-900 truncate">{displayName}</p>
            <p className="text-xs text-gray-500">{getRoleLabel(userRole)}</p>
          </div>
        </div>
        <button onClick={handleLogout} className="btn-secondary w-full text-xs py-1.5">
          Sign out
        </button>
      </div>
    </aside>
  );
}
