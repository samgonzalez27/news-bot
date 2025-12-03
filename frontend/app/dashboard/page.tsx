'use client';

import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
import { generateDigest, getDigests } from '@/lib/api';
import type { DigestSummary } from '@/lib/types';
import {
    Newspaper,
    Loader2,
    Zap,
    Calendar,
    Heart,
    ArrowRight,
    Eye,
} from 'lucide-react';

// Minimum loading time to prevent flash (in milliseconds)
const MIN_LOADING_TIME = 300;

export default function DashboardPage() {
    const { user, isLoading: authLoading } = useRequireAuth();
    const router = useRouter();
    const { toast } = useToast();

    const [recentDigests, setRecentDigests] = useState<DigestSummary[]>([]);
    const [isLoadingDigests, setIsLoadingDigests] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [lastFetchedUserId, setLastFetchedUserId] = useState<string | null>(null);
    const [fetchError, setFetchError] = useState(false);

    // Track if we've done the initial fetch for this user
    const hasFetchedRef = useRef(false);

    // Compute yesterday's date in UTC (the current digest_date)
    const currentDigestDate = useMemo(() => {
        const now = new Date();
        const yesterday = new Date(Date.UTC(
            now.getUTCFullYear(),
            now.getUTCMonth(),
            now.getUTCDate() - 1
        ));
        return yesterday.toISOString().split('T')[0]; // YYYY-MM-DD format
    }, []);

    // Check if a digest exists for the current digest_date
    const todaysDigest = useMemo(() => {
        // Only return a digest if we've finished loading for the current user
        if (isLoadingDigests) {
            return undefined;
        }
        // If we had a fetch error, don't show "Generate Now" - keep undefined
        if (fetchError) {
            return undefined;
        }
        return recentDigests.find(d => d.digest_date === currentDigestDate);
    }, [recentDigests, currentDigestDate, isLoadingDigests, fetchError]);

    // Stable fetch function
    const fetchDigests = useCallback(async (userId: string, forceRefresh = false) => {
        // Skip if we already have data for this user and not forcing refresh
        if (!forceRefresh && lastFetchedUserId === userId && recentDigests.length > 0) {
            setIsLoadingDigests(false);
            return;
        }

        setIsLoadingDigests(true);
        setFetchError(false);
        const startTime = Date.now();

        try {
            const response = await getDigests(1, 5);

            // Ensure minimum loading time to prevent flash
            const elapsed = Date.now() - startTime;
            if (elapsed < MIN_LOADING_TIME) {
                await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
            }

            setRecentDigests(response.digests);
            setLastFetchedUserId(userId);
            setFetchError(false);
        } catch (error) {
            console.error('Failed to fetch digests:', error);
            setFetchError(true);
            // Don't clear existing digests on error - keep showing old data
        } finally {
            setIsLoadingDigests(false);
        }
    }, [lastFetchedUserId, recentDigests.length]);

    // Single effect to handle fetching digests
    useEffect(() => {
        // Skip if no user or still loading auth
        if (!user) {
            setIsLoadingDigests(false);
            return;
        }

        const userId = user.id;

        // If user changed, reset the fetch flag
        if (lastFetchedUserId !== userId) {
            hasFetchedRef.current = false;
        }

        // Only fetch if we haven't fetched for this user yet
        if (!hasFetchedRef.current) {
            hasFetchedRef.current = true;
            fetchDigests(userId);
        } else {
            // We already have data, don't show loading
            setIsLoadingDigests(false);
        }
    }, [user?.id, lastFetchedUserId, fetchDigests]);

    const handleGenerateDigest = async () => {
        setIsGenerating(true);
        try {
            const digest = await generateDigest();
            toast({
                title: 'Digest generated!',
                description: 'Your personalized news digest is ready.',
            });
            router.push(`/digest/${digest.id}`);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to generate digest';
            toast({
                title: 'Generation failed',
                description: message,
                variant: 'destructive',
            });
        } finally {
            setIsGenerating(false);
        }
    };

    if (authLoading) {
        return (
            <div className="flex min-h-[80vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!user) {
        return null;
    }

    const hasInterests = user.interests && user.interests.length > 0;

    return (
        <div className="container py-8">
            {/* Welcome Section */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold">
                    Welcome back, {user.full_name.split(' ')[0]}!
                </h1>
                <p className="text-muted-foreground mt-2">
                    Here's your news digest dashboard
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Generate Digest Card */}
                <Card className="col-span-full lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-primary" />
                            {isLoadingDigests
                                ? 'Daily Digest'
                                : fetchError
                                    ? 'Daily Digest'
                                    : todaysDigest
                                        ? "Today's Digest"
                                        : 'Generate Digest'}
                        </CardTitle>
                        <CardDescription>
                            {isLoadingDigests
                                ? 'Checking your digest status...'
                                : fetchError
                                    ? 'Unable to check digest status. Please refresh.'
                                    : todaysDigest
                                        ? "Your digest for today is ready to read"
                                        : 'Create a personalized news digest based on your interests'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {!hasInterests ? (
                            <div className="text-center py-4">
                                <p className="text-sm text-muted-foreground mb-4">
                                    Set up your interests first to generate digests
                                </p>
                                <Link href="/interests">
                                    <Button variant="outline" className="gap-2">
                                        <Heart className="h-4 w-4" />
                                        Select Interests
                                    </Button>
                                </Link>
                            </div>
                        ) : isLoadingDigests ? (
                            <Button
                                disabled
                                className="w-full gap-2"
                            >
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading...
                            </Button>
                        ) : fetchError ? (
                            <Button
                                onClick={() => user && fetchDigests(user.id, true)}
                                variant="outline"
                                className="w-full gap-2"
                            >
                                <ArrowRight className="h-4 w-4" />
                                Retry
                            </Button>
                        ) : todaysDigest ? (
                            <Link href={`/digest/${todaysDigest.id}`}>
                                <Button
                                    variant="secondary"
                                    className="w-full gap-2"
                                >
                                    <Eye className="h-4 w-4" />
                                    View Today's Digest
                                </Button>
                            </Link>
                        ) : (
                            <Button
                                onClick={handleGenerateDigest}
                                disabled={isGenerating}
                                className="w-full gap-2"
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <Newspaper className="h-4 w-4" />
                                        Generate Now
                                    </>
                                )}
                            </Button>
                        )}
                    </CardContent>
                </Card>

                {/* User Interests Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Heart className="h-5 w-5 text-primary" />
                            Your Interests
                        </CardTitle>
                        <CardDescription>
                            {hasInterests
                                ? `${user.interests.length} topics selected`
                                : 'No interests selected'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {hasInterests ? (
                            <div className="flex flex-wrap gap-2">
                                {user.interests.map((interest) => (
                                    <span
                                        key={interest.id}
                                        className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                                    >
                                        {interest.name}
                                    </span>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                Select your interests to personalize your news digest
                            </p>
                        )}
                        <Link href="/interests" className="block mt-4">
                            <Button variant="outline" size="sm" className="gap-2">
                                Manage Interests
                                <ArrowRight className="h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>

                {/* Delivery Settings Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="h-5 w-5 text-primary" />
                            Delivery Settings
                        </CardTitle>
                        <CardDescription>Your digest delivery preferences</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Preferred Time</span>
                                <span className="font-medium">
                                    {user.preferred_time} UTC
                                </span>
                            </div>
                        </div>
                        <Link href="/settings" className="block mt-4">
                            <Button variant="outline" size="sm" className="gap-2">
                                Update Settings
                                <ArrowRight className="h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Digests */}
            <div className="mt-8">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold">Recent Digests</h2>
                    <Link href="/digest">
                        <Button variant="ghost" size="sm" className="gap-2">
                            View All
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </Link>
                </div>

                {isLoadingDigests ? (
                    <div className="flex justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                ) : recentDigests.length === 0 ? (
                    <Card>
                        <CardContent className="py-8 text-center">
                            <Newspaper className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">
                                No digests yet. Generate your first one!
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {recentDigests.map((digest) => (
                            <Link key={digest.id} href={`/digest/${digest.id}`}>
                                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg">
                                            {new Date(digest.digest_date + 'T00:00:00').toLocaleDateString(
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
                                                : 'No content'}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {digest.summary ? (
                                            <p className="text-sm text-muted-foreground line-clamp-2">
                                                {digest.summary}
                                            </p>
                                        ) : (
                                            <p className="text-sm text-muted-foreground italic">
                                                No summary available
                                            </p>
                                        )}
                                        <div className="flex flex-wrap gap-1 mt-3">
                                            {digest.interests_included.slice(0, 3).map((interest) => (
                                                <span
                                                    key={interest}
                                                    className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs font-medium"
                                                >
                                                    {interest}
                                                </span>
                                            ))}
                                            {digest.interests_included.length > 3 && (
                                                <span className="text-xs text-muted-foreground">
                                                    +{digest.interests_included.length - 3} more
                                                </span>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
