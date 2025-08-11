import { useEffect, useMemo, useRef, useState } from 'react'

const API_BASE = 'http://127.0.0.1:5001'

type ServerStart = { session_id: string; question?: string; error?: string }
type ServerChat = { question?: string; report?: string; session_id?: string; error?: string }

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [topic, setTopic] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [isChatting, setIsChatting] = useState(false)
  const [isReportReady, setIsReportReady] = useState(false)
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false)
  const [agentQuestion, setAgentQuestion] = useState<string>('')
  const [messages, setMessages] = useState<{ sender: 'agent' | 'user'; text: string }[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const canSend = useMemo(() => Boolean(agentQuestion && sessionId), [agentQuestion, sessionId])

  const addMsg = (sender: 'agent' | 'user', text: string) =>
    setMessages((m) => [...m, { sender, text }])

  const startConversation = async () => {
    if (!topic.trim()) return
    setIsStarting(true)
    try {
      const res = await fetch(`${API_BASE}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      })
      const data: ServerStart = await res.json()
      if (data.error) {
        addMsg('agent', `Erreur: ${data.error}`)
        return
      }
      setSessionId(data.session_id)
      setIsChatting(true)
      if (data.question) {
        setAgentQuestion(data.question)
        addMsg('agent', data.question)
      }
    } catch (e: any) {
      addMsg('agent', `Erreur de connexion: ${e?.message ?? e}`)
    } finally {
      setIsStarting(false)
    }
  }

  const sendAnswer = async (answer: string) => {
    if (!sessionId || !answer.trim()) return
    addMsg('user', answer)
    inputRef.current && (inputRef.current.value = '')
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer })
      })
      const data: ServerChat = await res.json()
      if (data.question) {
        setAgentQuestion(data.question)
        addMsg('agent', data.question)
      } else if (data.report) {
        setIsChatting(false)
        setIsReportReady(true)
        setIsGeneratingPDF(true)
        // Afficher un message de transition avant d'activer le téléchargement
        setTimeout(() => setIsGeneratingPDF(false), 4000)
      } else if (data.error) {
        addMsg('agent', `Erreur: ${data.error}`)
      }
    } catch (e: any) {
      addMsg('agent', `Erreur de connexion: ${e?.message ?? e}`)
    }
  }

  const downloadReport = async () => {
    if (!sessionId) return
    try {
      const res = await fetch(`${API_BASE}/download/${sessionId}`)
      if (!res.ok) {
        const err = await res.json()
        addMsg('agent', `Erreur téléchargement: ${err.error}`)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rapport_psychiatrique_${sessionId.substring(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      URL.revokeObjectURL(url)
      a.remove()
      await fetch(`${API_BASE}/cleanup/${sessionId}`, { method: 'POST' })
    } catch (e: any) {
      addMsg('agent', `Erreur: ${e?.message ?? e}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800">
      {/* Background Pattern */}
      <div className="fixed inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(59, 130, 246, 0.3) 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }}></div>
      </div>
      
      <div className="relative max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="sticky top-0 z-50 flex items-center justify-between mb-12 pb-6">
          <div className="flex items-center space-x-4">
            <img src="/logoPsyChat.png" alt="PsyChat logo" className="h-18 w-auto rounded-xl shadow-sm" />
            <div>
              <h1 className="text-xl font-bold text-white">PsyChat</h1>
              <p className="text-sm text-gray-400">Parle-nous, on s’occupe du reste</p>
            </div>
          </div>
          <div className="hidden md:flex items-center space-x-2 text-xs text-gray-500 bg-gray-900/50 px-3 py-2 rounded-lg border border-gray-800">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Confidentiel et sécurisé</span>
          </div>
        </header>

        {/* Main Content */}
        <main className="space-y-8">
          {!sessionId && (
            <section className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-3xl blur-3xl"></div>
              <div className="relative bg-gradient-to-br from-gray-900/90 to-black/90 backdrop-blur-xl border border-gray-700/30 rounded-3xl p-8 md:p-12">
                <div className="text-center mb-8">
                  <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
                    Dis-moi ton souci… on te pose
                    <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
                      10 questions
                    </span>
                  </h2>
                  <p className="text-lg text-gray-300 max-w-2xl mx-auto">
                    Notre assistant vous guide pas à pas et génère un rapport clair, structuré et prêt à partager.
                  </p>
                </div>
                
                <div className="max-w-md mx-auto space-y-4">
                  <div className="relative">
                    <input
                      className="w-full px-6 py-4 bg-gray-800/50 border border-gray-600/50 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-lg"
                      placeholder="Dites-nous ce qui vous préoccupe…"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                    />
                  </div>
                  <button
                    onClick={startConversation}
                    disabled={isStarting || !topic.trim()}
                    className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-2xl transition-all duration-200 transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-lg"
                  >
                    {isStarting ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Initialisation en cours…</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                        </svg>
                        <span>Commencer maintenant</span>
                      </div>
                    )}
                  </button>
                  <div className="flex items-center justify-center space-x-2 text-sm text-gray-500 mt-4">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                    <span>Vos données ne sont pas conservées à l’issue de la session</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {isChatting && (
            <section className="bg-gray-900/50 backdrop-blur-xl border border-gray-700/30 rounded-3xl p-6 md:p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">Entretien clinique en cours</h3>
                <div className="flex items-center space-x-2 text-sm text-gray-400 bg-gray-800/50 px-3 py-1.5 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>Session en cours</span>
                </div>
              </div>
              
              <div className="bg-black/30 rounded-2xl border border-gray-800/50 p-4 h-96 overflow-y-auto mb-4 scroll-smooth">
                {messages.map((m, i) => (
                  <div key={i} className={`flex mb-4 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-4 rounded-2xl ${
                      m.sender === 'agent' 
                        ? 'bg-gray-800/70 text-gray-100 border border-gray-700/50' 
                        : 'bg-gradient-to-r from-blue-500/80 to-blue-600/80 text-white border border-blue-400/30'
                    } shadow-lg`}>
                      <div className="flex items-start space-x-2">
                        {m.sender === 'agent' && (
                          <div className="w-6 h-6 bg-gray-700 rounded-full flex items-center justify-center mt-1 flex-shrink-0">
                            <svg className="w-3 h-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
                            </svg>
                          </div>
                        )}
                        <p className="text-sm leading-relaxed">{m.text}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex space-x-3">
                <input
                  ref={inputRef}
                  className="flex-1 px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  placeholder="Saisissez votre réponse…"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') sendAnswer((e.target as HTMLInputElement).value)
                  }}
                />
                <button
                  onClick={() => sendAnswer(inputRef.current?.value ?? '')}
                  disabled={!canSend}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium rounded-xl transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                  </svg>
        </button>
              </div>
            </section>
          )}

          {isReportReady && (
            <section className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 to-blue-500/10 rounded-3xl blur-2xl"></div>
              <div className="relative bg-gradient-to-br from-gray-900/90 to-black/90 backdrop-blur-xl border border-gray-700/30 rounded-3xl p-8 text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6">
                  {isGeneratingPDF ? (
                    <div className="w-8 h-8 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  )}
                </div>
                {isGeneratingPDF ? (
                  <>
                    <h3 className="text-2xl font-bold text-white mb-4">Entretien terminé</h3>
                    <div className="text-gray-300 mb-8 max-w-lg mx-auto text-base leading-relaxed">
                      <p className="mb-2">Merci pour votre participation. L’entretien clinique est à présent terminé avec succès.</p>
                      <p className="mb-2">Vos réponses sont en cours de traitement afin de générer un rapport psychiatrique professionnel et synthétique.</p>
                      <p className="mb-2">Le rapport PDF sera disponible au téléchargement dans quelques secondes (environ 5–10 s).</p>
                      <p className="">Vos informations restent strictement confidentielles et sécurisées.</p>
                    </div>
                  </>
                ) : (
                  <>
                    <h3 className="text-2xl font-bold text-white mb-4">Rapport généré</h3>
                    <p className="text-gray-300 mb-8 max-w-md mx-auto">
                      Votre rapport PDF est prêt. Il présente l’ensemble des informations de l’entretien de manière claire et structurée.
                    </p>
                    <button
                      onClick={downloadReport}
                      className="inline-flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-blue-400 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-white font-semibold rounded-2xl transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                      <span>Télécharger le rapport PDF</span>
                    </button>
                  </>
                )}
              </div>
            </section>
          )}
        </main>

        {/* Footer */}
        <footer className="mt-16 pt-8 border-t border-gray-800/50 text-center">
          <div className="flex items-center justify-center space-x-2 text-gray-500 text-sm">
            <img src="/logoPsyChat.png" alt="PsyChat logo" className="w-5 h-5 object-contain" />
            <span>PsyChat — Conçu avec des cliniciens, pour les cliniciens</span>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App