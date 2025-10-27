import { useState, useEffect } from 'react';

function ConversationalMode({ imageFile, onResults, isProcessing, setIsProcessing, apiUrl }) {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle', 'uploading', 'ready', 'error'

  const predefinedQuestions = [
    "Was ist der Außendurchmesser?",
    "Liste alle Maße mit Toleranzen auf",
    "Welche Materialspezifikationen sind angegeben?",
    "Extrahiere alle Teilenummern",
    "Was sind die kritischen Maße?",
    "Beschreibe die technischen Details",
    "Was steht in der Stückliste?",
    "Was ist der Maßstab dieser Zeichnung?",
    "Zeige mir alle Ansichten (Views) in dieser Zeichnung", // View detection with grounding
  ];

  // Upload image when imageFile changes
  useEffect(() => {
    if (!imageFile) {
      setSessionId(null);
      setUploadStatus('idle');
      setChatHistory([]);
      return;
    }

    const uploadImage = async () => {
      setUploadStatus('uploading');
      setIsProcessing(true);

      try {
        const formData = new FormData();
        formData.append('file', imageFile);

        const response = await fetch(`${apiUrl}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status}`);
        }

        const data = await response.json();
        setSessionId(data.session_id);
        setUploadStatus('ready');

        // Pass detected elements to parent (for bounding box visualization)
        if (data.detected_elements && data.detected_elements.length > 0) {
          onResults({
            detected_elements: data.detected_elements,
            image_width: data.image_width,
            image_height: data.image_height,
            text: `Automatisch ${data.detected_elements.length} Elemente erkannt`,
            markdown: ''
          });
        }

        // Add system message to chat
        const elementsMsg = data.detected_elements && data.detected_elements.length > 0
          ? ` (${data.detected_elements.length} Ansichten/Elemente erkannt)`
          : '';
        setChatHistory([{
          type: 'system',
          content: `✓ ${data.message}${elementsMsg}`
        }]);

      } catch (error) {
        console.error('Error uploading image:', error);
        setUploadStatus('error');
        setChatHistory([{
          type: 'error',
          content: `Upload-Fehler: ${error.message}`
        }]);
      } finally {
        setIsProcessing(false);
      }
    };

    uploadImage();
  }, [imageFile, apiUrl, setIsProcessing]);

  const askQuestion = async (questionText) => {
    if (!sessionId || !questionText.trim() || isProcessing) return;

    setIsProcessing(true);
    const userQuestion = questionText.trim();

    // Add user question to chat
    setChatHistory(prev => [...prev, { type: 'user', content: userQuestion }]);
    setQuestion('');

    try {
      // Enable grounding for view detection and localization queries
      const enableGrounding = userQuestion.toLowerCase().includes('ansicht') ||
                             userQuestion.toLowerCase().includes('view') ||
                             userQuestion.toLowerCase().includes('zeige') ||
                             userQuestion.toLowerCase().includes('locate') ||
                             userQuestion.toLowerCase().includes('wo ist') ||
                             userQuestion.toLowerCase().includes('finde');

      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('question', userQuestion);
      formData.append('use_grounding', enableGrounding ? 'true' : 'false');

      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response to chat
      const answerText = data.markdown || data.text || 'Keine Antwort';
      setChatHistory(prev => [...prev, {
        type: 'assistant',
        content: answerText,
        elements: data.detected_elements || [],
        processingTime: data.processing_time
      }]);

      // Also pass to parent for bounding box display
      onResults(data);

    } catch (error) {
      console.error('Error asking question:', error);
      setChatHistory(prev => [...prev, {
        type: 'error',
        content: `Fehler: ${error.message}`
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    askQuestion(question);
  };

  return (
    <div className="space-y-4">
      {/* Chat History */}
      <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 space-y-4 max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-blue-500 scrollbar-track-gray-700">
        {uploadStatus === 'uploading' ? (
          <div className="text-center text-blue-200 py-8">
            <div className="text-4xl mb-3">⏳</div>
            <div className="text-lg font-semibold mb-2">Bild wird verarbeitet...</div>
            <div className="text-sm">
              Das Bild wird hochgeladen und vorbereitet
            </div>
          </div>
        ) : chatHistory.length === 0 ? (
          <div className="text-center text-blue-200 py-8">
            <div className="text-4xl mb-3">💬</div>
            <div className="text-lg font-semibold mb-2">Konversationelle OCR</div>
            <div className="text-sm">
              Stellen Sie Fragen zu Ihrer technischen Zeichnung in natürlicher Sprache
            </div>
          </div>
        ) : (
          chatHistory.map((message, idx) => (
            <div key={idx} className={`flex ${message.type === 'user' ? 'justify-end' : message.type === 'system' ? 'justify-center' : 'justify-start'} mb-4`}>
              <div className={`
                ${message.type === 'system' ? 'max-w-[100%] bg-green-500/10 border border-green-500/30 text-green-200 text-center' : 'max-w-[85%]'} rounded-xl p-4 shadow-lg
                ${message.type === 'user' ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' :
                  message.type === 'error' ? 'bg-red-500/20 text-red-200 border-2 border-red-500' :
                  message.type === 'system' ? '' :
                  'bg-gradient-to-br from-slate-700/80 to-slate-800/80 text-white border border-slate-600/50'}
              `}>
                {message.type === 'user' && (
                  <div className="text-xs text-blue-100 mb-1">Sie fragten:</div>
                )}
                {message.type === 'assistant' && (
                  <div className="text-xs text-slate-300 mb-2 flex items-center gap-2">
                    <span className="font-semibold">🤖 KI-Antwort</span>
                    <span className="bg-slate-600/50 px-2 py-0.5 rounded">
                      {message.processingTime?.toFixed(1)}s
                    </span>
                  </div>
                )}
                <div
                  className="text-sm leading-relaxed [&>table]:w-full [&>table]:border-collapse [&>table]:my-2 [&>table_td]:border [&>table_td]:border-slate-500 [&>table_td]:px-2 [&>table_td]:py-1 [&>table_th]:border [&>table_th]:border-slate-400 [&>table_th]:bg-slate-600/50 [&>table_th]:px-2 [&>table_th]:py-1 [&>table_th]:font-semibold"
                  dangerouslySetInnerHTML={{ __html: message.content.replace(/\n/g, '<br/>') }}
                />
                {message.elements && message.elements.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-500/30">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="bg-green-500/20 text-green-300 px-2 py-1 rounded font-medium">
                        📍 {message.elements.length} Elemente lokalisiert
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Quick Questions */}
      {uploadStatus === 'ready' && chatHistory.length <= 1 && (
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-slate-600/30">
          <div className="text-blue-200 text-sm font-semibold mb-3 flex items-center gap-2">
            <span>⚡</span>
            <span>Schnellfragen:</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {predefinedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => askQuestion(q)}
                disabled={!sessionId || isProcessing}
                className="text-left text-sm bg-gradient-to-r from-blue-500/20 to-blue-600/20 hover:from-blue-500/30 hover:to-blue-600/30 disabled:bg-gray-500/20 disabled:cursor-not-allowed text-white px-3 py-2.5 rounded-lg transition-all border border-blue-500/30 hover:border-blue-400/50 hover:shadow-lg"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Question Input */}
      <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-md rounded-lg p-4 border border-slate-600/30 shadow-lg">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={uploadStatus === 'ready' ? "Stellen Sie eine Frage zu dieser Zeichnung..." : "Bitte laden Sie zuerst ein Bild hoch..."}
            disabled={!sessionId || isProcessing}
            className="flex-1 bg-slate-700/50 border-2 border-slate-600/50 rounded-xl px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:bg-slate-700/70 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base"
          />
          <button
            type="submit"
            disabled={!sessionId || !question.trim() || isProcessing}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-xl transition-all font-semibold shadow-lg hover:shadow-xl disabled:shadow-none text-base"
          >
            {isProcessing ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Verarbeite...</span>
              </span>
            ) : (
              'Fragen'
            )}
          </button>
        </div>
        <div className="text-xs text-blue-200 mt-2">
          💡 Tipp: Stellen Sie präzise Fragen für bessere Ergebnisse (z.B. "Welche Maße haben eine Toleranz?" statt "Zeig mir die Maße")
        </div>
      </form>

      {/* Clear Chat Button */}
      {chatHistory.length > 0 && (
        <button
          onClick={() => setChatHistory([])}
          className="w-full bg-red-500/20 hover:bg-red-500/30 text-red-200 px-4 py-2 rounded-lg transition-colors text-sm"
        >
          Chat-Verlauf löschen
        </button>
      )}
    </div>
  );
}

export default ConversationalMode;
