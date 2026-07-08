# PanEval Frontend

`pan-eval-front` is the Vue 3 frontend for PanEval. It provides the public home page, authenticated console shell, evaluation management pages, custom image management pages, and shared authentication/session plumbing for the PanEval web experience.

## Tech Stack

- Vue 3 with `<script setup lang="ts">`
- Vite 6
- TypeScript strict mode
- Vue Router with HTML5 history mode
- Pinia for app-level client state
- TanStack Query for server-state workflows
- Axios for API requests
- Element Plus for UI primitives
- Tailwind CSS v4 plus project CSS tokens
- Vue I18n
- Vitest and Vue Test Utils

## Prerequisites

Use the project runtime versions:

```bash
source /Users/rentongshuai/.nvm/nvm.sh && nvm use 22
corepack enable
```

The repository declares:

- Node `22.16.0` in `.nvmrc`
- pnpm `9.12.0` in `package.json`

Install dependencies:

```bash
corepack pnpm install
```

## Local Development

Start Vite:

```bash
corepack pnpm run dev
```

The dev server is configured for port `4000`. If that port is occupied, Vite will choose the next available port.

Authentication-sensitive pages rely on the shared backend cookie session. For local work, sign in through the shared backend flow first, then this app validates the session with `/users/me`.

## Scripts

```bash
corepack pnpm run dev          # Vite dev server, mode base
corepack pnpm run lint         # ESLint
corepack pnpm run typecheck    # vue-tsc plus node tsconfig check
corepack pnpm run test         # Vitest
corepack pnpm run build        # Production build, mode pro
corepack pnpm run build:dev    # Development build, mode dev
corepack pnpm run preview      # Preview production build
corepack pnpm run format       # Prettier write
```

## Environment

Environment files are checked in for the current deployment modes:

- `.env.base`: local/base development mode
- `.env.dev`: development build mode
- `.env.pro`: production build mode

Important Vite variables:

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Axios base URL, usually `/api` behind the Vite proxy |
| `VITE_UPLOAD_BASE_URL` | Upload/static upload prefix |
| `VITE_STATIC_BASE_URL` | Static asset base URL |
| `VITE_PRIVACY_URL` | Privacy link target |
| `VITE_ENABLE_ANALYTICS` | Enables analytics-related behavior when implemented |
| `VITE_DEPLOY_REGION` | Deployment region marker |
| `VITE_BASE_PATH` | Vite base path |
| `VITE_OUT_DIR` | Build output directory |
| `VITE_DROP_CONSOLE` | Drop console calls during build when `true` |
| `VITE_DROP_DEBUGGER` | Drop debugger statements during build when `true` |
| `VITE_SOURCEMAP` | Emit inline sourcemaps when `true` |

Development proxy defaults are defined in `vite.config.ts`:

```text
/api -> https://paneval.eclipse.org
/ws  -> wss://paneval.eclipse.org
```

Override them with:

```bash
DEV_API_PROXY_TARGET=http://host:port
DEV_WS_PROXY_TARGET=ws://host:port
```

## Project Structure

```text
src/
  api/                 Axios client and domain API modules
    auth/              Login, logout, and /users/me session validation
    evaluations/       Evaluation, batch, dataset, resource, and result APIs
    images/            Custom image list/create/audit/delete APIs
  app/                 App-level provider installation
  assets/              Static images, icons, and home page media
  components/          Shared UI components such as navigation and login dialog
  i18n/                Vue I18n setup and locale typing
  layouts/             Public and console layout shells
  locales/             Translation JSON files
  pages/               Route-level pages
    account/           Account/profile pages
    console/           Authenticated console features
    home/              Public home page
  router/              Router setup, route records, and route tests
  stores/              Pinia stores
  styles/              Global CSS and design tokens
  types/               Shared ambient typings
```

## Routing

The app uses HTML5 history mode. Deployment must serve `index.html` as the SPA fallback.

Current route groups:

- `/`: public home page in `PublicLayout`
- `/mine`: authenticated account page
- `/console`: authenticated console layout
- `/console/evaluations`: evaluation list
- `/console/evaluations/create`: create evaluation
- `/console/evaluations/:id/edit`: edit evaluation
- `/console/evaluations/:id`: evaluation detail
- `/console/images`: image list
- `/console/images/create`: create image

Routes with `meta.requiresAuth` call `refreshCurrentUser()`, which validates the current cookie-backed session through `/users/me`. If validation fails, the app opens the global login dialog and returns to the home route.

## API And State

- `src/api/client.ts` owns the shared Axios instance.
- Requests include credentials and attach `X-CSRFToken` from the `csrftoken` cookie when present.
- API functions live under `src/api/<domain>/`.
- Pinia stores hold app-level client state such as auth and login dialog state.
- TanStack Query is available for server-state fetching, caching, invalidation, and loading/error state.

## Development Guidelines

- Keep API calls in domain modules under `src/api/`.
- Keep shared auth/session calls in `src/api/auth`.
- Prefer Element Plus and existing local components before creating custom controls.
- Keep page-local state inside components or composables unless it truly needs app-level sharing.
- Do not add standalone email/password-only auth flows or staff/admin-only branching unless the product scope explicitly changes.
- Keep migration scope explicit: do not add unrelated legacy workflows unless that is the requested task.

## Verification

Recommended checks before handing off changes:

```bash
corepack pnpm run lint
corepack pnpm run typecheck
corepack pnpm run test
```

For routing, auth, proxy, environment, build, or deployment changes, also run:

```bash
corepack pnpm run build
```

For UI changes, start the dev server and verify the affected flow in a browser at desktop and mobile widths.
