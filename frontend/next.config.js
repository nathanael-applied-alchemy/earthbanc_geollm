module.exports = {
    async rewrites() {
        console.log("Processing rewrites...");
        return {
            beforeFiles: [
                {
                    source: '/api/:path*',
                    destination: 'http://localhost:8007/api/:path*'
                }
            ],
        }
    },
    httpAgentOptions: {
        keepAlive: true,
    },
    webpack: (config) => {
        // Optional: Disable Webpack caching for debugging purposes
        config.cache = false;
        return config;
    },
    trailingSlash: true,
};