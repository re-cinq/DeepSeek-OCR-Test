import { useState } from 'react';

function ResultsDisplay({ results, mode }) {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'dimensions', label: 'Dimensions', icon: '📏', count: results.dimensions?.length },
    { id: 'parts', label: 'Part Numbers', icon: '🔢', count: results.part_numbers?.length },
    { id: 'tables', label: 'Tables', icon: '📋', count: results.tables?.length },
    { id: 'text', label: 'Full Text', icon: '📄' },
  ];

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 space-y-4">
      {/* Stats Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-blue-500/20 rounded-lg p-3 text-center">
          <div className="text-blue-200 text-sm">Elements</div>
          <div className="text-white text-2xl font-bold">{results.detected_elements?.length || 0}</div>
        </div>
        <div className="bg-green-500/20 rounded-lg p-3 text-center">
          <div className="text-green-200 text-sm">Dimensions</div>
          <div className="text-white text-2xl font-bold">{results.dimensions?.length || 0}</div>
        </div>
        <div className="bg-amber-500/20 rounded-lg p-3 text-center">
          <div className="text-amber-200 text-sm">Parts</div>
          <div className="text-white text-2xl font-bold">{results.part_numbers?.length || 0}</div>
        </div>
        <div className="bg-purple-500/20 rounded-lg p-3 text-center">
          <div className="text-purple-200 text-sm">Time</div>
          <div className="text-white text-2xl font-bold">{results.processing_time?.toFixed(1)}s</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-white/20 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              px-4 py-2 rounded-t-lg transition-all flex items-center gap-2
              ${activeTab === tab.id
                ? 'bg-blue-500 text-white'
                : 'bg-white/5 text-blue-200 hover:bg-white/10'
              }
            `}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="max-h-[600px] overflow-y-auto">
        {activeTab === 'overview' && (
          <div className="space-y-4 text-white">
            {results.drawing_title && (
              <div>
                <div className="text-blue-200 text-sm font-semibold">Title</div>
                <div className="text-lg">{results.drawing_title}</div>
              </div>
            )}
            {results.drawing_number && (
              <div>
                <div className="text-blue-200 text-sm font-semibold">Drawing Number</div>
                <div>{results.drawing_number}</div>
              </div>
            )}
            {results.revision && (
              <div>
                <div className="text-blue-200 text-sm font-semibold">Revision</div>
                <div>{results.revision}</div>
              </div>
            )}
            {results.scale && (
              <div>
                <div className="text-blue-200 text-sm font-semibold">Scale</div>
                <div>{results.scale}</div>
              </div>
            )}
            <div>
              <div className="text-blue-200 text-sm font-semibold mb-2">Detected Elements</div>
              <div className="space-y-1">
                {Object.entries(
                  results.detected_elements?.reduce((acc, el) => {
                    acc[el.element_type] = (acc[el.element_type] || 0) + 1;
                    return acc;
                  }, {}) || {}
                ).map(([type, count]) => (
                  <div key={type} className="flex justify-between bg-white/5 p-2 rounded">
                    <span className="capitalize">{type}</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'dimensions' && (
          <div className="space-y-2">
            {results.dimensions && results.dimensions.length > 0 ? (
              results.dimensions.map((dim, index) => (
                <div key={index} className="bg-green-500/10 border border-green-500/30 rounded p-3">
                  <div className="text-white font-semibold">{dim.value}</div>
                  <div className="text-green-200 text-sm mt-1">
                    Type: {dim.dimension_type || 'Unknown'}
                    {dim.unit && ` • Unit: ${dim.unit}`}
                    {dim.tolerance && ` • Tolerance: ${dim.tolerance}`}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-blue-200 text-center py-8">No dimensions detected</div>
            )}
          </div>
        )}

        {activeTab === 'parts' && (
          <div className="space-y-2">
            {results.part_numbers && results.part_numbers.length > 0 ? (
              results.part_numbers.map((part, index) => (
                <div key={index} className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
                  <div className="text-white font-mono font-semibold">{part.number}</div>
                  {part.description && (
                    <div className="text-blue-200 text-sm mt-1">{part.description}</div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-blue-200 text-center py-8">No part numbers detected</div>
            )}
          </div>
        )}

        {activeTab === 'tables' && (
          <div className="space-y-4">
            {results.tables && results.tables.length > 0 ? (
              results.tables.map((table, index) => (
                <div key={index} className="bg-amber-500/10 border border-amber-500/30 rounded p-3 overflow-x-auto">
                  {table.table_type && (
                    <div className="text-amber-200 text-sm font-semibold mb-2 uppercase">
                      {table.table_type}
                    </div>
                  )}
                  <table className="w-full text-white text-sm">
                    {table.headers && (
                      <thead>
                        <tr className="border-b border-white/20">
                          {table.headers.map((header, i) => (
                            <th key={i} className="text-left p-2 font-semibold">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                    )}
                    <tbody>
                      {table.rows.map((row, i) => (
                        <tr key={i} className="border-b border-white/10">
                          {row.cells.map((cell, j) => (
                            <td key={j} className="p-2">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))
            ) : (
              <div className="text-blue-200 text-center py-8">No tables detected</div>
            )}
          </div>
        )}

        {activeTab === 'text' && (
          <div className="bg-white/5 rounded p-4">
            <pre className="text-white text-sm whitespace-pre-wrap font-mono">
              {results.markdown || results.text}
            </pre>
          </div>
        )}
      </div>

      {/* Download Button */}
      <div className="pt-4 border-t border-white/20">
        <button
          onClick={() => {
            const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ocr-results.json';
            a.click();
          }}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Download Results (JSON)
        </button>
      </div>
    </div>
  );
}

export default ResultsDisplay;
