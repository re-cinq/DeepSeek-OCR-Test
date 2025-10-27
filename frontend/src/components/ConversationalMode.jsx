import { useState } from 'react';

function ConversationalMode({ imageFile, onResults, isProcessing, setIsProcessing, apiUrl }) {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  const predefinedQuestions = [
    "What is the outer diameter?",
    "List all dimensions with tolerances",
    "What material specifications are shown?",
    "Extract all part numbers",
    "What are the critical dimensions?",
    "Describe the technical details",
    "What is shown in the BOM table?",
    "What is the scale of this drawing?",
  ];

  const askQuestion = async (questionText) => {
    if (!imageFile || !questionText.trim() || isProcessing) return;

    setIsProcessing(true);
    const userQuestion = questionText.trim();

    // Add user question to chat
    setChatHistory(prev => [...prev, { type: 'user', content: userQuestion }]);
    setQuestion('');

    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('mode', 'custom');
      formData.append('custom_prompt', `<image>\n${userQuestion}`);
      formData.append('grounding', 'true');

      const response = await fetch(`${apiUrl}/api/ocr`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response to chat
      const answerText = data.markdown || data.text || 'No response';
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
        content: `Error: ${error.message}`
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
      <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 space-y-4 max-h-[500px] overflow-y-auto">
        {chatHistory.length === 0 ? (
          <div className="text-center text-blue-200 py-8">
            <div className="text-4xl mb-3">💬</div>
            <div className="text-lg font-semibold mb-2">Conversational OCR</div>
            <div className="text-sm">
              Ask questions about your technical drawing in natural language
            </div>
          </div>
        ) : (
          chatHistory.map((message, idx) => (
            <div key={idx} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`
                max-w-[80%] rounded-lg p-3
                ${message.type === 'user' ? 'bg-blue-500 text-white' :
                  message.type === 'error' ? 'bg-red-500/20 text-red-200 border border-red-500' :
                  'bg-white/10 text-white'}
              `}>
                {message.type === 'user' && (
                  <div className="text-xs text-blue-100 mb-1">You asked:</div>
                )}
                {message.type === 'assistant' && (
                  <div className="text-xs text-blue-200 mb-1">
                    AI Response ({message.processingTime?.toFixed(1)}s)
                  </div>
                )}
                <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                {message.elements && message.elements.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/20 text-xs text-blue-200">
                    Detected {message.elements.length} elements
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Quick Questions */}
      {chatHistory.length === 0 && (
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4">
          <div className="text-blue-200 text-sm font-semibold mb-3">Quick Questions:</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {predefinedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => askQuestion(q)}
                disabled={!imageFile || isProcessing}
                className="text-left text-sm bg-blue-500/20 hover:bg-blue-500/30 disabled:bg-gray-500/20 disabled:cursor-not-allowed text-white px-3 py-2 rounded-lg transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Question Input */}
      <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-md rounded-lg p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about this drawing..."
            disabled={!imageFile || isProcessing}
            className="flex-1 bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-200 focus:outline-none focus:border-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!imageFile || !question.trim() || isProcessing}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors font-semibold"
          >
            {isProcessing ? 'Processing...' : 'Ask'}
          </button>
        </div>
        <div className="text-xs text-blue-200 mt-2">
          💡 Tip: Be specific! Ask about dimensions, materials, part numbers, tables, or any technical details.
        </div>
      </form>

      {/* Clear Chat Button */}
      {chatHistory.length > 0 && (
        <button
          onClick={() => setChatHistory([])}
          className="w-full bg-red-500/20 hover:bg-red-500/30 text-red-200 px-4 py-2 rounded-lg transition-colors text-sm"
        >
          Clear Chat History
        </button>
      )}
    </div>
  );
}

export default ConversationalMode;
