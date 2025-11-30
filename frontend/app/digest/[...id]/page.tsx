import DigestDetailClient from './DigestDetailClient';

/**
 * For static export with catch-all dynamic routes, we need generateStaticParams().
 * Since digest IDs are dynamic and user-specific, we return a placeholder entry.
 * This generates a single static page that handles all IDs at runtime via client-side routing.
 * The actual digest fetching happens client-side via useParams() in the client component.
 *
 * The catch-all route [...id] allows us to capture any path segments after /digest/
 * e.g., /digest/123, /digest/abc-def, etc.
 */
export function generateStaticParams() {
    // Return a placeholder to satisfy static export requirements
    // The actual ID resolution happens client-side
    return [{ id: ['placeholder'] }];
}

/**
 * Server component wrapper for the digest detail page.
 * This page uses a client component for all interactive/dynamic content
 * while keeping generateStaticParams() in the server component.
 */
export default function DigestDetailPage() {
    return <DigestDetailClient />;
}
