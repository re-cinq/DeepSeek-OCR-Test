import { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import BoundingBoxOverlay from './components/BoundingBoxOverlay';
import ConversationalMode from './components/ConversationalMode';

// Use environment variable or default to same host on port 8000
const API_URL = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);

  const handleImageUpload = (file) => {
    // Store the file for conversational mode
    setUploadedFile(file);

    // For images, create object URL for preview
    if (file.type.startsWith('image/')) {
      setUploadedImage(URL.createObjectURL(file));
    } else if (file.type === 'application/pdf') {
      setUploadedImage('PDF');  // Special marker for PDF files
    }
    setResults(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            💬 re:cinq - Technische Zeichnungen Chat
          </h1>
          <p className="text-blue-200 text-lg">
            Stellen Sie Fragen zu Ihren technischen Zeichnungen in natürlicher Sprache
          </p>
          <p className="text-blue-300 text-sm mt-1">
            Angetrieben von DeepSeek-OCR mit vLLM
          </p>
        </div>

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
                  <h3 className="text-white font-semibold">Bildvorschau</h3>
                  {results && results.detected_elements && results.detected_elements.length > 0 && (
                    <label className="flex items-center text-white text-sm">
                      <input
                        type="checkbox"
                        checked={showBoundingBoxes}
                        onChange={(e) => setShowBoundingBoxes(e.target.checked)}
                        className="mr-2"
                      />
                      Begrenzungsrahmen anzeigen
                    </label>
                  )}
                </div>
                <div className="relative">
                  {uploadedImage === 'PDF' ? (
                    <div className="bg-blue-900/30 border-2 border-blue-500 rounded-lg p-8 text-center">
                      <svg className="w-16 h-16 text-blue-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-white text-lg font-semibold mb-2">PDF-Dokument hochgeladen</p>
                      <p className="text-blue-200 text-sm">Verarbeite erste Seite der PDF...</p>
                      {results && (
                        <p className="text-green-300 text-sm mt-2">✓ Erfolgreich verarbeitet</p>
                      )}
                    </div>
                  ) : (
                    <>
                      <img
                        src={uploadedImage}
                        alt="Hochgeladene technische Zeichnung"
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

          </div>

          {/* Right Column - Conversational Mode */}
          <div>
            <ConversationalMode
              imageFile={uploadedFile}
              onResults={setResults}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              apiUrl={API_URL}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
