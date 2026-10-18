import Image from "next/image";
import Link from "next/link";
import type { ComponentProps } from "react";

type Props = {
  href?: string;
  size?: "sm" | "md" | "lg";
  variant?: "studio" | "marketing";
  className?: string;
} & Omit<ComponentProps<"div">, "children">;

const sizes = { sm: 22, md: 28, lg: 36 } as const;

export function BrandWordmark({
  href,
  size = "md",
  variant = "studio",
  className = "",
  ...rest
}: Props) {
  const px = sizes[size];
  const textClass = variant === "marketing" ? "lb-wordmark" : "st-wordmark";
  const textStyle =
    variant === "studio"
      ? { border: 0, padding: 0, height: "auto", fontSize: size === "lg" ? "1.05rem" : "0.92rem" }
      : { fontSize: size === "lg" ? "1.15rem" : size === "sm" ? "0.95rem" : "1.05rem" };

  const inner = (
    <>
      <Image src="/brand/librebase-mark.svg" alt="" width={px} height={px} priority />
      <span className={textClass} style={textStyle}>
        Libre<em>base</em>
      </span>
    </>
  );

  const style = {
    display: "inline-flex",
    alignItems: "center",
    gap: size === "sm" ? 8 : 10,
    textDecoration: "none",
    color: "inherit",
  } as const;

  if (href) {
    return (
      <Link href={href} className={className} style={style}>
        {inner}
      </Link>
    );
  }

  return (
    <div className={className} style={style} {...rest}>
      {inner}
    </div>
  );
}
