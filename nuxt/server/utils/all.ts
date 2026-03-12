import { z } from 'zod'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

const signInBodySchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1)
})

const signInResponseSchema = z.object({
  token: z.string(),
  user: z.object({
    id: z.union([z.string(), z.number()]),
    username: z.string()
  }).passthrough()
}).passthrough()

const profileResponseSchema = z.object({
  id: z.union([z.string(), z.number()]),
  username: z.string(),
  email: z.string().email().optional().nullable()
}).passthrough()

export const routeContracts = {
  '/auth/sign-in': {
    methods: ['POST'] as const,
    query: z.object({}).optional(),
    body: signInBodySchema,
    response: signInResponseSchema
  },
  '/users/api/getuser': {
    methods: ['GET'] as const,
    query: z.object({}).optional(),
    body: z.undefined(),
    response: profileResponseSchema
  }
} as const

export type RouteKey = keyof typeof routeContracts

export type ContractOf<K extends RouteKey> = (typeof routeContracts)[K]
export type ResponseOf<K extends RouteKey> = z.output<ContractOf<K>['response']>

export const mainserverlinks = Object.keys(routeContracts) as RouteKey[]
