import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variantClasses: Record<Variant, string> = {
  primary: "bg-ink-800 text-linen-50 hover:bg-ink-700",
  secondary: "bg-linen-100 text-ink-800 hover:bg-linen-200 border border-linen-200",
  ghost: "bg-transparent text-ink-700 hover:bg-linen-100",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center rounded-xl px-5 py-3 text-sm font-medium
          transition-colors disabled:opacity-50 disabled:pointer-events-none
          ${variantClasses[variant]} ${className}`}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
