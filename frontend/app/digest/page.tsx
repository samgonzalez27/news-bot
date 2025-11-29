'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
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
import { getDigests, getLatestDigest } from '@/lib/api';
import type { DigestSummary, DigestDetail } from '@/lib/types';
import { Newspaper, Loader2, Calendar, ExternalLink } from 'lucide-react';

export default function DigestPage() {
    const { isLoading: authLoading } = useRequireAuth();
    const { toast } = useToast();

    const [latestDigest, setLatestDigest] = useState<DigestDetail | null>(null);
    const [allDigests, setAllDigests] = useState<DigestSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(false);

    useEffect(() => {
        const fetchDigests = async () => {
            try {
                const [latest, digestsResponse] = await Promise.all([
                    getLatestDigest(),
                    getDigests(1, 10),
                ]);
                setLatestDigest(latest);
                setAllDigests(digestsResponse.digests);
                setHasMore(digestsResponse.has_next);
            } catch (error) {
                toast({
                    title: 'Failed to load digests',
                    description: 'Please try again later.',
                    variant: 'destructive',
                });
            } finally {
                setIsLoading(false);
            }
        };

        fetchDigests();
    }, [toast]);

    const loadMore = async () => {
        try {
            const response = await getDigests(page + 1, 10);
            setAllDigests((prev) => [...prev, ...response.digests]);
            setHasMore(response.has_next);
            setPage((prev) => prev + 1);
        } catch (error) {
            toast({
                title: 'Failed to load more digests',
                variant: 'destructive',
            });
        }
    };

    if (authLoading || isLoading) {
        return (
            <div className="flex min-h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="container py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold">Your News Digest</h1>
                <p className="text-muted-foreground mt-2">
                    Your personalized AI-curated news summaries
                </p>
            </div>

            {/* Latest Digest Display */}
            {latestDigest ? (
                <div className="mb-12">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <Calendar className="h-5 w-5 text-primary" />
                            Latest Digest -{' '}
                            {new Date(latestDigest.digest_date).toLocaleDateString('en-US', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                            })}
                        </h2>
                        <Link href={`/digest/${latestDigest.id}`}>
                            <Button variant="outline" size="sm">
                                View Full
                            </Button>
                        </Link>
                    </div>

                    <Card>
                        <CardContent className="pt-6">
                            {/* Summary */}
                            {latestDigest.summary && (
                                <div className="mb-6 p-4 bg-muted rounded-lg">
                                    <h3 className="font-semibold mb-2">Summary</h3>
                                    <p className="text-muted-foreground">{latestDigest.summary}</p>
                                </div>
                            )}

                            {/* Content Preview */}
                            <div className="prose max-w-none">
                                <div
                                    className="line-clamp-[20]"
                                    dangerouslySetInnerHTML={{
                                        __html: latestDigest.content
                                            .split('\n')
                                            .slice(0, 30)
                                            .join('\n')
                                            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                                            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                                            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                                            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                                            .replace(/\*(.*)\*/gim, '<em>$1</em>')
                                            .replace(/\n/g, '<br />'),
                                    }}
                                />
                            </div>

                            <div className="mt-6 pt-4 border-t">
                                <Link href={`/digest/${latestDigest.id}`}>
                                    <Button className="gap-2">
                                        Read Full Digest
                                        <ExternalLink className="h-4 w-4" />
                                    </Button>
                                </Link>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Headlines Used */}
                    {latestDigest.headlines_used.length > 0 && (
                        <div className="mt-6">
                            <h3 className="text-lg font-semibold mb-4">Sources Used</h3>
                            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                                {latestDigest.headlines_used.slice(0, 6).map((headline, idx) => (
                                    <a
                                        key={idx}
                                        href={headline.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block p-3 rounded-lg border hover:bg-muted transition-colors"
                                    >
                                        <p className="font-medium text-sm line-clamp-2">
                                            {headline.title}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {headline.source} • {headline.category}
                                        </p>
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <Card className="mb-12">
                    <CardContent className="py-12 text-center">
                        <Newspaper className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No digests yet</h3>
                        <p className="text-muted-foreground mb-4">
                            Generate your first personalized news digest
                        </p>
                        <Link href="/dashboard">
                            <Button>Go to Dashboard</Button>
                        </Link>
                    </CardContent>
                </Card>
            )}

            {/* All Digests List */}
            <div>
                <h2 className="text-xl font-semibold mb-4">Digest History</h2>
                {allDigests.length === 0 ? (
                    <p className="text-muted-foreground">No digest history available</p>
                ) : (
                    <>
                        <div className="space-y-4">
                            {allDigests.map((digest) => (
                                <Link key={digest.id} href={`/digest/${digest.id}`}>
                                    <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                        <CardHeader className="pb-2">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <CardTitle className="text-lg">
                                                        {new Date(digest.digest_date).toLocaleDateString(
                                                            'en-US',
                                                            {
                                                                weekday: 'long',
                                                                year: 'numeric',
                                                                month: 'long',
                                                                day: 'numeric',
                                                            }
                                                        )}
                                                    </CardTitle>
                                                    <CardDescription>
                                                        {digest.word_count
                                                            ? `${digest.word_count} words`
                                                            : 'Processing...'}
                                                        {' • '}
                                                        {digest.status}
                                                    </CardDescription>
                                                </div>
                                                <span
                                                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${digest.status === 'completed'
                                                            ? 'bg-green-100 text-green-800'
                                                            : digest.status === 'pending'
                                                                ? 'bg-yellow-100 text-yellow-800'
                                                                : 'bg-gray-100 text-gray-800'
                                                        }`}
                                                >
                                                    {digest.status}
                                                </span>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            {digest.summary && (
                                                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                                                    {digest.summary}
                                                </p>
                                            )}
                                            <div className="flex flex-wrap gap-1">
                                                {digest.interests_included.map((interest) => (
                                                    <span
                                                        key={interest}
                                                        className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs font-medium"
                                                    >
                                                        {interest}
                                                    </span>
                                                ))}
                                            </div>
                                        </CardContent>
                                    </Card>
                                </Link>
                            ))}
                        </div>
                        {hasMore && (
                            <div className="mt-6 text-center">
                                <Button variant="outline" onClick={loadMore}>
                                    Load More
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
