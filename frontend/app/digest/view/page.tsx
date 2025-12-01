'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useRequireAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { getDigest } from '@/lib/api';
import { renderFullContent } from '@/lib/markdown';
import type { DigestDetail } from '@/lib/types';
import {
    Loader2,
    ArrowLeft,
    Calendar,
    FileText,
    ExternalLink,
    BookOpen,
    RefreshCw,
} from 'lucide-react';

/**
 * Digest Detail Content Component
 * Uses useSearchParams which requires Suspense boundary
 */
function DigestDetailContent() {
    const searchParams = useSearchParams();
    const id = searchParams.get('id');
    const { isLoading: authLoading } = useRequireAuth();
    const { toast } = useToast();

    const [digest, setDigest] = useState<DigestDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDigest = useCallback(async () => {
        if (!id) {
            console.log('[DigestDetail] No ID provided');
            setError('No digest ID provided');
            setIsLoading(false);
            return;
        }

        console.log('[DigestDetail] Fetching digest:', id);
        setIsLoading(true);
        setError(null);

        try {
            const data = await getDigest(id);
            console.log('[DigestDetail] Digest fetched successfully:', data.id);
            setDigest(data);
        } catch (err) {
            console.error('[DigestDetail] Failed to fetch digest:', err);
            const message = err instanceof Error ? err.message : 'Failed to load digest';
            setError(message);
            toast({
                title: 'Failed to load digest',
                description: message,
                variant: 'destructive',
            });
        } finally {
            setIsLoading(false);
        }
    }, [id, toast]);

    useEffect(() => {
        if (!authLoading && id) {
            fetchDigest();
        }
    }, [authLoading, id, fetchDigest]);

    if (authLoading || isLoading) {
        return (
            <div className="flex min-h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!id) {
        return (
            <div className="container py-8">
                <Card>
                    <CardContent className="py-12 text-center">
                        <h2 className="text-lg font-semibold mb-2">No digest selected</h2>
                        <p className="text-muted-foreground mb-4">
                            Please select a digest from the list.
                        </p>
                        <Link href="/digest">
                            <Button>View All Digests</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (error || !digest) {
        return (
            <div className="container py-8">
                <Card>
                    <CardContent className="py-12 text-center">
                        <h2 className="text-lg font-semibold mb-2">Digest not found</h2>
                        <p className="text-muted-foreground mb-4">
                            {error || "This digest may have been deleted or doesn't exist."}
                        </p>
                        <div className="flex gap-2 justify-center">
                            <Button variant="outline" onClick={fetchDigest} className="gap-2">
                                <RefreshCw className="h-4 w-4" />
                                Retry
                            </Button>
                            <Link href="/digest">
                                <Button>Back to Digests</Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="container py-8 max-w-4xl">
            {/* Navigation */}
            <div className="mb-6">
                <Link href="/digest">
                    <Button variant="ghost" size="sm" className="gap-2">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Digests
                    </Button>
                </Link>
            </div>

            {/* Header - word count and read time only, date is in the markdown content */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-4">Your Daily News Digest</h1>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    {digest.word_count && (
                        <span className="flex items-center gap-1">
                            <FileText className="h-4 w-4" />
                            {digest.word_count} words
                        </span>
                    )}
                    <span className="flex items-center gap-1">
                        <BookOpen className="h-4 w-4" />
                        {Math.ceil((digest.word_count || 500) / 200)} min read
                    </span>
                </div>
            </div>

            {/* Topics Covered */}
            <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                    {digest.interests_included.map((interest) => (
                        <span
                            key={interest}
                            className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                        >
                            {interest}
                        </span>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <Card className="mb-8">
                <CardContent className="pt-6">
                    <article
                        className="prose max-w-none"
                        dangerouslySetInnerHTML={{
                            __html: renderFullContent(digest.content),
                        }}
                    />
                </CardContent>
            </Card>

            {/* How This Affects You Section */}
            <Card className="mb-8 border-primary/20 bg-primary/5">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <span className="text-2xl">💡</span>
                        How This Affects You
                    </CardTitle>
                    <CardDescription>
                        Key takeaways from today&apos;s news based on your interests
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <ul className="space-y-3">
                        {digest.interests_included.map((interest, idx) => (
                            <li key={interest} className="flex items-start gap-3">
                                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                                    {idx + 1}
                                </span>
                                <div>
                                    <span className="font-medium">{interest}:</span>{' '}
                                    <span className="text-muted-foreground">
                                        Stay informed about developments in this area to make
                                        better decisions.
                                    </span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </CardContent>
            </Card>

            {/* Sources */}
            {digest.headlines_used && digest.headlines_used.length > 0 && (
                <div>
                    <h2 className="text-xl font-semibold mb-4">Sources &amp; References</h2>
                    <div className="grid gap-3 md:grid-cols-2">
                        {digest.headlines_used.map((headline, idx) => (
                            <a
                                key={idx}
                                href={headline.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group block p-4 rounded-lg border hover:bg-muted transition-colors"
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors">
                                            {headline.title}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {headline.source} • {headline.category}
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                            {new Date(headline.published_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary transition-colors" />
                                </div>
                            </a>
                        ))}
                    </div>
                </div>
            )}

            {/* Footer Navigation */}
            <div className="mt-12 pt-8 border-t flex justify-between">
                <Link href="/digest">
                    <Button variant="outline" className="gap-2">
                        <ArrowLeft className="h-4 w-4" />
                        All Digests
                    </Button>
                </Link>
                <Link href="/dashboard">
                    <Button className="gap-2">
                        Generate New Digest
                    </Button>
                </Link>
            </div>
        </div>
    );
}

/**
 * Digest Detail Page
 * 
 * Uses query parameter approach for static export compatibility.
 * URL: /digest/view?id=<uuid>
 */
export default function DigestViewPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        }>
            <DigestDetailContent />
        </Suspense>
    );
}
