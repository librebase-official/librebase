import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function IconHome(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" />
    </Icon>
  );
}

export function IconTable(p: IconProps) {
  return (
    <Icon {...p}>
      <rect x="3.5" y="4.5" width="17" height="15" rx="1.5" />
      <path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10M14.5 9.5v10" />
    </Icon>
  );
}

export function IconSql(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M4 7h16M4 12h10M4 17h7" />
    </Icon>
  );
}

export function IconDatabase(p: IconProps) {
  return (
    <Icon {...p}>
      <ellipse cx="12" cy="6" rx="7" ry="2.4" />
      <path d="M5 6v4.5c0 1.3 3.1 2.4 7 2.4s7-1.1 7-2.4V6" />
      <path d="M5 10.5V15c0 1.3 3.1 2.4 7 2.4s7-1.1 7-2.4v-4.5" />
    </Icon>
  );
}

export function IconServer(p: IconProps) {
  return (
    <Icon {...p}>
      <rect x="3.5" y="4" width="17" height="6" rx="1.4" />
      <rect x="3.5" y="14" width="17" height="6" rx="1.4" />
      <path d="M7 7h.01M7 17h.01M10.5 7h4M10.5 17h4" />
    </Icon>
  );
}

export function IconLogs(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M5 5h14v14H5z" />
      <path d="M8 9h8M8 12h8M8 15h5" />
    </Icon>
  );
}

export function IconSettings(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.3.7 1 1.1 1.6 1.1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
    </Icon>
  );
}

export function IconPause(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M10 9v6M14 9v6" />
    </Icon>
  );
}

export function IconSearch(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-3.5-3.5" />
    </Icon>
  );
}

export function IconSun(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
    </Icon>
  );
}

export function IconMoon(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M20 14.5A8 8 0 1 1 9.5 4 6.5 6.5 0 0 0 20 14.5Z" />
    </Icon>
  );
}

export function IconPlus(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M12 5v14M5 12h14" />
    </Icon>
  );
}

export function IconTrash(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M4 7h16M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7" />
      <path d="M6.5 7 7.2 19a1.5 1.5 0 0 0 1.5 1.4h6.6a1.5 1.5 0 0 0 1.5-1.4l.7-12" />
      <path d="M10 11v6M14 11v6" />
    </Icon>
  );
}

export function IconCopy(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M9 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" />
      <path d="M9 9l6-6M9 9V4a2 2 0 0 1 2-2h5a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2h-2" />
    </Icon>
  );
}

export function IconCheck(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M20 6L9 17l-4-4" />
    </Icon>
  );
}

export function IconChevron(p: IconProps) {
  return (
    <Icon width="12" height="12" {...p}>
      <path d="m9 6 4 4-4 4" />
    </Icon>
  );
}

export function IconConnect(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M9 12h6" />
      <path d="M8 8H6.5A3.5 3.5 0 0 0 6.5 15H8" />
      <path d="M16 8h1.5a3.5 3.5 0 1 1 0 7H16" />
    </Icon>
  );
}

export function IconUser(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="12" cy="9" r="3.2" />
      <path d="M5.5 19.2a6.5 6.5 0 0 1 13 0" />
    </Icon>
  );
}

export function IconAuth(p: IconProps) {
  return (
    <Icon {...p}>
      <rect x="6" y="11" width="12" height="9" rx="1.5" />
      <path d="M8.5 11V8a3.5 3.5 0 0 1 7 0v3" />
    </Icon>
  );
}

export function IconKey(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="8" cy="8" r="4" />
      <path d="M11 11l8 8" />
      <path d="M15 15l2-2" />
      <path d="M18 18l2-2" />
    </Icon>
  );
}

export function IconStorage(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M4 7h16v4H4zM4 13h16v4H4z" />
      <path d="M8 9h.01M8 15h.01" />
    </Icon>
  );
}

export function IconEdge(p: IconProps) {
  return (
    <Icon {...p}>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v8M9 11l3-3 3 3" />
    </Icon>
  );
}

export function IconRealtime(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M4 12a8 8 0 0 1 16 0" />
      <path d="M7 12a5 5 0 0 1 10 0" />
      <path d="M10 12a2 2 0 0 1 4 0" />
      <circle cx="12" cy="16" r="1.2" fill="currentColor" stroke="none" />
    </Icon>
  );
}

export function IconShield(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M12 3 5 6v6c0 4 3 6.5 7 8 4-1.5 7-4 7-8V6l-7-3Z" />
    </Icon>
  );
}

export function IconMark(p: IconProps) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...p}>
      <rect x="1" y="1" width="16" height="16" rx="4" fill="var(--accent)" />
      <rect x="4.2" y="5" width="9.6" height="2" rx="1" fill="var(--accent-on)" />
      <rect x="4.2" y="8" width="7.2" height="2" rx="1" fill="var(--accent-on)" opacity="0.85" />
      <rect x="4.2" y="11" width="4.6" height="2" rx="1" fill="var(--accent-on)" opacity="0.65" />
    </svg>
  );
}

export function IconAgent(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M12 2a3 3 0 0 1 5 2v4a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V4a3 3 0 0 1 5-2h1z" />
      <circle cx="12" cy="11" r="1.5" fill="currentColor" stroke="none" />
      <path d="M6 13a5 5 0 0 1 5-2" />
    </Icon>
  );
}

export function IconBot(p: IconProps) {
  return (
    <Icon {...p}>
      <rect x="4" y="5" width="16" height="12" rx="2" />
      <circle cx="8.5" cy="9.5" r="1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="9.5" r="1" fill="currentColor" stroke="none" />
      <path d="M9 15c0-1 .5-2 2-2h2" />
    </Icon>
  );
}

export function IconChart(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M3 18V9h4v9" />
      <path d="M7 18V5h4v13" />
      <path d="M11 18V10h4v8" />
      <path d="M3 18h18" />
    </Icon>
  );
}

export function IconTodo(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M9 13l2 2 4-4" />
      <path d="M4 7h16M4 12h16" />
      <rect x="7" y="3" width="10" height="16" rx="2" />
    </Icon>
  );
}

export function IconTrend(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="M3 17l8-8 4 4 8-8" />
      <path d="M15 17V5h2v12" />
      <path d="M9 17V9h2v8" />
    </Icon>
  );
}

export function IconSend(p: IconProps) {
  return (
    <Icon {...p}>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </Icon>
  );
}
