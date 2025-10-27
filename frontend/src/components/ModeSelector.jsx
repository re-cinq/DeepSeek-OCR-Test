import { useState, useEffect } from 'react';

const MODES = [
  {
    id: 'technical_drawing',
    name: 'Technical Drawing',
    icon: '📐',
    description: 'Full analysis: dimensions, parts, BOMs, annotations'
  },
  {
    id: 'dimensions_only',
    name: 'Dimensions',
    icon: '📏',
    description: 'Extract measurements and tolerances'
  },
  {
    id: 'part_numbers',
    name: 'Part Numbers',
    icon: '🔢',
    description: 'Find part numbers and callouts'
  },
  {
    id: 'bom_extraction',
    name: 'BOM',
    icon: '📋',
    description: 'Extract bills of materials'
  },
  {
    id: 'plain_ocr',
    name: 'Plain OCR',
    icon: '📄',
    description: 'Simple text extraction'
  }
];

function ModeSelector({ selectedMode, onModeChange, disabled }) {
  return (
    <div className="bg-white/10 backdrop-blur-md rounded-lg p-4">
      <h3 className="text-white font-semibold mb-3">Analysis Mode</h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {MODES.map((mode) => (
          <button
            key={mode.id}
            onClick={() => onModeChange(mode.id)}
            disabled={disabled}
            className={`
              p-3 rounded-lg text-left transition-all duration-200
              ${selectedMode === mode.id
                ? 'bg-blue-500 text-white shadow-lg scale-105'
                : 'bg-white/5 text-blue-100 hover:bg-white/10'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-1">{mode.icon}</div>
            <div className="font-semibold text-sm">{mode.name}</div>
            <div className="text-xs opacity-75 mt-1">{mode.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default ModeSelector;
