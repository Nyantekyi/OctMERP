import { clearTokens } from '../../utils/backend'

export default defineEventHandler(async event => {
  clearTokens(event)

  return {
    success: true
  }
})
