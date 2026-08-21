import { useState } from 'react'
import { useNavigate, useSearchParams, useParams } from 'react-router-dom'
import { quizzesApi } from '@/features/lms/api'
import type { AttemptResult, QuizAttempt } from '@/types/lms'

export function QuizAttemptPage() {
  const { quizId = '' } = useParams<{ quizId: string }>()
  const [searchParams] = useSearchParams()
  const enrollmentId = searchParams.get('enrollment_id') ?? ''
  const navigate = useNavigate()

  const [attempt, setAttempt] = useState<QuizAttempt | null>(null)
  const [result, setResult] = useState<AttemptResult | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isStarting, setIsStarting] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleStart = async () => {
    setIsStarting(true)
    try {
      const a = await quizzesApi.startAttempt(quizId, enrollmentId)
      setAttempt(a)
    } finally {
      setIsStarting(false)
    }
  }

  const handleComplete = async () => {
    if (!attempt) return
    setIsSubmitting(true)
    try {
      for (const [questionId, optionId] of Object.entries(answers)) {
        await quizzesApi.submitAnswer(attempt.id, { question_id: questionId, selected_option_id: optionId })
      }
      const res = await quizzesApi.complete(attempt.id)
      setResult(res)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (result) {
    return (
      <div className="mx-auto max-w-2xl text-center">
        <div className="rounded-xl border bg-white p-12 shadow-sm">
          <p className="text-6xl font-bold text-gray-900">{result.score}%</p>
          <p className="mt-2 text-lg text-gray-500">{(result.score ?? 0) >= 60 ? '🎉 Félicitations !' : 'Continuez à vous entraîner.'}</p>
          <p className="mt-1 text-sm text-gray-400">
            {result.answers.filter((a) => a.is_correct).length} / {result.questions.length} bonnes réponses
          </p>
          <div className="mt-8 space-y-4 text-left">
            {result.questions.map((q, i) => {
              const myAnswer = result.answers.find((a) => a.question_id === q.id)
              return (
                <div key={q.id} className={`rounded-lg border p-4 ${myAnswer?.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <p className="font-medium text-gray-900">{i + 1}. {q.question}</p>
                  <p className="mt-1 text-sm text-gray-600 italic">{q.explanation}</p>
                </div>
              )
            })}
          </div>
          <button onClick={() => navigate(-1)} className="mt-8 rounded-md bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700">Retour</button>
        </div>
      </div>
    )
  }

  if (!attempt) {
    return (
      <div className="mx-auto max-w-lg text-center">
        <div className="rounded-xl border bg-white p-12 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900">Quiz</h1>
          <p className="mt-2 text-gray-500">Répondez aux questions pour valider vos connaissances.</p>
          <button onClick={handleStart} disabled={isStarting} className="mt-8 rounded-md bg-blue-600 px-8 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
            {isStarting ? 'Chargement…' : 'Démarrer le quiz'}
          </button>
        </div>
      </div>
    )
  }

  const answered = Object.keys(answers).length
  const total = attempt.questions.length

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Quiz</h1>
        <span className="text-sm text-gray-500">{answered}/{total} réponses</span>
      </div>
      <div className="space-y-6">
        {attempt.questions.map((q, i) => (
          <div key={q.id} className="rounded-xl border bg-white p-6 shadow-sm">
            <p className="font-medium text-gray-900">{i + 1}. {q.question}</p>
            <div className="mt-4 space-y-2">
              {q.options.map(opt => (
                <label key={opt.id} className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 hover:bg-gray-50 ${answers[q.id] === opt.id ? 'border-blue-500 bg-blue-50' : ''}`}>
                  <input type="radio" name={q.id} value={opt.id} checked={answers[q.id] === opt.id} onChange={() => setAnswers(prev => ({ ...prev, [q.id]: opt.id }))} className="h-4 w-4 text-blue-600" />
                  <span className="text-sm text-gray-700">{opt.text}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button onClick={handleComplete} disabled={isSubmitting || answered < total} className="w-full rounded-md bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
        {isSubmitting ? 'Soumission…' : answered < total ? `Répondez à toutes les questions (${total - answered} restantes)` : 'Terminer le quiz'}
      </button>
    </div>
  )
}
