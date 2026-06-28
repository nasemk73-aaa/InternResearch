# KUN Visual Novel - 项目指南

## 项目概要

KUN Visual Novel（鲲 Galgame）是一个基于 Nuxt 4 的全栈视觉小说社区论坛。PostgreSQL + Prisma ORM，Redis 缓存，JWT 双 Token 认证，Socket.IO 实时通信，S3 文件存储。

## 构建和运行命令

- **开发**: `pnpm dev` (http://127.0.0.1:1007)
- **构建**: `pnpm build` 或 `pnpm build:limit`（8GB 内存限制）
- **代码检查**: `pnpm lint`，修复: `pnpm lint:fix`
- **格式化**: `pnpm format`
- **类型检查**: `pnpm typecheck`
- **Prisma 生成**: `pnpm prisma:generate`
- **Prisma 推送**: `pnpm prisma:push`
- **PM2 启动/停止**: `pnpm start` / `pnpm stop`

## 代码风格

- 单引号，无分号，行宽 80，缩进 2 空格，无尾逗号
- 箭头函数参数始终加括号: `(x) => x`
- Vue 组件使用 `<script setup lang="ts">`
- 模板中使用 Tailwind CSS 实用类
- 错误消息使用中文

## 命名规范

- **API 文件**: `index.get.ts`, `index.post.ts`（kebab-case + HTTP 方法后缀）
- **组件**: `PascalCase.vue`
- **Composable**: `use` 前缀，如 `useTopic.ts`
- **持久化 Store**: `usePersist*` 前缀
- **临时 Store**: `useTemp*` 前缀
- **数据库字段**: `snake_case`（`user_id`, `vndb_id`）
- **多语言键**: `'en-us'`, `'ja-jp'`, `'zh-cn'`, `'zh-tw'`
- **常量**: `UPPER_SNAKE_CASE`

## 目录结构

- `app/` - 前端（pages, components, composables, store, validations, constants, styles）
- `server/` - 后端（api, utils, plugins, socket, tasks, middleware）
- `shared/` - 共享代码（types, utils, 全局类型声明 *.d.ts）
- `prisma/schema/` - 数据库模型（模块化拆分 .prisma 文件）
- `lib/` - 通用库（S3 客户端, icon 配置, tagMap）

## API 端点编写模式

```typescript
export default defineEventHandler(async (event) => {
  // 1. Zod 验证
  const input = await kunParsePostBody(event, someSchema)
  if (typeof input === 'string') return kunError(event, input)

  // 2. 认证
  const userInfo = await getCookieTokenInfo(event)
  if (!userInfo) return kunError(event, '用户登录失效', 205)

  // 3. 业务逻辑 + 返回数据
  return prisma.someModel.create({ data: { ... } })
})
```

## 错误码约定

- `205` - 认证失效（客户端自动跳转登录页）
- `233` - 通用业务错误（客户端显示错误消息）

## 关键工具函数

- `kunParseGetQuery/kunParsePostBody/kunParsePutBody` - Zod 验证解析
- `kunError(event, message, code?, statusCode?)` - 统一错误响应
- `getCookieTokenInfo(event)` - 获取当前登录用户信息
- `kungalgameResponseHandler` - 客户端统一响应拦截器
- `createEmptyLocaleMap()` - 创建空的四语言映射对象

## 重要约束

- Prisma Schema 分模块放在 `prisma/schema/` 目录，修改后需 `pnpm prisma:generate`
- 新增数据库模型需在 `user.prisma` 中添加反向关联
- 新增持久化 Store 需在 `app/store/index.ts` 的 `kungalgameStoreReset()` 中添加重置逻辑
- 组件和 Composable 自动导入，无需手动 import
- 前端请求 `useFetch` / `$fetch` 需携带 `...kungalgameResponseHandler`

## 详细文档

@docs/proj/architecture.md
@docs/proj/code-style.md
@docs/proj/api-patterns.md
@docs/proj/database.md
@docs/proj/state-management.md
@docs/proj/key-features.md
@docs/proj/development-guide.md
