"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Home and Talk are wired to real screens as of Phase 2. Coach and You are
// still placeholders for later phases.
const items = [
  { href: "/dashboard", label: "Home" },
  { href: "/chat", label: "Talk" },
  { href: "/dashboard", label: "Coach" },
  { href: "/dashboard", label: "You" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 border-t border-linen-200 bg-linen-50/95 backdrop-blur">
      <ul className="mx-auto flex max-w-md justify-between px-6 py-3 sm:max-w-lg">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <li key={item.label}>
              <Link
                href={item.href}
                className={`font-body text-xs ${
                  active ? "text-ink-900 font-medium" : "text-ink-600"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
