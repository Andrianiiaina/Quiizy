import type { ContentType } from '@/types/content'

const ICONS: Record<ContentType, string> = {
  TEXT: '📄',
  PDF: '📕',
  CSV: '📊',
  AUDIO: '🎵',
  WEB_LINK: '🔗',
}

const LABELS: Record<ContentType, string> = {
  TEXT: 'Texte',
  PDF: 'PDF',
  CSV: 'CSV',
  AUDIO: 'Audio',
  WEB_LINK: 'Lien web',
}

export function ContentTypeIcon({ type }: { type: ContentType }) {
  return (
    <span title={LABELS[type]} className="text-xl leading-none select-none">
      {ICONS[type]}
    </span>
  )
}
