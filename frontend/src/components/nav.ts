export const NAV_ITEMS = [
  { href: "/", label: "Overview", glyph: "◈" },
  { href: "/dashboard", label: "Dashboard", glyph: "▦" },
  { href: "/investigation", label: "Investigation", glyph: "⌖" },
  { href: "/decision-lab", label: "Decision Lab", glyph: "◇" },
  { href: "/reports", label: "Reports", glyph: "▤" },
] as const;

export function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
