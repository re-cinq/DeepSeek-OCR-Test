import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set worker path for pdfjs
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

function PdfPreview({ file }) {
  const [numPages, setNumPages] = useState(null);
  const [pageWidth, setPageWidth] = useState(0);

  useEffect(() => {
    // Calculate width based on container
    const updateWidth = () => {
      const container = document.getElementById('pdf-container');
      if (container) {
        setPageWidth(container.offsetWidth - 40); // Subtract padding
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  return (
    <div id="pdf-container" className="bg-white/5 rounded-lg p-4">
      <div className="text-blue-200 text-sm mb-2">
        PDF-Vorschau (Seite 1 {numPages && `von ${numPages}`})
      </div>
      <Document
        file={file}
        onLoadSuccess={onDocumentLoadSuccess}
        loading={
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <span className="ml-3 text-white">Lade PDF...</span>
          </div>
        }
        error={
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200">
            Fehler beim Laden der PDF-Datei
          </div>
        }
      >
        <Page
          pageNumber={1}
          width={pageWidth}
          renderTextLayer={false}
          renderAnnotationLayer={false}
          className="shadow-lg"
        />
      </Document>
    </div>
  );
}

export default PdfPreview;
