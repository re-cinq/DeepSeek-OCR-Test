import { useState, useRef } from 'react';

function ImageUpload({ onImageUpload, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        onImageUpload(file);
      } else {
        alert('Please upload an image file');
      }
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onImageUpload(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragging
          ? 'border-blue-400 bg-blue-500/20 scale-105'
          : 'border-blue-300/50 bg-white/5 hover:bg-white/10'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileSelect}
        disabled={disabled}
      />

      <div className="flex flex-col items-center">
        <svg
          className="w-16 h-16 text-blue-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        <p className="text-white text-lg font-semibold mb-2">
          {isDragging ? 'Drop your image here' : 'Upload Technical Drawing'}
        </p>

        <p className="text-blue-200 text-sm">
          Drag and drop or click to select
        </p>

        <p className="text-blue-300 text-xs mt-2">
          Supports: JPG, PNG, TIFF (CAD drawings, blueprints, engineering diagrams)
        </p>
      </div>
    </div>
  );
}

export default ImageUpload;
