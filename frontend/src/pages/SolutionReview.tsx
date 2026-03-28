import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import MoveList from '@/components/review/MoveList';
import StepNavigator from '@/components/review/StepNavigator';
import { getSolution } from '@/lib/api';

export default function SolutionReview() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [currentStep, setCurrentStep] = useState<number>(0);

  const { data: solution, isLoading, isError } = useQuery({
    queryKey: ['solution', sessionId],
    queryFn: () => getSolution(sessionId!),
    enabled: !!sessionId,
  });

  const steps = solution?.steps ?? [];

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-2xl">
        <Skeleton className="h-8 w-48 bg-slate-800" />
        <Skeleton className="h-96 w-full bg-slate-800" />
      </div>
    );
  }

  if (isError || !solution) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400">Session not found.</p>
        <Link to="/results">
          <Button variant="outline" className="mt-4 border-slate-700 text-slate-300">
            Back to Results
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.22em] text-kl-secondary">PI³</p>
          <h1 className="font-space-grotesk text-3xl font-semibold text-kl-on-surface">Solution Review</h1>
          <p className="font-mono text-xs text-kl-on-surface-variant">Session #{sessionId}</p>
        </div>
        <Link to="/results">
          <Button variant="outline" className="border-kl-outline-variant text-kl-on-surface-variant hover:bg-kl-surface-high">
            <span className="material-symbols-outlined mr-1 text-base" aria-hidden="true">arrow_back</span>
            Back to Results
          </Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-3">
        {solution.algorithm_used && (
          <Badge className="border-kl-primary/40 bg-kl-primary/10 text-kl-primary">
            {solution.algorithm_used}
          </Badge>
        )}
        {steps.length > 0 && (
          <Badge className="border-cyan-400/35 bg-cyan-400/10 font-mono text-cyan-200">
            {steps.length} moves
          </Badge>
        )}
      </div>

      <MoveList steps={steps} currentStep={currentStep} />

      <StepNavigator
        total={steps.length}
        current={currentStep}
        onStep={setCurrentStep}
      />
    </div>
  );
}
