import { CircleAlert, CircleCheck, CircleDashed } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const QUALITY_CONFIG: Record<
  string,
  { icon: typeof CircleCheck; className: string }
> = {
  Excellent: {
    icon: CircleCheck,
    className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  Good: {
    icon: CircleDashed,
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  Weak: {
    icon: CircleAlert,
    className: "bg-destructive/10 text-destructive",
  },
};

// quality/bestScore come from app/services/search_evaluator.py's
// SearchEvaluator - it grades the best retrieved chunk's match score
// (best_score >= 0.7 -> Excellent, >= 0.5 -> Good, else Weak). This
// reflects how well the source documents matched the question, not
// whether the LLM's wording was good.
export function AnswerQualityBadge({
  quality,
  bestScore,
}: {
  quality?: string;
  bestScore?: number;
}) {
  if (!quality) return null;

  const config = QUALITY_CONFIG[quality];
  if (!config) return null;

  const Icon = config.icon;
  const percent = typeof bestScore === "number" ? Math.round(bestScore * 100) : null;

  return (
    <Badge
      variant="secondary"
      className={config.className}
      title="How well the source documents matched this question"
    >
      <Icon className="size-3" />
      {quality} match
      {percent !== null && <span className="opacity-70">· {percent}%</span>}
    </Badge>
  );
}
