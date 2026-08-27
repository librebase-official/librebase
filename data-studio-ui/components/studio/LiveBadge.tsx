import { Badge, type BadgeVariant } from "@/components/ui/badge";

export function LiveBadge({
  variant,
  label,
  spinner,
  className,
}: {
  variant: BadgeVariant;
  label: string;
  spinner?: boolean;
  className?: string;
}) {
  return (
    <Badge variant={variant} className={className}>
      {spinner ? <span className="spinner" style={{ width: 10, height: 10 }} /> : null}
      {label}
    </Badge>
  );
}
