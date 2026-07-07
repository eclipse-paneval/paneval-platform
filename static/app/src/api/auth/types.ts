export type AuthUser = {
  id?: number | string
  name?: string
  username?: string
  email?: string
  avatar?: string
  status?: string
  phone?: string
  organization?: string
  organizationEn?: string
  platform?: string
  tasks?: string[]
  isResearcher?: boolean
  isPrivateModel?: boolean
  huggingface?: string
}

export type LoginPayload = {
  username: string
  password: string
}
