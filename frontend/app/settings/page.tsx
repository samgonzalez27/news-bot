'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRequireAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { updateUserPreferences } from '@/lib/api';
import {
    generateTimeOptions,
    formatTimeFor12Hour,
    roundToNearest15Minutes,
} from '@/lib/timezone';
import { Loader2, Settings, Clock, Save } from 'lucide-react';

// Pre-generate time options (memoized outside component)
const TIME_OPTIONS = generateTimeOptions();

export default function SettingsPage() {
    const { user, refreshUser, isLoading: authLoading } = useRequireAuth();
    const { toast } = useToast();

    // Local state for preferred time (stored and displayed in UTC)
    const [preferredTime, setPreferredTime] = useState<string>('08:00');
    const [isSaving, setIsSaving] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);

    // Initialize form state from user data
    useEffect(() => {
        if (user && !isInitialized) {
            if (user.preferred_time) {
                // Round to nearest 15 minutes to match our dropdown options
                setPreferredTime(roundToNearest15Minutes(user.preferred_time));
            }
            setIsInitialized(true);
        }
    }, [user, isInitialized]);

    // Reset initialization flag if user changes (e.g., logout/login)
    useEffect(() => {
        if (!user) {
            setIsInitialized(false);
        }
    }, [user]);

    // Handle time change
    const handleTimeChange = useCallback((newTime: string) => {
        setPreferredTime(newTime);
    }, []);

    // Handle save
    const handleSave = async () => {
        setIsSaving(true);

        try {
            await updateUserPreferences({
                preferred_time: preferredTime,
                // NOTE: timezone field removed - all users use UTC
            });

            await refreshUser();

            toast({
                title: 'Settings saved!',
                description: `Your digest will be delivered at ${formatTimeFor12Hour(preferredTime)} UTC.`,
            });
        } catch (error) {
            const message =
                error instanceof Error ? error.message : 'Failed to save settings';
            toast({
                title: 'Save failed',
                description: message,
                variant: 'destructive',
            });
        } finally {
            setIsSaving(false);
        }
    };

    // Check if there are unsaved changes
    const hasChanges = useCallback(() => {
        if (!user) return false;
        const storedTime = user.preferred_time || '08:00';
        return preferredTime !== roundToNearest15Minutes(storedTime);
    }, [user, preferredTime]);

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

    return (
        <div className="container py-8 max-w-2xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Settings className="h-8 w-8 text-primary" />
                    Settings
                </h1>
                <p className="text-muted-foreground mt-2">
                    Manage your account preferences and digest delivery settings
                </p>
            </div>

            {/* Account Information */}
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>Account Information</CardTitle>
                    <CardDescription>Your account details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <Label className="text-muted-foreground">Name</Label>
                        <p className="font-medium">{user.full_name}</p>
                    </div>
                    <div className="grid gap-2">
                        <Label className="text-muted-foreground">Email</Label>
                        <p className="font-medium">{user.email}</p>
                    </div>
                    <div className="grid gap-2">
                        <Label className="text-muted-foreground">Member since</Label>
                        <p className="font-medium">
                            {new Date(user.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                            })}
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Digest Delivery Settings */}
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Digest Delivery
                    </CardTitle>
                    <CardDescription>
                        Configure when you receive your daily news digest
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Time Selection */}
                    <div className="grid gap-2">
                        <Label htmlFor="preferred_time">Preferred Delivery Time (UTC)</Label>
                        <Select value={preferredTime} onValueChange={handleTimeChange}>
                            <SelectTrigger className="w-full max-w-[180px]" id="preferred_time">
                                <SelectValue>
                                    {formatTimeFor12Hour(preferredTime)}
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent className="max-h-[200px]">
                                {TIME_OPTIONS.map((option) => (
                                    <SelectItem key={option.value} value={option.value}>
                                        {option.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-sm text-muted-foreground">
                            Your digest will be generated around this time daily (UTC timezone)
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Interests Summary */}
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>Your Interests</CardTitle>
                    <CardDescription>
                        {user.interests.length} topics selected
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {user.interests.length > 0 ? (
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
                        <p className="text-muted-foreground">No interests selected</p>
                    )}
                    <Button
                        variant="outline"
                        size="sm"
                        className="mt-4"
                        onClick={() => (window.location.href = '/interests')}
                    >
                        Manage Interests
                    </Button>
                </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex items-center justify-between">
                {hasChanges() && (
                    <p className="text-sm text-muted-foreground">
                        You have unsaved changes
                    </p>
                )}
                <div className="flex justify-end flex-1">
                    <Button
                        onClick={handleSave}
                        disabled={isSaving || !hasChanges()}
                        className="gap-2"
                    >
                        {isSaving ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Save className="h-4 w-4" />
                                Save Changes
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
