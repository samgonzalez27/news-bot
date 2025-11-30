'use client';

import { AuthProvider } from '@/context/AuthContext';
import { Toaster } from '@/components/ui/toaster';
import { Navbar } from '@/components/navbar';

interface ClientLayoutProps {
    children: React.ReactNode;
}

export function ClientLayout({ children }: ClientLayoutProps) {
    return (
        <AuthProvider>
            <div className="relative flex min-h-screen flex-col">
                <Navbar />
                <main className="flex-1">{children}</main>
                <footer className="border-t py-6 md:py-0">
                    <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
                        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                            © {new Date().getFullYear()} NewsDigest. All rights reserved.
                        </p>
                    </div>
                </footer>
            </div>
            <Toaster />
        </AuthProvider>
    );
}
