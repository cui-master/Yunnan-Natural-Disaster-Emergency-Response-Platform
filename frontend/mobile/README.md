# 云南自然灾害应急 · 信息员移动端（H5）

服务于「云南省自然灾害应急响应平台」**普通信息员（ROLE_REPORTER）** 角色的
独立移动端 H5 应用。

- 技术栈：**Next.js 14（App Router） + React 18 + TypeScript + Tailwind CSS 3.4**
- 移动端优先（手机视口），桌面端自动切换为顶部导航
- 主题配色：应急蓝 `#1d4ed8` / 深红 `#dc2626`，背景浅灰

## 目录结构

```
mobile/
├── package.json / tsconfig.json / tailwind.config.ts
├── postcss.config.mjs / next.config.mjs
├── .env.example            # 环境变量样例
├── README.md
└── src/
    ├── app/
    │   ├── layout.tsx       # 根布局（导航 + Toast + Auth）
    │   ├── globals.css      # 全局样式 / 安全区
    │   ├── page.tsx         # 首页（速览 + 我要上报 + 最近灾情）
    │   ├── login/page.tsx   # 登录页
    │   ├── report/page.tsx  # 上报页（表单 + 定位 + 媒体上传）
    │   └── profile/page.tsx # 我的（用户信息 + 登出 + 我的上报）
    ├── components/
    │   ├── AuthProvider.tsx # 登录态 Context
    │   ├── ToastProvider.tsx# 轻提示
    │   ├── RequireAuth.tsx  # 路由守卫
    │   ├── Navigation.tsx   # 底部 Tab（md:hidden）+ 顶部导航 + 移动头
    │   ├── BottomSheet.tsx  # 底部上滑弹层
    │   ├── MediaUploader.tsx# 拍照/录像/相册上传
    │   └── IncidentCard.tsx # 灾情卡片
    └── lib/
        ├── types.ts         # 接口契约类型
        ├── constants.ts     # 灾害类型/等级/状态枚举
        ├── api.ts           # 请求封装
        └── storage.ts       # token / 用户 / 最近上报 本地存储
```

## 快速开始

```bash
cd mobile
cp .env.example .env.local   # 按需修改后端地址
npm install
npm run dev                  # 开发，默认 http://localhost:3000
npm run build && npm run start   # 生产构建并启动
```

> 注意：`next dev` / `next start` 已绑定 `-H 0.0.0.0`，方便手机在同一局域网访问。

## 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE` | 后端 API 基地址（**不含** `/api` 前缀） | `http://localhost:8080` |

所有接口路径内部已拼接 `/api` 前缀，例如最终请求 `http://localhost:8080/api/auth/login`。

## 对接的后端接口（严格对齐契约）

统一响应结构：`{ code: number, message: string, data: T }`，`code === 0` 视为成功；
除登录外，所有请求需带 `Authorization: Bearer <token>` 头。

| 功能 | 方法 / 路径 | 说明 |
| --- | --- | --- |
| 登录 | `POST /api/auth/login` | body `{ username, password }`，返回 `data: { token, username, realName, roleKey, roleName }` |
| 当前用户 | `GET /api/auth/me` | 返回同上结构 |
| 上报灾情 | `POST /api/reports` | body：`title, type, level, content, locationText, lat, lng, images, contact`；其中 `images` 为**逗号分隔的 URL 字符串**（非数组） |
| 文件上传 | `POST /api/upload` | `multipart/form-data`，字段名 `file`，返回 `data: { url }` |
| 灾情列表 | `GET /api/incidents` | 返回 Incident 数组，用于首页/我的页兜底展示 |

### 字段取值
- `type`：`EARTHQUAKE`(地震) / `FLOOD`(洪涝) / `LANDSLIDE`(滑坡) / `DEBRIS_FLOW`(泥石流) / `DROUGHT`(干旱) / `FOREST_FIRE`(森林火灾) / `HAIL`(冰雹) / `TYPHOON`(台风)
- `level`：`I`(特别重大) / `II`(重大) / `III`(较大) / `IV`(一般)
- `status`：`PENDING_VERIFY`(待核验) / `CONFIRMED`(已确认) / `IN_PROGRESS`(处置中) / `CLOSED`(已结束) / `REJECTED`(已驳回)

### 演示账号
- 用户名 `reporter`，密码 `123456`（角色 `ROLE_REPORTER`）

## 页面功能
- **登录**：用户名 + 密码，成功后 token 存 `localStorage`，跳转首页。
- **首页**：信息员速览 + 「我要上报」大按钮 + 最近灾情列表（/api/incidents）。
- **上报**：标题 / 灾害类型（底部弹层选择）/ 等级（底部弹层选择）/ 灾情描述 /
  位置（手动文本 + 「获取定位」调用 `navigator.geolocation`）/ 联系电话 /
  媒体上传区（拍照 `capture`、录像 `capture`、相册选择，逐一上传 /api/upload，
  缩略图预览与删除）。提交后提示成功并清空表单，同时在本地暂存「我的上报」。
- **我的**：展示 `realName` / `roleName`，登出按钮；展示本地暂存的「我的上报」与
  /api/incidents 的近期灾情动态。

## 适配说明
- 手机端底部固定 Tab（`fixed bottom-0`，`md:hidden`），桌面端隐藏并改为顶部导航。
- 使用 `env(safe-area-inset-bottom)` 适配刘海屏底部安全区。
- `<input type="file" accept="image/*" capture="environment">` 调起后置摄像头拍照，
  `accept="video/*" capture="environment"` 调起录像，无 `capture` 则为相册选择。

## 备注
- 后端暂未提供专门的「我的上报」接口，移动端将提交成功的记录暂存于
  `localStorage`（key: `yn_recent_reports`）以支撑「我的上报」展示。
- 构建已开启 TypeScript 严格检查；`next.config.mjs` 中将 `eslint.ignoreDuringBuilds`
  设为 `true`，避免 ESLint 配置缺失阻断生产构建。
