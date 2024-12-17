module.exports = {
    async rewrites() {
        console.log("Processing rewrites...");
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:8007/api/:path*', // Adjust port if needed
            },
        ];
    },
    webpack: (config) => {
        // Optional: Disable Webpack caching for debugging purposes
        config.cache = false;
        return config;
    },
    trailingSlash: true,
};