import type { Metadata } from 'next';
import { ClientLayout } from '@/components/client-layout';
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
                <ClientLayout>{children}</ClientLayout>
            </body>
        </html>
    );
}
