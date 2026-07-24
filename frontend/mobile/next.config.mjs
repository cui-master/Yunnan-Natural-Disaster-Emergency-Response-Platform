/** @type {import('next').NextConfig} */
const nextConfig = {
  // 移动端 H5 不强依赖 ESLint 阻断构建；类型检查仍开启
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
