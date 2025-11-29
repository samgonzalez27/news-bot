import Link from 'next/link';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Newspaper, Zap, Target, Clock } from 'lucide-react';

export default function HomePage() {
    return (
        <div className="flex flex-col">
            {/* Hero Section */}
            <section className="relative overflow-hidden py-20 sm:py-32">
                <div className="container">
                    <div className="mx-auto max-w-2xl text-center">
                        <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl text-foreground">
                            Your Personal{' '}
                            <span className="text-primary">AI News Curator</span>
                        </h1>
                        <p className="mt-6 text-lg leading-8 text-muted-foreground">
                            Get personalized news digests powered by AI. Select your interests
                            and receive curated daily summaries that matter to you. Stay
                            informed without the noise.
                        </p>
                        <div className="mt-10 flex items-center justify-center gap-x-4">
                            <Link href="/register">
                                <Button size="lg" className="gap-2">
                                    <Zap className="h-4 w-4" />
                                    Start Free
                                </Button>
                            </Link>
                            <Link href="/login">
                                <Button variant="outline" size="lg">
                                    Sign In
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-muted/50">
                <div className="container">
                    <div className="mx-auto max-w-2xl text-center">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                            How It Works
                        </h2>
                        <p className="mt-4 text-muted-foreground">
                            Simple, personalized, and intelligent news delivery.
                        </p>
                    </div>
                    <div className="mx-auto mt-16 max-w-5xl">
                        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                        <Target className="h-6 w-6 text-primary" />
                                    </div>
                                    <CardTitle>Choose Your Interests</CardTitle>
                                    <CardDescription>
                                        Select from categories like Technology, Science, Business,
                                        Sports, and more.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        Our system learns your preferences and curates content that
                                        matches your interests.
                                    </p>
                                </CardContent>
                            </Card>

                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                        <Zap className="h-6 w-6 text-primary" />
                                    </div>
                                    <CardTitle>AI-Powered Summaries</CardTitle>
                                    <CardDescription>
                                        Advanced AI analyzes and summarizes the day's most important
                                        news.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        Get concise, readable digests that highlight key points and
                                        how they affect you.
                                    </p>
                                </CardContent>
                            </Card>

                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                        <Clock className="h-6 w-6 text-primary" />
                                    </div>
                                    <CardTitle>Daily Delivery</CardTitle>
                                    <CardDescription>
                                        Receive your personalized digest at your preferred time each
                                        day.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        Set your preferred delivery time and timezone for a
                                        consistent reading routine.
                                    </p>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20">
                <div className="container">
                    <div className="mx-auto max-w-2xl text-center">
                        <div className="inline-flex items-center justify-center rounded-lg bg-primary/10 p-3 mb-6">
                            <Newspaper className="h-8 w-8 text-primary" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                            Ready to stay informed?
                        </h2>
                        <p className="mt-4 text-muted-foreground">
                            Join thousands of readers who trust NewsDigest for their daily
                            news updates.
                        </p>
                        <div className="mt-8">
                            <Link href="/register">
                                <Button size="lg">Create Your Account</Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
