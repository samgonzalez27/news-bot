'use client';

import { useEffect, useState } from 'react';
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
} from 'lucide-react';

export default function DashboardPage() {
    const { user, isLoading: authLoading } = useRequireAuth();
    const router = useRouter();
    const { toast } = useToast();

    const [recentDigests, setRecentDigests] = useState<DigestSummary[]>([]);
    const [isLoadingDigests, setIsLoadingDigests] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);

    useEffect(() => {
        const fetchDigests = async () => {
            try {
                const response = await getDigests(1, 5);
                setRecentDigests(response.digests);
            } catch (error) {
                console.error('Failed to fetch digests:', error);
            } finally {
                setIsLoadingDigests(false);
            }
        };

        if (user) {
            fetchDigests();
        }
    }, [user]);

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
            const message =
                error instanceof Error ? error.message : 'Failed to generate digest';
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
                            Generate Digest
                        </CardTitle>
                        <CardDescription>
                            Create a personalized news digest based on your interests
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
                                <span className="font-medium">{user.preferred_time}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Timezone</span>
                                <span className="font-medium">{user.timezone}</span>
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
