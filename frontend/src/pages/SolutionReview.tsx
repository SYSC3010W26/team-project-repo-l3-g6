import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
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
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link to="/results">
          <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white">
            <ArrowLeft size={18} />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Solution Review</h1>
          <p className="text-slate-400 text-sm">Session: {sessionId?.substring(0, 12)}...</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        {solution.algorithm && (
          <Badge className="bg-slate-700 text-slate-200 border-slate-600">
            {solution.algorithm}
          </Badge>
        )}
        {steps.length > 0 && (
          <Badge className="bg-slate-700 text-slate-200 border-slate-600">
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
