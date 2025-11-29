'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Application error:', error);
    }, [error]);

    return (
        <div className="flex min-h-[80vh] flex-col items-center justify-center text-center">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
                <AlertTriangle className="h-12 w-12 text-destructive" />
            </div>
            <h2 className="text-2xl font-semibold">Something went wrong!</h2>
            <p className="mt-2 text-muted-foreground max-w-md">
                An unexpected error occurred. Please try again or contact support if the
                problem persists.
            </p>
            <Button onClick={reset} className="mt-8 gap-2">
                <RefreshCw className="h-4 w-4" />
                Try again
            </Button>
        </div>
    );
}
