import type { ReactNode } from "react";
import { IconPause } from "./icons";

export function EmptyState({
  icon,
  title,
  body,
  facts,
  actions,
}: {
  icon?: ReactNode;
  title: string;
  body?: ReactNode;
  facts?: string[];
  actions?: ReactNode;
}) {
  return (
    <div className="st-panel st-empty">
      <div className="st-empty-icon">{icon ?? <IconPause />}</div>
      <h2>{title}</h2>
      {body ? <p>{body}</p> : null}
      {facts && facts.length > 0 ? (
        <ul>
          {facts.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      ) : null}
      {actions ? <div className="st-empty-actions">{actions}</div> : null}
    </div>
  );
}
