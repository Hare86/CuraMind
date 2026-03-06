"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getCurrentUser, STAFF_ROLES } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      const user = getCurrentUser();
      const role = user?.role ?? "student";
      // Staff/admin go to dashboard; students go directly to knowledge bases
      if (STAFF_ROLES.includes(role)) {
        router.replace("/dashboard");
      } else {
        router.replace("/knowledge-bases");
      }
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      <div className="text-center">
        <p className="text-gray-400 text-sm">Redirecting...</p>
      </div>
    </div>
  );
}
