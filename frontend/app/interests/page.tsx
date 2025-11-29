'use client';

import { useEffect, useState } from 'react';
import { useRequireAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { getInterests, updateUserInterests } from '@/lib/api';
import type { Interest } from '@/lib/types';
import { Loader2, Heart, Check, RefreshCw } from 'lucide-react';

export default function InterestsPage() {
    const { user, refreshUser, isLoading: authLoading } = useRequireAuth();
    const { toast } = useToast();

    const [interests, setInterests] = useState<Interest[]>([]);
    const [selectedSlugs, setSelectedSlugs] = useState<Set<string>>(new Set());
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    // Initialize selected interests from user data
    useEffect(() => {
        if (user) {
            const userInterestSlugs = new Set(
                user.interests.map((interest) => interest.slug)
            );
            setSelectedSlugs(userInterestSlugs);
        }
    }, [user]);

    // Fetch all available interests
    useEffect(() => {
        const fetchInterests = async () => {
            try {
                const response = await getInterests();
                setInterests(response.interests);
            } catch (error) {
                toast({
                    title: 'Failed to load interests',
                    description: 'Please try again later.',
                    variant: 'destructive',
                });
            } finally {
                setIsLoading(false);
            }
        };

        fetchInterests();
    }, [toast]);

    const toggleInterest = (slug: string) => {
        setSelectedSlugs((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(slug)) {
                newSet.delete(slug);
            } else {
                newSet.add(slug);
            }
            return newSet;
        });
        setHasChanges(true);
    };

    const handleSave = async () => {
        if (selectedSlugs.size === 0) {
            toast({
                title: 'Select at least one interest',
                description: 'You need to select at least one interest to receive personalized digests.',
                variant: 'destructive',
            });
            return;
        }

        setIsSaving(true);
        try {
            await updateUserInterests({ interest_slugs: Array.from(selectedSlugs) });
            await refreshUser();
            setHasChanges(false);
            toast({
                title: 'Interests updated!',
                description: 'Your news preferences have been saved.',
            });
        } catch (error) {
            const message =
                error instanceof Error ? error.message : 'Failed to update interests';
            toast({
                title: 'Update failed',
                description: message,
                variant: 'destructive',
            });
        } finally {
            setIsSaving(false);
        }
    };

    const resetChanges = () => {
        if (user) {
            const userInterestSlugs = new Set(
                user.interests.map((interest) => interest.slug)
            );
            setSelectedSlugs(userInterestSlugs);
            setHasChanges(false);
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
        <div className="container py-8 max-w-3xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Heart className="h-8 w-8 text-primary" />
                    Your Interests
                </h1>
                <p className="text-muted-foreground mt-2">
                    Select the topics you want to follow. Your digest will be personalized
                    based on these interests.
                </p>
            </div>

            {/* Selected count */}
            <div className="mb-6 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                    <span className="font-semibold text-foreground">
                        {selectedSlugs.size}
                    </span>{' '}
                    of {interests.length} topics selected
                </p>
                {hasChanges && (
                    <Button variant="ghost" size="sm" onClick={resetChanges}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Reset
                    </Button>
                )}
            </div>

            {/* Interests Grid */}
            <div className="grid gap-4 sm:grid-cols-2">
                {interests
                    .filter((interest) => interest.is_active)
                    .sort((a, b) => a.display_order - b.display_order)
                    .map((interest) => {
                        const isSelected = selectedSlugs.has(interest.slug);
                        return (
                            <Card
                                key={interest.id}
                                className={`cursor-pointer transition-all ${isSelected
                                        ? 'border-primary bg-primary/5 shadow-sm'
                                        : 'hover:border-muted-foreground/50'
                                    }`}
                                onClick={() => toggleInterest(interest.slug)}
                            >
                                <CardHeader className="pb-2">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                {interest.name}
                                                {isSelected && (
                                                    <Check className="h-4 w-4 text-primary" />
                                                )}
                                            </CardTitle>
                                            {interest.description && (
                                                <CardDescription className="mt-1">
                                                    {interest.description}
                                                </CardDescription>
                                            )}
                                        </div>
                                        <Switch
                                            checked={isSelected}
                                            onCheckedChange={() => toggleInterest(interest.slug)}
                                            onClick={(e) => e.stopPropagation()}
                                            aria-label={`Toggle ${interest.name}`}
                                        />
                                    </div>
                                </CardHeader>
                            </Card>
                        );
                    })}
            </div>

            {interests.length === 0 && (
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-muted-foreground">
                            No interests available at the moment.
                        </p>
                    </CardContent>
                </Card>
            )}

            {/* Save Button */}
            <div className="mt-8 flex justify-end gap-4 sticky bottom-4">
                {hasChanges && (
                    <Card className="p-4 shadow-lg border-primary/20">
                        <div className="flex items-center gap-4">
                            <p className="text-sm text-muted-foreground">
                                You have unsaved changes
                            </p>
                            <div className="flex gap-2">
                                <Button variant="outline" onClick={resetChanges}>
                                    Cancel
                                </Button>
                                <Button onClick={handleSave} disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        'Save Changes'
                                    )}
                                </Button>
                            </div>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
}
