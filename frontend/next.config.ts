/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: '/api/flask/:path*', destination: 'http://127.0.0.1:5000/:path*' },
    ];
  },
};
export default nextConfig;
