# Coding Style & Conventions Reference

This document captures the coding style, patterns, and conventions used throughout this Nuxt.js / Nitro / Pinia project (a pharmaceutical ERP system).

---

## 1. Vue Component API Style

**Universal pattern: `<script setup lang="ts">`** (Composition API with `<script setup>`)

Both attribute orderings are interchangeable:
```vue
<script setup lang="ts">  <!-- most common -->
<script lang="ts" setup>  <!-- also used (layouts, sidebar, etc.) -->
```

No Options API components exist. No `.js` component files — TypeScript only.

---

## 2. Block Ordering

**Script → Template → Style** is the standard:
```vue
<script setup lang="ts">
// ...
</script>

<template>
  <!-- ... -->
</template>

<style scoped></style>
```

Style blocks are almost always **empty** (`<style scoped></style>`) or omitted entirely. When styling is present:
- `<style scoped>` — default
- `<style lang="css" scoped>` — logo.vue (exception)
- `<style lang="scss" scoped>` — emp_create.vue (exception)

---

## 3. TypeScript Usage

### Schema-Derived Types (primary pattern)
All domain types come from Zod schemas in `app/schema/`:
```ts
type Schema = z.output<typeof payroll>
// or
type StaffSchema = z.infer<typeof staff>
```

### `import type` for Type-Only Imports (consistent)
```ts
import type { NavigationMenuItem } from '@nuxt/ui'
import type { FormSubmitEvent, FormError } from '#ui/types'
import type { UseFetchOptions } from 'nuxt/app'
```

### Interfaces Defined Inline (complex components)
```ts
interface FormFieldConfig {
  type: 'input' | 'textarea' | 'select' | 'switch' | 'number' | 'array' | 'file' | 'custom'
  label?: string
  placeholder?: string
}
interface Props { schema: ZodObject<any>; modelValue: T }
interface Emits {
  (e: 'update:modelValue', value: T): void
  (e: 'submit', event: FormSubmitEvent<T>): void
}
```

### Generic Components (rare, used in DynamicForm)
```ts
<script lang="ts" setup generic="T extends Record<string, any>">
```

### Type Casting for Prop Types
```ts
type: String as () => 'Create' | 'Update'
```

---

## 4. Import Patterns

### Auto-Imports (never imported explicitly)
All Nuxt/Vue primitives are auto-imported — never add explicit imports for:
```
ref, reactive, computed, watch, watchEffect, onMounted, onBeforeMount,
onUnmounted, useRoute, useRouter, navigateTo, useFetch, definePageMeta,
useSeoMeta, useToast, useCookie, useNuxtApp, useState, defineShortcuts,
useWindowSize, useOverlay, useTemplateRef
```

### Component Lazy Loading (from `#components`)
```ts
import { Alerts, LazyFormsHrmEmpManagement, LazyPageHrmStaffprofile } from '#components'
```

### Third-Party Named Imports
```ts
import { z } from 'zod'
import { createSharedComposable, useDebounceFn, useMediaQuery, createReusableTemplate } from '@vueuse/core'
import { upperFirst } from 'scule'
import { $fetch } from 'ofetch'         // server-side
import { H3Event } from 'h3'            // server-side
```

### Schema Path Alias
```ts
import { payroll, payrolldetails } from '~/schema/hrm'
import { itemcreate, barcodes } from '~/schema/inv'
import { staff } from '~/schema/user'
```

### `~~/` for Workspace Root Imports (server code)
```ts
import { mainserverlinks } from '~~/server/utils/all'
```

---

## 5. Naming Conventions

| Entity | Convention | Examples |
|--------|-----------|---------|
| Vue components | PascalCase filename | `AppSidebar.vue`, `DynamicForm.vue` |
| Component usage in templates | PascalCase preferred | `<Branchswitch />`, `<UButton />` |
| Pages / layouts | kebab-case | `sign-in.vue`, `default.vue` |
| Composable files | camelCase | `useSidebarState.ts`, `dashing.ts` |
| Composable functions | `use` prefix + camelCase | `useDashboard`, `useScanRead` |
| Store files | `use` prefix + PascalCase | `useAuthStore.ts` |
| Zod schema objects | camelCase (lowercase first) | `payroll`, `employeemanagement` |
| TypeScript interfaces/types | PascalCase | `Schema`, `FormFieldConfig`, `SidebarState` |
| Variables / refs | camelCase | `currentBranch`, `branchlist`, `openmodal` |
| Functions | camelCase | `branchChange`, `onSubmit`, `flattenErrors` |
| Icons | Iconify string format | `i-heroicons-chart-bar`, `i-lucide-bell` |
| Server API route files | Method suffix | `sign-in.post.ts`, `preferences.get.ts` |
| Wildcard route files | `[...].ts` | `server/api/serv/[...].ts` |
| Props variable | Always `props` | `const props = defineProps(...)` |
| Emits variable | Always `emit` | `const emit = defineEmits(...)` |

---

## 6. Props Patterns

### Object Syntax (with defaults / type casting)
```ts
const props = defineProps({
  collapsed: { type: Boolean, default: false },
  block: { type: Boolean, default: true },
  edit_id: { type: String, required: false },
  formtypeval: { type: String as () => 'Create' | 'Update', required: true }
})
```

### TypeScript Generic Syntax (simple / no defaults needed)
```ts
const props = defineProps<{ collapsed?: boolean }>()
```

### `withDefaults` Syntax (interface-based props)
```ts
const props = withDefaults(defineProps<Props>(), {
  fieldConfig: () => ({}),
  submitLabel: 'Submit',
  showActions: true,
  loading: false,
  disabled: false
})
```

---

## 7. Emits Patterns

Always TypeScript generic syntax with named tuple types:
```ts
// Single emit:
const emit = defineEmits<{ close: [boolean] }>()

// Multiple emits:
const emit = defineEmits<{
  close: [boolean],
  result: [value: string]
}>()

// Interface-based (complex component):
const emit = defineEmits<Emits>()
```

Called directly: `emit('close', true)`, `emit('result', res.id)`

---

## 8. State Management Patterns

### Local Reactive State
Always `ref<Schema>({...})` with explicit type:
```ts
const state = ref<Schema>({
  date: `${new Date().getFullYear()}-...`,
  payroll_details: [],
  status: 'pending'
})
```

### `computed()` for Derived Values
```ts
const navigations = computed<NavigationMenuItem[][]>(() => {
  return geturls(`/${route.path.split('/')[1]}` || '')
})

const maxDays = computed(() => {
  const date = new Date(state.value.date)
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
})
```

### `watchEffect()` for Reactive Side Effects
```ts
watchEffect(() => {
  if (current_branch.value) {
    openmodal.value = false
    currentBranch.value = branchlist.value.find(b => b.value === current_branch.value)
  } else {
    openmodal.value = true
  }
})
```

### `watch()` for Specific Dependencies
```ts
watch(() => route.fullPath, () => {
  isNotificationsSlideoverOpen.value = false
})
```

### `shallowRef()` for Performance on Large Objects
```ts
const barcoded = shallowRef()
```

### `useState()` for Shared Cross-Component State (Nuxt)
```ts
const branchSwitch = useState('branchSwitch', () => ({ branch: 'main' }))
```

### Pinia Stores (Composition API style)
```ts
export const useAuthStore = defineStore('auths', () => {
  const onlinestate = computed<boolean>(() => true)

  async function passwordresetrequest(email: string) { ... }
  function $reset() {}

  return { staff, onlinestate, passwordresetrequest, passwordreset }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}
```

### `useCookie()` for Cookie-Based Persistent State
```ts
const current_branch = useCookie('branch')
```

---

## 9. Composable Patterns

**Named exports only** — no default exports in composables:
```ts
export const useDashboard = createSharedComposable(_useDashboard)
export function flattenErrors(errors: Record<string, any>): FormError[] { ... }
export async function submit(...) { ... }
```

**`createSharedComposable`** for singleton shared state:
```ts
const _useDashboard = () => {
  const isNotificationsSlideoverOpen = ref(false)
  defineShortcuts({ 'g-h': () => router.push('/') })
  watch(() => route.fullPath, () => { isNotificationsSlideoverOpen.value = false })
  return { isNotificationsSlideoverOpen }
}
export const useDashboard = createSharedComposable(_useDashboard)
```

**Generic typed composables**:
```ts
export const useDebounceUniqueFunction = <T extends object>(
  url: string,
  uniqueFields: (keyof T)[],
  debounceTime: number = 500
) => {
  return useDebounceFn(async (data: T) => { ... }, debounceTime)
}
```

**Lifecycle hooks inside composables** are acceptable:
```ts
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
```

---

## 10. API Call Patterns

### `useFetch()` — Reactive/SSR-friendly (inside `<script setup>`)
```ts
const { data, refresh } = useFetch(`${url}/get_unpaid_staff`, {
  method: 'GET',
  query: { date: props.date }
})
const { data: profile } = useFetch(`/api/users/profile/${userId}`, { method: 'GET' })
```

### `$fetch()` — Imperative (lifecycle hooks and event handlers)
```ts
onBeforeMount(async () => {
  const prefetcheddata = await $fetch(`${url}/${props.edit_id}`, { method: 'GET' })
  state.value = prefetcheddata
})
```

### `$api` Plugin (configured in `app/plugins/api.ts`)
```ts
const { $api } = useNuxtApp()
const response = await $api(url, { method: 'POST', body: validatedData })
// Plugin sets: timeout: 10000, retry: 3
```

**Rule**: `useFetch` for reactive/template-bound data; `$fetch` / `$api` for event handlers and one-time calls.

---

## 11. Form Handling Pattern

The universal form pattern across all form components:

```ts
// 1. Schema import + type extraction
import { payroll } from '~/schema/hrm'
type Schema = z.output<typeof payroll>

// 2. State ref with typed schema
const state = ref<Schema>({ date: '...', status: 'pending' })

// 3. Template ref for the UForm element
const form = useTemplateRef('form')

// 4. Pre-fill data in onBeforeMount for Update mode
onBeforeMount(async () => {
  if (props.formtypeval === 'Update' && props.edit_id) {
    const data = await $fetch(`${url}/${props.edit_id}`, { method: 'GET' })
    state.value = data
  }
})

// 5. Submit via shared submit() composable
async function onSubmit(event: FormSubmitEvent<Schema>) {
  submit(event, payroll, url, props.formtypeval, props.edit_id)
    .then((res) => {
      toast.add({ title: 'Success', description: '...', color: 'success', icon: 'i-lucide-check-circle' })
      emit('result', res.id)
      emit('close', true)
    })
    .catch((error) => {
      form.value?.setErrors(flattenErrors(error?.data?.data))
      toast.add({ title: 'Error', description: error.message, color: 'error' })
    })
}
```

**Template structure**:
```html
<UForm ref="form" :schema="payroll" :state="state" @submit="onSubmit">
  <UFormField name="field_name" label="Label">
    <UInput v-model="state.field_name" />
  </UFormField>
</UForm>
```

**Every form component accepts these standard props**:
```ts
formtypeval: { type: String as () => 'Create' | 'Update', required: true }
edit_id: { type: String, required: false }
```

---

## 12. Modal / Overlay Pattern

```ts
const overlay = useOverlay()

// Open and await result:
const modal = overlay.create(LazyPageHrmStaffprofile)
const instance = modal.open()
const result = await instance.result
```

For alert confirmation dialogs (`Alerts.vue`):
- Props: `title`, `message`, `confirmtext`, `cancelText`, `comp`
- Emits: `close(boolean)`

---

## 13. Error Handling Patterns

```ts
// Form validation errors — DRF-to-FormError conversion
form.value?.setErrors(flattenErrors(error?.data?.data))

// User-facing toast notifications
toast.add({ title: 'Error', description: error.message, color: 'error' })
toast.add({ title: 'Success', description: '...', color: 'success', icon: 'i-lucide-check-circle' })

// Server-side HTTP errors (Nitro)
throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
throw createError({ statusCode: 404, statusMessage: 'User not found' })

// Optional chaining for safe access
error?.data?.data
event?.errors?.[0]?.id
```

`flattenErrors()` in `app/composables/useapifetch.ts` recursively converts Django REST Framework nested error responses into `FormError[]` and fires a toast per error.

---

## 14. Template Patterns

### Conditional Rendering
```html
<div v-if="!collapsed">...</div>
<template v-if="condition">...</template>
<UButton v-if="x" ... />
<UButton v-else ... />
```

### Iteration
```html
<template v-for="item in items" :key="item.id">...</template>
```

### Named Slots with Destructuring
```html
<template #header="{ collapsed }">
  <Logo :collapsed="collapsed" />
</template>
<template #default="{ collapsed }">...</template>
<template #footer="{ collapsed }">...</template>
```

### v-bind Spread
```html
<UButton v-bind="{ trailingIcon: collapsed ? undefined : 'i-lucide-chevrons-up-down' }" />
```

### Lazy Components (Nuxt auto-generated `Lazy` prefix)
```html
<LazyFormsUserProfilepict />
```

### `<ClientOnly>` Wrapper for Client-Only Components
```html
<ClientOnly>
  <Branchswitch collapsed />
</ClientOnly>
```

### Keyboard Shortcuts
```ts
defineShortcuts({
  'g-h': () => router.push('/'),
  'alt_shift_b': () => openmodal.value = true,
  'n': () => isNotificationsSlideoverOpen.value = !isNotificationsSlideoverOpen.value
})
```

---

## 15. CSS / Styling Patterns

- **Exclusively Tailwind CSS** — no custom CSS, only empty scoped style blocks when present
- **Dark mode** via `dark:` variants: `class="bg-white dark:bg-gray-900"`
- **Responsive** via breakpoint prefixes: `class="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"`
- **CSS custom properties** for theme tokens (in SVG/inline): `fill="var(--ui-primary)"`, `color="var(--ui-muted)"`
- **`@nuxt/ui` component library** is the primary UI toolkit — all interactive elements use `U`-prefixed components:
  ```
  UButton, UInput, UForm, UFormField, UModal, UCard, UTabs, UDropdownMenu,
  USelectMenu, UNavigationMenu, UDashboardGroup, UDashboardSidebar,
  UDashboardPanel, UDashboardNavbar, USeparator, UTooltip, UBadge,
  UChip, UIcon, UAvatar, UUser, UContainer
  ```
- **`app.config.ts`** overrides UI component slot classes with deep Tailwind string configs:
  ```ts
  ui: {
    colors: { primary: "teal", neutral: "zinc" },
    avatar: { slots: { root: "rounded-md" } },
  }
  ```

---

## 16. Page-Level Patterns

**Pages are thin** — they primarily just mount a form/component:
```html
<template>
  <FormsAuthSignIn />
</template>
```

**`definePageMeta()`** at the top of script for layout assignment:
```ts
definePageMeta({ layout: 'auth' })
definePageMeta({ layout: 'default1' })
```

**`useSeoMeta()`** for SEO metadata:
```ts
useSeoMeta({ title: 'Page Title', description: 'Description' })
```

---

## 17. Layout Architecture

Six named layouts (in `app/layouts/`):
| Layout | Purpose |
|--------|---------|
| `default` | Full dashboard with collapsible `UDashboardGroup` + `UDashboardSidebar` |
| `auth` | Split-screen (form left, decorative SVG right) |
| `inventory` | Sub-navigation sidebar panel for inventory module |
| `hrm` | Deep nested navigation tree for HRM module |
| `noauth` | Public unauthenticated pages |
| `setting`, `ecom`, `test` | Specialized module layouts |

Navigation items are typed as `NavigationMenuItem[][]` (array of groups) loaded from `layouts/urls/`.

---

## 18. Server-Side Patterns (Nitro)

### Event Handler Structure
```ts
export default defineEventHandler(async event => {
  await requireUserSession(event)  // auth guard — first line
  // ...
})
```

### Session Management (`nuxt-auth-utils`)
```ts
const session = await getUserSession(event)
const token = session?.secure?.token

await setUserSession(event, {
  user: { ... },
  secure: { token: `Token ${data.token}` },
  loggedInAt: new Date()
})
await clearUserSession(event)
await replaceUserSession(event, { ... })
```

### Server-Side Caching
```ts
export const getcurrentuser = defineCachedFunction(async (event, token) => {
  return await fetchApi('/users/api/getuser', { method: 'GET' }, event)
}, {
  maxAge: 60 * 60 * 3,
  name: 'currentuser',
  getKey: async (event, token) => token
})
```

### Proxy Architecture
`server/api/serv/[...].ts` is a catch-all that proxies all `/api/serv/*` calls to the Django backend, injecting the auth token, branch cookie, and department cookie. Scheduled tasks run before/after each request.

### Typed Catch-All Wildcard Route (`server/api/serv/[...].ts`)

This route receives **every** request under `/api/serv/*` and maps it to a backend path. Because it is a single gateway for many endpoints, typing must be enforced at three levels:

1. **Route key typing** (which paths/methods are allowed)
2. **Input typing** (params/query/body shape)
3. **Output typing** (response payload shape)

#### How the wildcard route works

`[...].ts` captures a dynamic path segment array. For example:

- `GET /api/serv/users/api/getuser` -> route param `['users', 'api', 'getuser']`
- `POST /api/serv/inv/api/item/create` -> route param `['inv', 'api', 'item', 'create']`

Implementation flow should be:

1. Read and normalize the wildcard path.
2. Resolve it against a typed route registry (`server/utils/all.ts`).
3. Validate HTTP method against route's allowed methods.
4. Validate incoming query/body with a schema (Zod).
5. Forward request to backend (`fetchApi`) with auth/cookies headers.
6. Validate backend response with a schema (Zod) before returning.
7. Return a typed payload to callers.

#### Route registry should be strongly typed

Define route contracts as data, then infer types from those contracts:

```ts
import { z } from 'zod'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

const GetUserResponse = z.object({
  id: z.string().uuid(),
  username: z.string(),
  email: z.string().email().optional(),
})

const UpdateUserBody = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
})

export const routeContracts = {
  '/users/api/getuser': {
    methods: ['GET'] as const,
    query: z.object({}).optional(),
    body: z.undefined(),
    response: GetUserResponse,
  },
  '/users/api/update': {
    methods: ['PATCH'] as const,
    query: z.object({}).optional(),
    body: UpdateUserBody,
    response: GetUserResponse,
  },
} as const

type RouteKey = keyof typeof routeContracts
```

This prevents accidental proxying of unknown endpoints and gives method/body/response type inference from one source of truth.

#### Wildcard handler implementation pattern

Use a generic helper to parse and validate both input and output:

```ts
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  await requireUserSession(event)

  const method = getMethod(event).toUpperCase() as HttpMethod
  const segments = getRouterParam(event, '...')
  const path = `/${Array.isArray(segments) ? segments.join('/') : segments || ''}` as RouteKey

  const contract = routeContracts[path]
  if (!contract) {
    throw createError({ statusCode: 404, statusMessage: 'Unknown API route' })
  }

  if (!contract.methods.includes(method as never)) {
    throw createError({ statusCode: 405, statusMessage: 'Method not allowed' })
  }

  const queryInput = getQuery(event)
  const bodyInput = ['POST', 'PUT', 'PATCH'].includes(method) ? await readBody(event) : undefined

  const query = contract.query ? contract.query.parse(queryInput) : undefined
  const body = contract.body ? contract.body.parse(bodyInput) : undefined

  const upstream = await fetchApi(path, {
    method,
    query,
    body,
  }, event)

  // Guarantees the response shape returned to frontend callers.
  return contract.response.parse(upstream)
})
```

#### How to keep return data always typed

- Never return raw `any` from `[...].ts`; always parse with `contract.response.parse(...)`.
- Avoid `as SomeType` casts for untrusted data; prefer runtime validation with Zod.
- For each new proxied backend endpoint, add one contract entry with `methods`, `body`, `query`, and `response`.
- Use inferred types for consumers:

```ts
type ContractOf<K extends RouteKey> = (typeof routeContracts)[K]
type ResponseOf<K extends RouteKey> = z.output<ContractOf<K>['response']>
```

This allows typed frontend/server utility functions such as:

```ts
async function callServ<K extends RouteKey>(
  path: K,
  options: { method: ContractOf<K>['methods'][number]; body?: unknown; query?: unknown }
): Promise<ResponseOf<K>> {
  return await $fetch(`/api/serv${path}`, options)
}
```

#### Validation error shape recommendation

Normalize all schema failures to a stable response format so UI forms can consume errors consistently:

```ts
{
  statusCode: 400,
  message: 'Validation failed',
  errors: [
    { path: 'first_name', message: 'String must contain at least 1 character' }
  ]
}
```

This aligns with the existing `flattenErrors()` form pipeline and keeps form error handling predictable.

### Detailed Function Guide for `server/utils/fetc.ts`

`fetc.ts` is the server-side transport and authorization helper layer used by many Nitro API routes. It centralizes:

- Upstream Django API calls (`fetchApi`)
- Input/output validation hooks (Zod)
- Session and permission checks
- Cache wrappers
- Shared routing utilities for wildcard-style endpoints

Below is a function-by-function reference.

#### `extractPathFromUrl(url: string): string`

Purpose:
- Extracts only the path and query string from a full URL.

How it works:
- Creates a `URL` object from `url`.
- Reads `pathname` and `search`.
- Returns `pathname + search`.

Typical use:
- Used by cache key logic to normalize URLs before key creation.

#### `cachekey(url: string, event: H3Event<EventHandlerRequest>): string`

Purpose:
- Builds a deterministic cache key from request context.

Inputs used:
- Cookies: `company`, `department`, `branch`
- Request method (`event.method`)
- Normalized path from `extractPathFromUrl(url)`
- Query is read and sorted, but currently not included in the final returned key.

Behavior:
- For mutating methods (`POST`, `PUT`, `DELETE`) it prefixes key with `refresh.__.`.
- For non-mutating methods it returns a regular key.

Notes:
- Current return value does not include sorted query params even though they are computed; this can cause key collisions between different query strings.

#### `getIPAddress(event: H3Event<EventHandlerRequest>): Promise<string>`

Purpose:
- Returns request origin as `protocol://ip`.

Behavior:
- Uses Nitro helpers `getRequestIP(event)` and `getRequestProtocol(event)`.
- Logs IP/protocol.
- Returns `${protocol}://${ip}`.

Notes:
- Contains commented proxy-forwarded IP logic for production.

#### `fetchApi<T>(path: string, options: FetchOptions = {}, event: H3Event<EventHandlerRequest>)`

Purpose:
- Core upstream HTTP client for backend calls.
- Injects auth/session context and standard retry/timeout/error behavior.

Detailed flow:
1. Reads active user session and token via `getUserSession(event)`.
2. Reads branch/department cookies.
3. Creates local error storage (`unstorage` with `fsDriver` under `./tmp/errors`).
4. Calls `$fetch(useRuntimeConfig(event).golderppath + path, ...)`.
5. Adds `Authorization` header with session token.
6. Applies defaults: `timeout: 10000`, `retry: 3`, `retryDelay: 600`.
7. Merges request query params and injects `currentbranch` in `onRequest`.
8. In `onResponse`: checks session expiry and extends session timeout by 30 minutes when valid.
9. In `onResponseError`: maps backend status codes into `createError(...)` objects:
   - `401`: clears session, redirects to `/sign-in`, throws unauthorized error.
   - `403`: throws forbidden.
   - `500`: throws rich error with `_data`, stack, cause, message.
   - `400` on write methods: throws validation-oriented error payload.
   - Others: throws generalized structured error.

Output:
- Returns upstream payload when successful.
- Throws Nitro `createError` for handled error paths.

#### `requestsid<T>(url: string, event: H3Event<EventHandlerRequest>, geturl?: string, bodySchema?: ZodType<T>, dataSchema?: ZodType<T>)`

Purpose:
- Handles CRUD-like endpoints that require a slug route param and optional `extra` segment.

Detailed flow:
1. Requires authenticated session (`requireUserSession`).
2. Reads `slug` and `extra` from route params.
3. Builds path: ``${url}${id}/${extra ? extra + '/' : ''}``.
4. For write methods, reads body and validates it with `bodySchema` if provided.
5. Branches by method:
   - `GET`: optional URL override (`geturl`), fetches data, validates with `dataSchema`.
   - `PUT`: forwards body, validates response with `dataSchema`.
   - `PATCH`: forwards body, validates response with `dataSchema`.
   - `DELETE`: forwards delete request.
   - `POST` with `extra`: forwards post request.
   - Otherwise throws `405`.

Output:
- Returns parsed/validated data when schema checks succeed.
- Returns raw data otherwise.

Notes:
- Has broad `try/catch` that can return `error` directly in outer catch, which weakens return typing.

#### `requested<T>(url: string, event: H3Event<EventHandlerRequest>, geturl?: string, bodySchema?: ZodType<T>, dataSchema?: ZodType<T>)`

Purpose:
- Generic helper for list GET and create POST requests (non-slug endpoints).

Detailed flow:
- Requires user session.
- `GET` path:
  - Optional URL override via `geturl`.
  - Calls `fetchApi`.
  - Rewrites paginated `next` and `previous` links by removing backend base URL.
  - If `dataSchema` is provided, validates `responseData.results` as `z.array(dataSchema)`.
- `POST` path:
  - Reads and validates body via `bodySchema`.
  - Calls `fetchApi` with POST body.
  - Validates response with `dataSchema` when provided.

Output:
- Returns paginated list object or created object depending on method.

Notes:
- `catch` currently logs errors and does not consistently rethrow, so callers may receive `undefined` on failure.

#### `getrequestcached<T>(url: string, event: H3Event<EventHandlerRequest>)`

Purpose:
- GET-only wrapper around `fetchApi` with pagination link normalization.

Behavior:
- Requires user session.
- Accepts only `GET`; otherwise throws `408` in current implementation.
- Calls `fetchApi` and maps errors into `createError` with structured metadata.
- Rewrites `next` and `previous` links to internal relative API paths.

Output:
- Returns fetched data object.

#### `postcached<T>(url: string, event: H3Event<EventHandlerRequest>, bodySchema?: ZodType<T>, dataSchema?: ZodType<T>)`

Purpose:
- POST-only wrapper with optional body/response Zod validation.

Behavior:
- Requires user session.
- Reads body and validates with `bodySchema` if provided.
- Calls `fetchApi` using `POST`.
- If `dataSchema` exists, runs `safeParse` on response.

Output:
- Returns raw response data when no `dataSchema`.
- Returns parse result object when `dataSchema` is used.

Notes:
- Uses `if (dataSchema.safeParse(data))` pattern; for strict typing, prefer checking `.success` and returning parsed `.data` only.

#### `cachingmain`

Signature:
- `defineCachedFunction(async (event: H3Event, url: string) => ...)`

Purpose:
- Caches GET results from `requested(url, event)`.

Cache config:
- `maxAge: 100 * 60`
- `name: 'CachedUserData'`
- `getKey`: derived from `getcompany_token(url, event)`.

Behavior:
- Allows only `GET`; throws on other methods.

#### `validate_alldata(url: string, event: H3Event<EventHandlerRequest>, query?: {})`

Purpose:
- Convenience validator to ensure a list endpoint returns at least one result.

Behavior:
- Calls `fetchApi` with GET and optional query.
- Checks `data.results.length`.
- Returns:
  - `{ success: false, data: 'No data found' }` when empty.
  - `{ success: true, data: data.results }` when not empty.

#### `cachedpermissions`

Signature:
- `defineCachedFunction(async (event, company) => ...)`

Purpose:
- Caches permissions list fetch for a company context.

Behavior:
- Calls `requested('/users/permission/?size=10000', event)`.
- Cache key is `company`.
- Cache `maxAge` is one hour.

#### `type permobj`

Purpose:
- Encodes per-method permission mapping object:

```ts
type permobj = {
  post?: string
  get?: string
  put?: string
  delete?: string
}
```

Used by:
- `allroutesperms(...)` to resolve required permission for current method.

#### `allroutesperms(event: H3Event<EventHandlerRequest>, permission: permobj)`

Purpose:
- Method-aware permission resolver and authorizer.

Behavior:
- Maps `event.method` to corresponding key in `permobj`.
- Throws if method unsupported or permission missing.
- Calls `authorize(event, allowperm, perm)`.

Output:
- Returns result of authorization check.

#### `slug_it(str: string): string`

Purpose:
- Normalizes free text into URL-safe slug.

Transform steps:
- Trim whitespace.
- Lowercase.
- Remove diacritics via Unicode normalization.
- Replace non-alphanumeric chars with spaces.
- Collapse spaces/hyphens to single hyphen.
- Trim leading/trailing hyphens.

Output:
- Stable slug string (e.g., `"Amoxicillin 500mg" -> "amoxicillin-500mg"`).

#### `useMianAuth(event: H3Event<EventHandlerRequest>)`

Purpose:
- Main authorization/router guard for dynamic server routes tied to `mainserverlinks`.

Detailed flow:
1. Requires session.
2. Reads dynamic param `event.context.params?._`.
3. Validates route shape length (`base[/slug][/extra]`, max 3 segments).
4. Extracts `base`, `slug`, `extra`.
5. Looks up `base` in `mainserverlinks` route registry.
6. Resolves allowed method entry for current `event.method` (and `extra` when present).
7. Verifies permission via `authorize(allowperm, allowedmethod.permission)`.
8. Validates `extra` format and match against allowed method metadata.

Output:
- Returns tuple `[url, slug, extra] as const` for downstream handlers.

Notes:
- UUID validation is present but currently not enforced (commented-out throw path).
- Function name is spelled `useMianAuth` in source; keep this exact name unless refactoring everywhere.

### Server Route File Naming
```
sign-in.post.ts      → POST /api/sign-in
preferences.get.ts   → GET /api/preferences
[...].ts             → wildcard catch-all
```

---

## 19. Schema Patterns (Zod)

All schemas live in `app/schema/` and are shared with server code.

### Reusable Base Schemas (`app/schema/addon.ts`)
```ts
export const createdtimestamp_uid = z.object({
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  id: z.string().uuid(),
})
```

### Composition via `.merge()` and `.extend()`
```ts
export const dosageForm = z.object({ ... }).merge(createdtimestamp_uid)

const dataSchema = employeemanagement.extend({
  staff_username: z.string(),
  leave_days: z.number(),
})
```

### Common Field Patterns
```ts
z.string().uuid()                          // foreign key ID
z.array(z.string().uuid()).default([])     // many-to-many
z.enum(['pending', 'active', 'completed']) // enum choices
z.number().min(0).multipleOf(0.01)         // monetary decimal
z.string().date()                          // date-only field
z.string().datetime()                      // full datetime
z.string().uuid().or(z.null())             // nullable FK
z.boolean().default(false)                 // boolean with default
z.string().min(1).max(100)                 // validated string
```

---

## 20. Recurring Idioms & Project-Specific Conventions

- **Branch switching**: multi-branch system using `useCookie('branch')` + `POST /api/auth/switchbranch`; `<Branchswitch>` appears in every layout
- **Form Create/Update duality**: every form component accepts `formtypeval: 'Create' | 'Update'` and `edit_id?: string`
- **`@ts-nocheck`**: used in `useform.ts` to suppress legacy code — acceptable for legacy files
- **Commented-out code is preserved**: old implementations and migration notes are kept inline as history
- **Inline technical debt acknowledgment**: `// not a scalable way to do it but works for now` — pragmatic, incremental development style
- **HMR support** in every Pinia store:
  ```ts
  if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
  }
  ```
- **`$fetch` vs `useFetch` rule**: use `useFetch` in `<script setup>` for reactive data; use `$fetch` in `onBeforeMount`, event handlers, and composable utilities
- **`useTemplateRef('form')`** instead of the older `ref<InstanceType<...>>(null)` pattern for template refs
- **URL configuration files** in `app/layouts/urls/` define navigation menus per module — navigation is data-driven, not hardcoded in templates
