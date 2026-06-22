import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "border-brand-line bg-slate-50 text-slate-600",
        pass: "border-brand-green/40 bg-brand-green/15 text-[#3f6f00]",
        cond: "border-brand-orange/40 bg-brand-orange/12 text-[#b8431f]",
        mock: "border-amber-300/60 bg-amber-50 text-amber-700",
        base: "border-brand-grey/30 bg-brand-grey/10 text-brand-grey",
        brand: "border-brand-blue/30 bg-brand-blue/10 text-brand-blue",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
