import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import { Toaster } from '@/components/ui/toaster';
import { Navbar } from '@/components/navbar';
import '@/styles/globals.css';

export const metadata: Metadata = {
    title: 'NewsDigest - Personalized News Summaries',
    description:
        'Get AI-powered personalized news digests based on your interests. Stay informed with curated news summaries delivered daily.',
    keywords: ['news', 'digest', 'AI', 'personalized', 'summary'],
    authors: [{ name: 'NewsDigest Team' }],
    robots: 'index, follow',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-background font-sans antialiased">
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
            </body>
        </html>
    );
}
