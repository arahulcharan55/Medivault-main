"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, getProfile, UserProfile } from "@/lib/api";
import { useEffect, useState } from "react";

const patientLinks = [
  ["Dashboard", "/dashboard"],
  ["Upload", "/upload"],
  ["Documents", "/documents"],
  ["Timeline", "/timeline"],
  ["Consents", "/consents"],
  ["Audit", "/audit"],
];

const doctorLinks = [["Portal", "/doctor"]];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    setProfile(getProfile<UserProfile>());
  }, [pathname]);

  if (pathname === "/" || pathname.startsWith("/login") || pathname.startsWith("/register")) return null;

  const links = profile?.role === "doctor" ? doctorLinks : patientLinks;

  return (
    <header className="sticky top-0 z-20 border-b border-teal-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href={profile?.role === "doctor" ? "/doctor" : "/dashboard"} className="text-lg font-semibold tracking-tight text-teal-800">
          MediVault
        </Link>
        <nav className="hidden gap-4 text-sm md:flex">
          {links.map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className={pathname === href || pathname.startsWith(`${href}/`) ? "font-semibold text-teal-700" : "text-slate-600 hover:text-teal-700"}
            >
              {label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden text-xs text-slate-500 sm:inline">{profile?.name}</span>
          <button
            className="rounded-lg bg-slate-100 px-3 py-1 text-sm hover:bg-slate-200"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
