"""
Pydantic models for request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class OCRMode(str, Enum):
    """OCR processing modes"""
    TECHNICAL_DRAWING = "technical_drawing"
    DIMENSIONS_ONLY = "dimensions_only"
    PART_NUMBERS = "part_numbers"
    BOM_EXTRACTION = "bom_extraction"
    PLAIN_OCR = "plain_ocr"
    CUSTOM = "custom"

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

class DetectedElement(BaseModel):
    """Detected element with bounding box"""
    label: str = Field(..., description="Element label/text")
    element_type: str = Field(..., description="Type: dimension, part_number, table, text, image, title")
    bbox: BoundingBox
    confidence: Optional[float] = Field(None, description="Detection confidence if available")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class Dimension(BaseModel):
    """Extracted dimension measurement"""
    value: str = Field(..., description="Dimension value (e.g., '50mm', 'Ø25')")
    unit: Optional[str] = Field(None, description="Measurement unit")
    tolerance: Optional[str] = Field(None, description="Tolerance if specified")
    dimension_type: Optional[str] = Field(None, description="Type: linear, diameter, radius, angular")
    bbox: Optional[BoundingBox] = None

class PartNumber(BaseModel):
    """Extracted part number or item reference"""
    number: str = Field(..., description="Part number")
    description: Optional[str] = Field(None, description="Part description if available")
    bbox: Optional[BoundingBox] = None

class TableRow(BaseModel):
    """Row in extracted table"""
    cells: List[str]
    row_number: int

class ExtractedTable(BaseModel):
    """Extracted table data"""
    headers: Optional[List[str]] = None
    rows: List[TableRow]
    table_type: Optional[str] = Field(None, description="Type: bom, dimension_table, notes, etc.")
    bbox: Optional[BoundingBox] = None

class OCRResponse(BaseModel):
    """Basic OCR response"""
    text: str = Field(..., description="Extracted text")
    markdown: Optional[str] = Field(None, description="Formatted markdown output")
    detected_elements: List[DetectedElement] = Field(default_factory=list)
    image_width: int
    image_height: int
    processing_time: float = Field(..., description="Processing time in seconds")

class TechnicalDrawingResponse(OCRResponse):
    """Extended response for technical drawing analysis"""
    dimensions: List[Dimension] = Field(default_factory=list, description="Extracted dimensions")
    part_numbers: List[PartNumber] = Field(default_factory=list, description="Extracted part numbers")
    tables: List[ExtractedTable] = Field(default_factory=list, description="Extracted tables (BOMs, etc.)")
    annotations: List[str] = Field(default_factory=list, description="General annotations and notes")
    drawing_title: Optional[str] = Field(None, description="Drawing title if detected")
    drawing_number: Optional[str] = Field(None, description="Drawing number if detected")
    revision: Optional[str] = Field(None, description="Revision number if detected")
    scale: Optional[str] = Field(None, description="Drawing scale if detected")

class BatchOCRResponse(BaseModel):
    """Batch processing response"""
    results: List[TechnicalDrawingResponse]
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, str]] = Field(default_factory=list)

class PDFOCRResponse(BaseModel):
    """PDF processing response"""
    pages: List[TechnicalDrawingResponse]
    total_pages: int
    combined_markdown: str
    output_files: Dict[str, str] = Field(default_factory=dict, description="Generated output file paths")
