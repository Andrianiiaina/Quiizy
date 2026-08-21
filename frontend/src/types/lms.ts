export type LPStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'

export interface LearningPath {
  id: string
  created_by: string
  title: string
  description: string | null
  status: LPStatus
  created_at: string
  updated_at: string
}

export interface LPCourseItem {
  course_id: string
  position: number
}

export type AssignmentTargetType = 'COURSE' | 'LEARNING_PATH'
export type AssignmentStatus = 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'EXPIRED' | 'CANCELLED'

export interface Assignment {
  id: string
  user_id: string
  assigned_by: string
  target_type: AssignmentTargetType
  target_id: string
  starts_at: string | null
  due_date: string | null
  status: AssignmentStatus
  created_at: string
}

export type EnrollmentStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'OVERDUE' | 'CANCELLED'

export interface Enrollment {
  id: string
  user_id: string
  assignment_id: string
  course_id: string
  learning_path_id: string | null
  status: EnrollmentStatus
  progress_percent: number
  started_at: string | null
  completed_at: string | null
  due_date: string | null
  created_at: string
}

export type ProgressStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'

export interface ContentProgress {
  id: string
  enrollment_id: string
  content_id: string
  status: ProgressStatus
  progress_percent: number
  last_position: string | null
  completed_at: string | null
}

export type QuizStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED'

export interface QuizOption {
  id: string
  text: string
  position: number
}

export interface QuizOptionWithAnswer extends QuizOption {
  is_correct: boolean
}

export interface QuizQuestion {
  id: string
  question: string
  position: number
  options: QuizOption[]
}

export interface QuizQuestionResult {
  id: string
  question: string
  explanation: string
  position: number
  options: QuizOptionWithAnswer[]
}

export interface Quiz {
  id: string
  course_id: string
  version: number
  status: QuizStatus
  difficulty: 'EASY' | 'MEDIUM' | 'HARD'
  question_count: number
  generated_at: string | null
}

export interface QuizDetail extends Quiz {
  questions: QuizQuestion[]
}

export interface GenerationJob {
  id: string
  course_id: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
}

export interface QuizAttempt {
  id: string
  quiz_id: string
  enrollment_id: string
  started_at: string
  completed_at: string | null
  score: number | null
  questions: QuizQuestion[]
}

export interface QuizAnswer {
  id: string
  question_id: string
  selected_option_id: string
  is_correct: boolean
}

export interface AttemptResult {
  id: string
  quiz_id: string
  score: number | null
  started_at: string
  completed_at: string | null
  answers: QuizAnswer[]
  questions: QuizQuestionResult[]
}
