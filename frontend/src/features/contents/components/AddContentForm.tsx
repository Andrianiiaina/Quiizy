import { useState, useRef } from 'react'
import type { ContentType } from '@/types/content'
import { useCreateContent, useUploadFile } from '../hooks/useContents'

const FILE_TYPES: ContentType[] = ['TEXT', 'PDF', 'CSV', 'AUDIO', 'WEB_LINK']
const LABEL: Record<ContentType, string> = {
  TEXT: 'Texte', PDF: 'PDF', CSV: 'CSV', AUDIO: 'Audio', WEB_LINK: 'Lien web',
}
const ACCEPT: Record<string, string> = {
  PDF: '.pdf', CSV: '.csv', AUDIO: '.mp3,.wav,.ogg,.m4a',
}

const inputCls = 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

interface AddContentFormProps {
  courseId: string
  onSuccess: () => void
}

export function AddContentForm({ courseId, onSuccess }: AddContentFormProps) {
  const [type, setType] = useState<ContentType>('TEXT')
  const [title, setTitle] = useState('')
  const [textContent, setTextContent] = useState('')
  const [externalUrl, setExternalUrl] = useState('')
  const [fileAssetId, setFileAssetId] = useState<string | null>(null)
  const [uploadedName, setUploadedName] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const { mutateAsync: createContent, isPending: isCreating } = useCreateContent(courseId)
  const { mutateAsync: uploadFile, isPending: isUploading } = useUploadFile()

  const handleTypeChange = (newType: ContentType) => {
    setType(newType)
    setFileAssetId(null)
    setUploadedName(null)
    setError(null)
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    try {
      const asset = await uploadFile(file)
      setFileAssetId(asset.id)
      setUploadedName(asset.original_filename)
    } catch {
      setError('Échec de l\'upload. Vérifiez le type et la taille du fichier.')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!title.trim()) { setError('Le titre est requis.'); return }
    try {
      await createContent({
        type,
        title: title.trim(),
        text_content: type === 'TEXT' ? textContent : null,
        file_asset_id: ['PDF', 'CSV', 'AUDIO'].includes(type) ? fileAssetId : null,
        external_url: type === 'WEB_LINK' ? externalUrl : null,
      })
      setTitle(''); setTextContent(''); setExternalUrl('')
      setFileAssetId(null); setUploadedName(null)
      if (fileRef.current) fileRef.current.value = ''
      onSuccess()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      setError(msg ?? 'Une erreur est survenue.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border bg-gray-50 p-4">
      <h4 className="font-medium text-gray-900">Ajouter un contenu</h4>

      <div className="flex gap-2 flex-wrap">
        {FILE_TYPES.map((t) => (
          <button
            key={t} type="button"
            onClick={() => handleTypeChange(t)}
            className={`rounded-full px-3 py-1 text-sm font-medium ${type === t ? 'bg-blue-600 text-white' : 'bg-white border text-gray-700 hover:bg-gray-50'}`}
          >
            {LABEL[t]}
          </button>
        ))}
      </div>

      <input
        type="text" placeholder="Titre *" value={title}
        onChange={(e) => setTitle(e.target.value)}
        className={inputCls}
      />

      {type === 'TEXT' && (
        <textarea
          placeholder="Contenu textuel *" value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          rows={4} className={inputCls + ' resize-none'}
        />
      )}

      {['PDF', 'CSV', 'AUDIO'].includes(type) && (
        <div>
          <input
            ref={fileRef} type="file" accept={ACCEPT[type]}
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
          />
          {isUploading && <p className="mt-1 text-xs text-blue-600">Upload en cours…</p>}
          {uploadedName && !isUploading && (
            <p className="mt-1 text-xs text-green-600">✓ {uploadedName}</p>
          )}
        </div>
      )}

      {type === 'WEB_LINK' && (
        <input
          type="url" placeholder="https://example.com *" value={externalUrl}
          onChange={(e) => setExternalUrl(e.target.value)}
          className={inputCls}
        />
      )}

      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <button
        type="submit" disabled={isCreating || isUploading}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isCreating ? 'Ajout…' : 'Ajouter'}
      </button>
    </form>
  )
}
