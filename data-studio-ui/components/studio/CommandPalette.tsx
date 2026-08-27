"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export interface CommandItem {
  id: string;
  label: string;
  href: string;
  group: string;
}

export function CommandPalette({
  open,
  onClose,
  items,
}: {
  open: boolean;
  onClose: () => void;
  items: CommandItem[];
}) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);

  const filtered = useMemo(() => {
    const n = q.trim().toLowerCase();
    if (!n) return items;
    return items.filter((i) => i.label.toLowerCase().includes(n) || i.group.toLowerCase().includes(n));
  }, [items, q]);

  useEffect(() => {
    setActive(0);
  }, [q, open]);

  useEffect(() => {
    if (!open) setQ("");
  }, [open]);

  if (!open) return null;

  function go(href: string) {
    onClose();
    router.push(href);
  }

  return (
    <div className="st-cmd" role="presentation" onClick={onClose}>
      <div
        className="st-cmd-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Search"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          className="st-cmd-input"
          autoFocus
          placeholder="Search pages and actions…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((i) => Math.min(i + 1, filtered.length - 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((i) => Math.max(i - 1, 0));
            }
            if (e.key === "Enter" && filtered[active]) go(filtered[active].href);
          }}
        />
        <div className="st-cmd-list">
          {filtered.length === 0 ? (
            <p className="muted" style={{ padding: "12px 10px" }}>
              No matches.
            </p>
          ) : (
            filtered.map((item, i) => (
              <button
                key={item.id}
                type="button"
                className="st-cmd-item"
                data-active={i === active}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(item.href)}
              >
                {item.label}
                <span>{item.group}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
