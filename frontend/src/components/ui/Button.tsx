import {
  type AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  type ForwardedRef,
  forwardRef,
} from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "ghost" | "outline";

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "href"> {
  variant?: ButtonVariant;
  /** When set, renders as `<a>` (valid markup for navigation CTAs). */
  href?: string;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-ink text-canvas h-9 px-4 rounded-md font-sans text-body-sm font-medium " +
    "hover:bg-[#f1f7fe] active:bg-[#f1f7fe] transition-colors " +
    "mobile:h-11",
  ghost:
    "bg-surface-elevated text-ink border border-hairline-strong h-9 px-4 rounded-md font-sans text-body-sm " +
    "hover:bg-surface-card transition-colors mobile:h-11",
  outline:
    "bg-canvas text-ink border border-hairline-strong h-9 px-4 rounded-md font-sans text-body-sm " +
    "hover:bg-surface-card transition-colors mobile:h-11",
};

export const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, ButtonProps>(
  ({ variant = "primary", className, href, type = "button", disabled, ...props }, ref) => {
    const classes = cn(variantClasses[variant], className);
    if (href) {
      return (
        <a
          ref={ref as ForwardedRef<HTMLAnchorElement>}
          href={href}
          className={cn(classes, disabled && "pointer-events-none opacity-60")}
          aria-disabled={disabled || undefined}
          {...(props as AnchorHTMLAttributes<HTMLAnchorElement>)}
        />
      );
    }
    return (
      <button
        ref={ref as ForwardedRef<HTMLButtonElement>}
        type={type}
        disabled={disabled}
        className={classes}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
