export type ContentType = 'TEXT' | 'PDF' | 'CSV' | 'AUDIO' | 'WEB_LINK'

export interface FileAssetSummary {
  id: string
  original_filename: string
  mime_type: string
  size_bytes: number
}

export interface FileAsset extends FileAssetSummary {
  created_at: string
}

export interface CourseContent {
  id: string
  course_id: string
  type: ContentType
  title: string
  text_content: string | null
  file_asset_id: string | null
  file_asset: FileAssetSummary | null
  external_url: string | null
  position: number
  created_at: string
  updated_at: string
}

export interface CreateContentRequest {
  type: ContentType
  title: string
  text_content?: string | null
  file_asset_id?: string | null
  external_url?: string | null
}
