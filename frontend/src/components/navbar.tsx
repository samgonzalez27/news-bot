'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import {
    Newspaper,
    LayoutDashboard,
    Settings,
    Heart,
    LogOut,
    Menu,
    X,
} from 'lucide-react';
import { useState } from 'react';

export function Navbar() {
    const { isAuthenticated, isLoading, logout, user } = useAuth();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const navLinks = [
        { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { href: '/digest', label: 'Digest', icon: Newspaper },
        { href: '/interests', label: 'Interests', icon: Heart },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 items-center justify-between">
                <div className="flex items-center gap-6">
                    <Link href="/" className="flex items-center space-x-2">
                        <Newspaper className="h-6 w-6 text-primary" />
                        <span className="font-bold text-xl">NewsDigest</span>
                    </Link>

                    {/* Desktop Navigation */}
                    {isAuthenticated && (
                        <nav className="hidden md:flex items-center space-x-4">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    <link.icon className="h-4 w-4" />
                                    {link.label}
                                </Link>
                            ))}
                        </nav>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    {isLoading ? (
                        <div className="h-8 w-24 animate-pulse rounded bg-muted" />
                    ) : isAuthenticated ? (
                        <>
                            <span className="hidden sm:inline text-sm text-muted-foreground">
                                {user?.full_name || user?.email}
                            </span>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={logout}
                                className="hidden md:flex items-center gap-2"
                            >
                                <LogOut className="h-4 w-4" />
                                Logout
                            </Button>

                            {/* Mobile menu button */}
                            <Button
                                variant="ghost"
                                size="icon"
                                className="md:hidden"
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                aria-label="Toggle menu"
                            >
                                {mobileMenuOpen ? (
                                    <X className="h-5 w-5" />
                                ) : (
                                    <Menu className="h-5 w-5" />
                                )}
                            </Button>
                        </>
                    ) : (
                        <div className="flex items-center gap-2">
                            <Link href="/login">
                                <Button variant="ghost" size="sm">
                                    Login
                                </Button>
                            </Link>
                            <Link href="/register">
                                <Button size="sm">Get Started</Button>
                            </Link>
                        </div>
                    )}
                </div>
            </div>

            {/* Mobile Navigation */}
            {isAuthenticated && mobileMenuOpen && (
                <div className="md:hidden border-t">
                    <nav className="container py-4 flex flex-col space-y-2">
                        {navLinks.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                onClick={() => setMobileMenuOpen(false)}
                                className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-md transition-colors"
                            >
                                <link.icon className="h-4 w-4" />
                                {link.label}
                            </Link>
                        ))}
                        <button
                            onClick={() => {
                                setMobileMenuOpen(false);
                                logout();
                            }}
                            className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                        >
                            <LogOut className="h-4 w-4" />
                            Logout
                        </button>
                    </nav>
                </div>
            )}
        </header>
    );
}
