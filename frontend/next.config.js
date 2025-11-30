/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    // Enable trailing slash for better static hosting compatibility
    trailingSlash: true,
    images: {
        unoptimized: true,
    },
    // TypeScript settings
    typescript: {
        // Set to true if you want to ignore TS errors during production build
        ignoreBuildErrors: false,
    },
    // ESLint settings - ignore during builds to prevent CI failures on warnings
    eslint: {
        ignoreDuringBuilds: true,
    },
    // Disable x-powered-by header for security
    poweredByHeader: false,
    // Generate source maps for debugging (optional, can be false for smaller builds)
    productionBrowserSourceMaps: false,
    // Increase static generation timeout for pages with complex client components
    staticPageGenerationTimeout: 120,
};

module.exports = nextConfig;
