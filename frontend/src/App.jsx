import { useState, useRef } from 'react';
import ImageUpload from './components/ImageUpload';
import ModeSelector from './components/ModeSelector';
import ResultsDisplay from './components/ResultsDisplay';
import BoundingBoxOverlay from './components/BoundingBoxOverlay';
import ConversationalMode from './components/ConversationalMode';

// Use environment variable or default to same host on port 8000
const API_URL = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

function App() {
  const [interfaceMode, setInterfaceMode] = useState('structured'); // 'structured' or 'conversational'
  const [selectedMode, setSelectedMode] = useState('technical_drawing');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null); // Store file for conversational mode
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);

  const handleImageUpload = async (file) => {
    // Store the file for conversational mode
    setUploadedFile(file);

    // For images, create object URL for preview. For PDFs, set null (will show message)
    if (file.type.startsWith('image/')) {
      setUploadedImage(URL.createObjectURL(file));
    } else if (file.type === 'application/pdf') {
      setUploadedImage('PDF');  // Special marker for PDF files
    }
    setResults(null);
    setError(null);

    // Only auto-process in structured mode
    if (interfaceMode === 'structured') {
      setIsProcessing(true);
    } else {
      // In conversational mode, just upload without processing
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', selectedMode);
      formData.append('grounding', 'true');
      formData.append('extract_dimensions', 'true');
      formData.append('extract_part_numbers', 'true');
      formData.append('extract_tables', 'true');

      const response = await fetch(`${API_URL}/api/ocr`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'OCR processing failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
      console.error('Error processing image:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            re:cinq - OCR Platform
          </h1>
          <p className="text-blue-200 text-lg">
            Technical Drawing Analysis & OCR
          </p>
          <p className="text-blue-300 text-sm mt-1">
            Powered by DeepSeek-VL with vLLM
          </p>
        </div>

        {/* Interface Mode Toggle */}
        <div className="mb-6 flex justify-center gap-2">
          <button
            onClick={() => setInterfaceMode('structured')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              interfaceMode === 'structured'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-blue-200 hover:bg-white/20'
            }`}
          >
            📊 Structured OCR
          </button>
          <button
            onClick={() => setInterfaceMode('conversational')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              interfaceMode === 'conversational'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-blue-200 hover:bg-white/20'
            }`}
          >
            💬 Conversational
          </button>
        </div>

        {/* Mode Selector - Only show in structured mode */}
        {interfaceMode === 'structured' && (
          <div className="mb-6">
            <ModeSelector
              selectedMode={selectedMode}
              onModeChange={setSelectedMode}
              disabled={isProcessing}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Upload & Image Display */}
          <div className="space-y-4">
            <ImageUpload
              onImageUpload={handleImageUpload}
              disabled={isProcessing}
            />

            {uploadedImage && (
              <div className="bg-white/10 backdrop-blur-md rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-white font-semibold">Image Preview</h3>
                  {results && results.detected_elements && results.detected_elements.length > 0 && (
                    <label className="flex items-center text-white text-sm">
                      <input
                        type="checkbox"
                        checked={showBoundingBoxes}
                        onChange={(e) => setShowBoundingBoxes(e.target.checked)}
                        className="mr-2"
                      />
                      Show Bounding Boxes
                    </label>
                  )}
                </div>
                <div className="relative">
                  {uploadedImage === 'PDF' ? (
                    <div className="bg-blue-900/30 border-2 border-blue-500 rounded-lg p-8 text-center">
                      <svg className="w-16 h-16 text-blue-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-white text-lg font-semibold mb-2">PDF Document Uploaded</p>
                      <p className="text-blue-200 text-sm">Processing first page of PDF...</p>
                      {results && (
                        <p className="text-green-300 text-sm mt-2">✓ Processed successfully</p>
                      )}
                    </div>
                  ) : (
                    <>
                      <img
                        src={uploadedImage}
                        alt="Uploaded technical drawing"
                        className="w-full rounded"
                      />
                      {showBoundingBoxes && results && results.detected_elements && (
                        <BoundingBoxOverlay
                          imageWidth={results.image_width}
                          imageHeight={results.image_height}
                          elements={results.detected_elements}
                        />
                      )}
                    </>
                  )}
                </div>
              </div>
            )}

            {isProcessing && (
              <div className="bg-blue-500/20 border border-blue-400 rounded-lg p-4 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
                <p className="text-white">Processing technical drawing...</p>
              </div>
            )}

            {error && (
              <div className="bg-red-500/20 border border-red-400 rounded-lg p-4">
                <p className="text-red-200 font-semibold">Error:</p>
                <p className="text-red-100">{error}</p>
              </div>
            )}
          </div>

          {/* Right Column - Results or Conversational */}
          <div>
            {interfaceMode === 'conversational' ? (
              <ConversationalMode
                imageFile={uploadedFile}
                onResults={setResults}
                isProcessing={isProcessing}
                setIsProcessing={setIsProcessing}
                apiUrl={API_URL}
              />
            ) : (
              results && (
                <ResultsDisplay
                  results={results}
                  mode={selectedMode}
                />
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
