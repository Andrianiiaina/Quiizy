export interface Category {
  id: string
  name: string
  description: string | null
  created_at: string
}

export type CourseStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'

export interface Course {
  id: string
  owner_id: string
  category_id: string | null
  category: { id: string; name: string } | null
  title: string
  description: string | null
  status: CourseStatus
  created_at: string
  updated_at: string
}

export interface CreateCourseRequest {
  title: string
  description?: string | null
  category_id?: string | null
}

export interface UpdateCourseRequest {
  title?: string
  description?: string | null
  category_id?: string | null
}
