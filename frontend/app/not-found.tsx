import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
    return (
        <div className="flex min-h-[80vh] flex-col items-center justify-center text-center">
            <h1 className="text-9xl font-bold text-muted-foreground/30">404</h1>
            <h2 className="mt-4 text-2xl font-semibold">Page Not Found</h2>
            <p className="mt-2 text-muted-foreground max-w-md">
                Sorry, we couldn't find the page you're looking for. It might have been
                moved or deleted.
            </p>
            <div className="mt-8 flex gap-4">
                <Link href="/">
                    <Button className="gap-2">
                        <Home className="h-4 w-4" />
                        Go Home
                    </Button>
                </Link>
                <Button variant="outline" onClick={() => window.history.back()}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Go Back
                </Button>
            </div>
        </div>
    );
}
