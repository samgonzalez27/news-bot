'use client';

import { useState } from 'react';
import { useRequireAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { updateUserPreferences } from '@/lib/api';
import { Loader2, Settings, Clock, Globe, Save } from 'lucide-react';

// Common timezones
const TIMEZONES = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Asia/Singapore',
    'Australia/Sydney',
];

export default function SettingsPage() {
    const { user, refreshUser, isLoading: authLoading } = useRequireAuth();
    const { toast } = useToast();

    const [preferredTime, setPreferredTime] = useState(
        user?.preferred_time || '08:00'
    );
    const [timezone, setTimezone] = useState(user?.timezone || 'UTC');
    const [isSaving, setIsSaving] = useState(false);

    // Update state when user loads
    if (user && preferredTime !== user.preferred_time && !isSaving) {
        setPreferredTime(user.preferred_time);
    }
    if (user && timezone !== user.timezone && !isSaving) {
        setTimezone(user.timezone);
    }

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await updateUserPreferences({
                preferred_time: preferredTime,
                timezone: timezone,
            });
            await refreshUser();
            toast({
                title: 'Settings saved!',
                description: 'Your preferences have been updated.',
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
                <CardContent className="space-y-6">
                    <div className="grid gap-2">
                        <Label htmlFor="preferred_time">Preferred Delivery Time</Label>
                        <Input
                            id="preferred_time"
                            type="time"
                            value={preferredTime}
                            onChange={(e) => setPreferredTime(e.target.value)}
                            className="max-w-[200px]"
                        />
                        <p className="text-sm text-muted-foreground">
                            Your digest will be generated around this time daily
                        </p>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="timezone" className="flex items-center gap-2">
                            <Globe className="h-4 w-4" />
                            Timezone
                        </Label>
                        <select
                            id="timezone"
                            value={timezone}
                            onChange={(e) => setTimezone(e.target.value)}
                            className="flex h-10 w-full max-w-[300px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        >
                            {TIMEZONES.map((tz) => (
                                <option key={tz} value={tz}>
                                    {tz.replace(/_/g, ' ')}
                                </option>
                            ))}
                        </select>
                        <p className="text-sm text-muted-foreground">
                            Used to schedule your digest delivery
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
            <div className="flex justify-end">
                <Button onClick={handleSave} disabled={isSaving} className="gap-2">
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
    );
}
