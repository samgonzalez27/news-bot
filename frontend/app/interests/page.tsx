'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
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

    // Track whether initial sync has occurred to prevent re-sync after save
    const isInitializedRef = useRef(false);
    // Track the last saved state to compute hasChanges accurately
    const savedSlugsRef = useRef<Set<string>>(new Set());

    // Initialize selected interests from user data ONLY on first load
    useEffect(() => {
        if (user && !isInitializedRef.current) {
            const userInterestSlugs = new Set(
                user.interests.map((interest) => interest.slug)
            );
            setSelectedSlugs(userInterestSlugs);
            savedSlugsRef.current = new Set(userInterestSlugs);
            isInitializedRef.current = true;
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

    // Compute hasChanges by comparing current selection with saved state
    // Using Array.from() for TypeScript/Next.js build compatibility (avoids downlevelIteration issues)
    const computeHasChanges = useCallback((current: Set<string>, saved: Set<string>): boolean => {
        if (current.size !== saved.size) return true;
        // Convert Set to Array for iteration - avoids TS build errors with for...of on Sets
        return !Array.from(current).every((slug) => saved.has(slug));
    }, []);

    const toggleInterest = useCallback((slug: string) => {
        setSelectedSlugs((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(slug)) {
                newSet.delete(slug);
            } else {
                newSet.add(slug);
            }
            // Update hasChanges based on comparison with saved state
            setHasChanges(computeHasChanges(newSet, savedSlugsRef.current));
            return newSet;
        });
    }, [computeHasChanges]);

    const handleSave = async () => {
        if (selectedSlugs.size === 0) {
            toast({
                title: 'Select at least one interest',
                description: 'You need to select at least one interest to receive personalized digests.',
                variant: 'destructive',
            });
            return;
        }

        // Capture the current selection before async operations
        const slugsToSave = Array.from(selectedSlugs);
        const slugsSet = new Set(selectedSlugs);

        setIsSaving(true);
        try {
            // Send update to server
            await updateUserInterests({ interest_slugs: slugsToSave });

            // Update saved state reference to match what we just saved
            // This prevents the UI from flickering back
            savedSlugsRef.current = slugsSet;

            // Refresh user context in background (for other components)
            // but DO NOT re-derive local state from it
            await refreshUser();

            // Clear changes flag AFTER successful save
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
            // On error, recompute hasChanges since save failed
            setHasChanges(computeHasChanges(selectedSlugs, savedSlugsRef.current));
        } finally {
            setIsSaving(false);
        }
    };

    const resetChanges = useCallback(() => {
        // Reset to the last saved state (from ref), not from user object
        // This ensures consistency even if user object hasn't updated yet
        setSelectedSlugs(new Set(savedSlugsRef.current));
        setHasChanges(false);
    }, []);

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
