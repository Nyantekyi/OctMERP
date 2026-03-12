import { z } from 'zod'

import type { FormError, FormSubmitEvent } from '#ui/types'

function flattenFieldErrors(value: unknown, path: string): FormError[] {
  if (Array.isArray(value)) {
    return value.flatMap((entry) => {
      if (typeof entry === 'string') {
        return [{ name: path, message: entry }]
      }
      return flattenFieldErrors(entry, path)
    })
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, nested]) => {
      const nestedPath = path ? `${path}.${key}` : key
      return flattenFieldErrors(nested, nestedPath)
    })
  }

  if (typeof value === 'string') {
    return [{ name: path, message: value }]
  }

  return []
}

export function flattenErrors(errors: Record<string, unknown>): FormError[] {
  return flattenFieldErrors(errors, '')
}

export async function submit<TSchema extends z.ZodTypeAny>(
  event: FormSubmitEvent<z.output<TSchema>>,
  schema: TSchema,
  url: string,
  formType: 'Create' | 'Update',
  editId?: string
) {
  const payload = schema.parse(event.data)
  const { $api } = useNuxtApp()

  const method = formType === 'Update' ? 'PATCH' : 'POST'
  const endpoint = formType === 'Update' && editId ? `${url}/${editId}` : url

  return await $api(endpoint, {
    method,
    body: payload as Record<string, unknown>
  })
}
