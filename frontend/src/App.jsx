
import { useEffect, useState } from 'react'

function App() {
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)

  const [repoUrl, setRepoUrl] = useState('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])

  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [progress, setProgress] = useState('')
  const [error, setError] = useState('')

  // Load all repositories
  const loadRepos = async () => {
    try {
      const response = await fetch('/api/repos')

      if (!response.ok) {
        throw new Error('Could not load repositories')
      }

      const data = await response.json()
      setRepos(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  // Check repository indexing status
  useEffect(() => {
    if (
      !selectedRepo?.id ||
      !['pending', 'cloning', 'indexing'].includes(selectedRepo.status)
    ) {
      return
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/repos/${selectedRepo.id}`)

        if (response.ok) {
          const data = await response.json()
          setSelectedRepo(data)
          loadRepos()
        }
      } catch (err) {
        console.error(err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [selectedRepo?.id, selectedRepo?.status])

  // Add a GitHub repository
  const addRepository = async (e) => {
    e.preventDefault()

    if (!repoUrl.trim()) return

    setAdding(true)
    setError('')
    setProgress('Adding repository...')

    try {
      const response = await fetch('/api/repos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: repoUrl.trim() }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to add repository')
      }

      setRepoUrl('')
      setSelectedRepo(data)
      setMessages([])
      setProgress('Repository added. Cloning and indexing...')
      await loadRepos()
    } catch (err) {
      setError(err.message)
      setProgress('')
    } finally {
      setAdding(false)
    }
  }

  // Select a repository
  const selectRepository = async (repo) => {
    setError('')
    setProgress('Loading repository...')
    setMessages([])

    try {
      const response = await fetch(`/api/repos/${repo.id}`)

      if (!response.ok) {
        throw new Error('Could not load repository details')
      }

      const data = await response.json()
      setSelectedRepo(data)
      setProgress('')
    } catch (err) {
      setError(err.message)
      setProgress('')
    }
  }

  // Delete a repository
  const deleteRepository = async (repoId) => {
    const confirmed = window.confirm(
      'Are you sure you want to delete this repository and its indexed data?'
    )

    if (!confirmed) return

    try {
      const response = await fetch(`/api/repos/${repoId}`, {
        method: 'DELETE',
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete repository')
      }

      if (selectedRepo?.id === repoId) {
        setSelectedRepo(null)
        setMessages([])
      }

      setProgress('Repository deleted successfully.')
      setError('')
      await loadRepos()
    } catch (err) {
      setError(err.message)
    }
  }

  // Send a question using Server-Sent Events
  const askQuestion = async (e) => {
    e.preventDefault()

    if (!question.trim() || !selectedRepo?.id || loading) return

    const currentQuestion = question.trim()

    setQuestion('')
    setError('')
    setLoading(true)
    setProgress('Connecting to assistant...')

    setMessages((previous) => [
      ...previous,
      {
        role: 'user',
        content: currentQuestion,
      },
    ])

    try {
      const response = await fetch(
        `/api/repos/${selectedRepo.id}/chat/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: currentQuestion,
          }),
        }
      )

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to get an answer')
      }

      if (!response.body) {
        throw new Error('Streaming is not supported by this response')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let buffer = ''
      let completed = false

      const processEvent = (eventText) => {
        const lines = eventText.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data:')) continue

          const rawData = line.slice(5).trim()
          if (!rawData) continue

          let payload

          try {
            payload = JSON.parse(rawData)
          } catch {
            continue
          }

          if (payload.status === 'error') {
            throw new Error(payload.message || 'Something went wrong')
          }

          if (payload.status === 'completed') {
            completed = true

            setMessages((previous) => [
              ...previous,
              {
                role: 'assistant',
                content: payload.answer || 'No answer was generated.',
                sources: payload.sources || [],
                tool: payload.tool,
              },
            ])

            setProgress('')
          } else if (payload.message) {
            setProgress(payload.message)
          }
        }
      }

      while (true) {
        const { value, done } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split(/\r?\n\r?\n/)
        buffer = events.pop() || ''

        for (const eventText of events) {
          processEvent(eventText)
        }
      }

      buffer += decoder.decode()

      if (buffer.trim()) {
        processEvent(buffer)
      }

      if (!completed) {
        throw new Error('The response stream ended before completion')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setProgress('')
    }
  }

  const statusColor = (status) => {
    switch (status) {
      case 'ready':
        return 'bg-green-500/15 text-green-400'
      case 'failed':
        return 'bg-red-500/15 text-red-400'
      case 'cloning':
      case 'indexing':
      case 'pending':
        return 'bg-yellow-500/15 text-yellow-400'
      default:
        return 'bg-slate-700 text-slate-300'
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-xl font-bold">
            G
          </div>

          <div>
            <h1 className="text-lg font-bold">
              GitHub Codebase Onboarding Assistant
            </h1>
            <p className="text-xs text-slate-400">
              Understand repositories with AI
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 p-6 lg:grid-cols-3">
        {/* Left panel */}
        <aside className="space-y-6 lg:col-span-1">
          {/* Add repository */}
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="mb-4 text-lg font-semibold">
              Add Repository
            </h2>

            <form onSubmit={addRepository} className="space-y-3">
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-blue-500"
                required
              />

              <button
                type="submit"
                disabled={adding}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
              >
                {adding ? 'Adding...' : '+ Add Repository'}
              </button>
            </form>
          </section>

          {/* Repository list */}
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Repositories</h2>

              <button
                onClick={loadRepos}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                Refresh
              </button>
            </div>

            {repos.length === 0 ? (
              <p className="text-sm text-slate-500">
                No repositories added yet.
              </p>
            ) : (
              <div className="space-y-3">
                {repos.map((repo) => (
                  <div
                    key={repo.id}
                    className={`rounded-lg border p-3 ${
                      selectedRepo?.id === repo.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-slate-800 bg-slate-950'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <button
                        onClick={() => selectRepository(repo)}
                        className="min-w-0 flex-1 text-left"
                      >
                        <p className="truncate font-medium">
                          {repo.owner}/{repo.name}
                        </p>

                        <span
                          className={`mt-2 inline-block rounded-full px-2 py-1 text-xs ${statusColor(
                            repo.status
                          )}`}
                        >
                          {repo.status}
                        </span>
                      </button>

                      <button
                        onClick={() => deleteRepository(repo.id)}
                        title="Delete repository"
                        className="text-sm text-red-400 hover:text-red-300"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </aside>

        {/* Right panel */}
        <section className="flex min-h-[650px] flex-col rounded-xl border border-slate-800 bg-slate-900 lg:col-span-2">
          {!selectedRepo ? (
            <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
              <div className="mb-4 text-5xl">📂</div>
              <h2 className="text-xl font-semibold">
                Welcome to Codebase Assistant
              </h2>
              <p className="mt-2 max-w-md text-sm text-slate-400">
                Add a GitHub repository and ask questions about its code,
                issues, pull requests, and commits.
              </p>
            </div>
          ) : (
            <>
              {/* Repository information */}
              <div className="border-b border-slate-800 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-bold">
                      {selectedRepo.owner}/{selectedRepo.name}
                    </h2>

                    <p className="mt-1 text-xs text-slate-400">
                      {selectedRepo.url}
                    </p>
                  </div>

                  <span
                    className={`rounded-full px-3 py-1 text-xs ${statusColor(
                      selectedRepo.status
                    )}`}
                  >
                    {selectedRepo.status}
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div className="rounded-lg bg-slate-950 p-3">
                    <p className="text-xs text-slate-400">Files Indexed</p>
                    <p className="mt-1 text-xl font-bold">
                      {selectedRepo.files_indexed ?? 0}
                    </p>
                  </div>

                  <div className="rounded-lg bg-slate-950 p-3">
                    <p className="text-xs text-slate-400">Code Chunks</p>
                    <p className="mt-1 text-xl font-bold">
                      {selectedRepo.chunks ?? 0}
                    </p>
                  </div>

                  <div className="rounded-lg bg-slate-950 p-3">
                    <p className="text-xs text-slate-400">Branch</p>
                    <p className="mt-1 truncate text-sm font-bold">
                      {selectedRepo.default_branch || 'Not available'}
                    </p>
                  </div>
                </div>

                {selectedRepo.status === 'failed' && (
                  <p className="mt-3 text-sm text-red-400">
                    {selectedRepo.error || 'Repository indexing failed.'}
                  </p>
                )}
              </div>

              {/* Chat messages */}
              <div className="flex-1 space-y-5 overflow-y-auto p-5">
                {messages.length === 0 && (
                  <div className="py-12 text-center">
                    <div className="mb-3 text-4xl">💬</div>
                    <h3 className="font-semibold">Ask about this repository</h3>
                    <p className="mt-2 text-sm text-slate-400">
                      Try asking what the repository contains or ask about its
                      issues, pull requests, and commits.
                    </p>
                  </div>
                )}

                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === 'user'
                        ? 'justify-end'
                        : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[90%] rounded-xl p-4 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'border border-slate-700 bg-slate-950'
                      }`}
                    >
                      <p className="mb-2 text-xs font-semibold opacity-70">
                        {message.role === 'user' ? 'You' : 'Assistant'}
                      </p>

                      <div className="whitespace-pre-wrap break-words text-sm leading-6">
                        {message.content}
                      </div>

                      {message.tool && (
                        <p className="mt-3 text-xs text-slate-400">
                          Tool used: {message.tool}
                        </p>
                      )}

                      {message.sources?.length > 0 && (
                        <div className="mt-4 border-t border-slate-700 pt-3">
                          <p className="mb-2 text-xs font-semibold text-blue-400">
                            Sources
                          </p>

                          {message.sources.map((source, sourceIndex) => (
                            <div
                              key={sourceIndex}
                              className="mb-2 rounded-lg bg-slate-900 p-3 text-xs"
                            >
                              <p className="break-all font-medium text-slate-200">
                                {source.file_path || source.path || 'Source'}
                              </p>

                              {source.start_line !== undefined && (
                                <p className="mt-1 text-slate-400">
                                  Lines {source.start_line}–{source.end_line}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="rounded-lg bg-slate-950 p-4 text-sm text-blue-300">
                    {progress || 'Thinking...'}
                  </div>
                )}
              </div>

              {/* Question input */}
              <div className="border-t border-slate-800 p-5">
                {selectedRepo.status === 'ready' ? (
                  <form onSubmit={askQuestion} className="flex gap-3">
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask a question about this repository..."
                      disabled={loading}
                      className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-blue-500 disabled:opacity-50"
                    />

                    <button
                      type="submit"
                      disabled={loading || !question.trim()}
                      className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
                    >
                      Send
                    </button>
                  </form>
                ) : (
                  <p className="text-center text-sm text-slate-400">
                    {selectedRepo.status === 'failed'
                      ? 'Indexing failed. Check the repository error above.'
                      : 'Please wait while the repository is being indexed...'}
                  </p>
                )}
              </div>
            </>
          )}
        </section>
      </main>

      {/* Error / progress messages */}
      {(error || progress) && (
        <div className="fixed bottom-5 right-5 max-w-md rounded-lg border border-slate-700 bg-slate-900 px-5 py-3 shadow-xl">
          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}
          {!error && progress && (
            <p className="text-sm text-blue-300">{progress}</p>
          )}
          {error && (
            <button
              onClick={() => setError('')}
              className="mt-2 text-xs text-slate-400 hover:text-white"
            >
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default App
