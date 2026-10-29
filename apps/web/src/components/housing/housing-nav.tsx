"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2 as BuildingOffice2Icon,
  Home as HomeModernIcon,
  Key as KeyIcon,
  FileCheck2 as DocumentCheckIcon,
  ShieldCheck as ShieldCheckIcon,
  Wrench as WrenchScrewdriverIcon,
  BarChart3 as ChartBarIcon,
  Users as UserGroupIcon,
  Inbox as InboxStackIcon,
  ClipboardCheck as ClipboardDocumentListIcon,
  ArrowRightLeft as ArrowPathRoundedSquareIcon,
  LucideIcon,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Housing Hub", href: "/app/housing", icon: HomeModernIcon },
  { name: "Properties", href: "/app/housing/properties", icon: BuildingOffice2Icon },
  { name: "Providers & Landlords", href: "/app/housing/providers", icon: UserGroupIcon },
  { name: "Unit & Bed Inventory", href: "/app/housing/inventory", icon: KeyIcon },
  { name: "Requests & Waitlist", href: "/app/housing/requests", icon: InboxStackIcon, badge: "Active" },
  { name: "Allocations & Offers", href: "/app/housing/allocations", icon: ArrowPathRoundedSquareIcon },
  { name: "Leases & Agreements", href: "/app/housing/agreements", icon: DocumentCheckIcon },
  { name: "Check-In / Out", href: "/app/housing/check-in-out", icon: ClipboardDocumentListIcon },
  { name: "Inspections & Safety", href: "/app/housing/inspections", icon: ShieldCheckIcon },
  { name: "Maintenance", href: "/app/housing/maintenance", icon: WrenchScrewdriverIcon },
  { name: "Occupancy Analytics", href: "/app/housing/analytics", icon: ChartBarIcon },
];

export function HousingNav({ title, subtitle }: { title?: string; subtitle?: string }) {
  const pathname = usePathname();

  return (
    <div className="bg-white border-b border-gray-200 mb-6">
      {/* Header section with CampusOS brand identity */}
      <div className="px-6 pt-6 pb-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                CampusOS Residential Life
              </span>
              <span className="text-xs text-gray-500">
                “One Campus. One System. One Source of Truth.”
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">
              {title || "Student Housing, Accommodation & Compliance"}
            </h1>
            <p className="text-sm text-gray-600 mt-0.5">
              {subtitle ||
                "Enterprise administration of on-campus halls, approved private accommodations, allocations, digital leases, and safety inspections."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Live Inventory Synced
            </span>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="px-6 flex overflow-x-auto space-x-1 border-t border-gray-100 scrollbar-none">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/app/housing"
              ? pathname === "/app/housing"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-3.5 py-3 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
                isActive
                  ? "border-indigo-600 text-indigo-600 font-semibold"
                  : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.name}</span>
              {item.badge && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

