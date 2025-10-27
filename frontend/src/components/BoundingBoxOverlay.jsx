import { useMemo } from 'react';

const ELEMENT_COLORS = {
  dimension: '#10b981', // green
  part_number: '#3b82f6', // blue
  table: '#f59e0b', // amber
  title: '#8b5cf6', // purple
  view: '#ef4444', // red - for different views (front, side, top, etc.)
  text: '#6b7280', // gray
  image: '#ec4899', // pink
};

function BoundingBoxOverlay({ imageWidth, imageHeight, elements }) {
  const containerRef = useMemo(() => ({ current: null }), []);

  if (!elements || elements.length === 0) return null;

  return (
    <svg
      className="absolute top-0 left-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${imageWidth} ${imageHeight}`}
      preserveAspectRatio="xMidYMid meet"
    >
      {elements.map((element, index) => {
        const { bbox, element_type, label } = element;
        const color = ELEMENT_COLORS[element_type] || ELEMENT_COLORS.text;
        const width = bbox.x2 - bbox.x1;
        const height = bbox.y2 - bbox.y1;

        return (
          <g key={index}>
            {/* Bounding box rectangle */}
            <rect
              x={bbox.x1}
              y={bbox.y1}
              width={width}
              height={height}
              fill="none"
              stroke={color}
              strokeWidth={Math.max(2, imageWidth / 500)}
              strokeDasharray="5,5"
              opacity={0.8}
            />

            {/* Corner markers */}
            <circle cx={bbox.x1} cy={bbox.y1} r={3} fill={color} />
            <circle cx={bbox.x2} cy={bbox.y1} r={3} fill={color} />
            <circle cx={bbox.x1} cy={bbox.y2} r={3} fill={color} />
            <circle cx={bbox.x2} cy={bbox.y2} r={3} fill={color} />

            {/* Label background */}
            <rect
              x={bbox.x1}
              y={bbox.y1 - 20}
              width={label.length * 7 + 10}
              height={18}
              fill={color}
              opacity={0.9}
              rx={3}
            />

            {/* Label text */}
            <text
              x={bbox.x1 + 5}
              y={bbox.y1 - 6}
              fill="white"
              fontSize={Math.max(12, imageWidth / 80)}
              fontFamily="monospace"
              fontWeight="bold"
            >
              {element_type}: {label.substring(0, 30)}{label.length > 30 ? '...' : ''}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default BoundingBoxOverlay;
