import type { CourseContent } from '@/types/content'
import { ContentTypeIcon } from './ContentTypeIcon'
import { filesApi } from '../api'

interface ContentCardProps {
  content: CourseContent
  canEdit: boolean
  isFirst: boolean
  isLast: boolean
  onMoveUp: () => void
  onMoveDown: () => void
  onDelete: () => void
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / 1024 / 1024).toFixed(1)} Mo`
}

export function ContentCard({
  content, canEdit, isFirst, isLast, onMoveUp, onMoveDown, onDelete,
}: ContentCardProps) {
  return (
    <div className="flex gap-3 rounded-lg border bg-white p-4 shadow-sm">
      <ContentTypeIcon type={content.type} />

      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900">{content.title}</p>

        {content.type === 'TEXT' && content.text_content && (
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">{content.text_content}</p>
        )}

        {content.file_asset && (
          <a
            href={filesApi.downloadUrl(content.file_asset.id)}
            className="mt-1 inline-block text-sm text-blue-600 hover:underline"
          >
            {content.file_asset.original_filename} ({formatBytes(content.file_asset.size_bytes)})
          </a>
        )}

        {content.external_url && (
          <a
            href={content.external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 block truncate text-sm text-blue-600 hover:underline"
          >
            {content.external_url}
          </a>
        )}
      </div>

      {canEdit && (
        <div className="flex shrink-0 flex-col gap-1">
          <button
            onClick={onMoveUp}
            disabled={isFirst}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
            title="Monter"
          >
            ↑
          </button>
          <button
            onClick={onMoveDown}
            disabled={isLast}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
            title="Descendre"
          >
            ↓
          </button>
          <button
            onClick={onDelete}
            className="rounded p-1 text-red-400 hover:bg-red-50"
            title="Supprimer"
          >
            ×
          </button>
        </div>
      )}
    </div>
  )
}
