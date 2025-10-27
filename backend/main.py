"""
FastAPI Backend for DeepSeek-OCR Technical Drawing Analysis
Uses existing vLLM installation - no Docker required
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import uvicorn
import logging
from pathlib import Path
import shutil
import tempfile

from ocr_service import DeepSeekOCRService
from models import TechnicalDrawingResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DeepSeek-OCR Technical Drawing API",
    description="OCR API specialized for technical drawings, machine parts, and engineering documentation",
    version="1.0.0"
)

# CORS configuration - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. For production, specify exact origins.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR service (singleton)
ocr_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize OCR service on startup"""
    global ocr_service
    logger.info("Initializing DeepSeek-OCR service with vLLM...")
    try:
        ocr_service = DeepSeekOCRService()
        logger.info("✓ OCR service initialized successfully")
        logger.info(f"✓ GPU available: {ocr_service.gpu_available()}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize OCR service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down OCR service...")
    if ocr_service:
        ocr_service.cleanup()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "DeepSeek-OCR Technical Drawing API",
        "version": "1.0.0",
        "model_ready": ocr_service is not None and ocr_service.is_ready()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": ocr_service is not None and ocr_service.is_ready(),
        "gpu_available": ocr_service.gpu_available() if ocr_service else False
    }

@app.post("/api/ocr", response_model=TechnicalDrawingResponse)
async def process_technical_drawing(
    file: UploadFile = File(...),
    mode: str = Form("technical_drawing"),
    custom_prompt: Optional[str] = Form(None),
    extract_dimensions: bool = Form(True),
    extract_part_numbers: bool = Form(True),
    extract_tables: bool = Form(True),
    grounding: bool = Form(True),
    base_size: int = Form(1024),
    image_size: int = Form(640),
    crop_mode: bool = Form(True)
):
    """
    Process technical drawing for OCR

    Modes:
    - technical_drawing: Full analysis (dimensions, parts, tables, annotations)
    - dimensions_only: Extract only measurements and tolerances
    - part_numbers: Extract part numbers and callouts
    - bom_extraction: Extract bill of materials tables
    - plain_ocr: Simple text extraction
    - custom: Use custom_prompt
    """
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR service not initialized")

    # Validate file type
    if not file.content_type or not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail=f"File must be an image or PDF (got {file.content_type})")

    # Create temp file for processing
    temp_dir = tempfile.mkdtemp()
    temp_input_path = Path(temp_dir) / file.filename

    try:
        # Save uploaded file
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing {file.filename} in mode: {mode}")

        # If PDF, convert first page to image
        if file.content_type == "application/pdf":
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(str(temp_input_path))
            if len(pdf_doc) == 0:
                raise HTTPException(status_code=400, detail="PDF file is empty")

            # Convert first page to image
            page = pdf_doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better quality
            img_path = str(temp_input_path).replace('.pdf', '_page0.png')
            pix.save(img_path)
            pdf_doc.close()

            logger.info(f"Converted PDF first page to image: {img_path}")
            process_path = img_path
        else:
            process_path = str(temp_input_path)

        # Process image
        result = await ocr_service.process_technical_drawing(
            image_path=process_path,
            mode=mode,
            custom_prompt=custom_prompt,
            extract_dimensions=extract_dimensions,
            extract_part_numbers=extract_part_numbers,
            extract_tables=extract_tables,
            grounding=grounding,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode
        )

        logger.info(f"✓ Processed in {result.processing_time:.2f}s - Found {len(result.detected_elements)} elements")

        return result

    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp files
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

@app.post("/api/ocr/batch")
async def process_batch(
    files: List[UploadFile] = File(...),
    mode: str = Form("technical_drawing"),
    grounding: bool = Form(True)
):
    """Process multiple technical drawings in batch"""
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR service not initialized")

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per batch")

    results = []
    temp_dir = tempfile.mkdtemp()

    try:
        # Save all files
        file_paths = []
        for file in files:
            if not file.content_type.startswith("image/"):
                continue
            temp_path = Path(temp_dir) / file.filename
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(str(temp_path))

        logger.info(f"Batch processing {len(file_paths)} images...")

        # Process batch
        results = await ocr_service.process_batch(
            image_paths=file_paths,
            mode=mode,
            grounding=grounding
        )

        return {
            "results": results,
            "total": len(results),
            "successful": len(results),
            "failed": len(file_paths) - len(results)
        }

    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

@app.post("/api/ocr/pdf")
async def process_pdf(
    file: UploadFile = File(...),
    mode: str = Form("technical_drawing"),
    dpi: int = Form(144)
):
    """Process multi-page PDF technical documentation"""
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR service not initialized")

    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    temp_dir = tempfile.mkdtemp()
    temp_pdf_path = Path(temp_dir) / file.filename

    try:
        # Save PDF
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing PDF: {file.filename}")

        # Process PDF
        result = await ocr_service.process_pdf(
            pdf_path=str(temp_pdf_path),
            mode=mode,
            dpi=dpi,
            output_dir=temp_dir
        )

        return result

    except Exception as e:
        logger.error(f"PDF processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

@app.get("/api/modes")
async def get_available_modes():
    """Get available OCR processing modes"""
    return {
        "modes": [
            {
                "id": "technical_drawing",
                "name": "Technical Drawing Analysis",
                "description": "Complete analysis: dimensions, part numbers, tables, annotations"
            },
            {
                "id": "dimensions_only",
                "name": "Dimension Extraction",
                "description": "Extract measurements, tolerances, and geometric dimensions"
            },
            {
                "id": "part_numbers",
                "name": "Part Number Detection",
                "description": "Identify part numbers, item numbers, and callouts"
            },
            {
                "id": "bom_extraction",
                "name": "BOM Extraction",
                "description": "Extract bill of materials tables"
            },
            {
                "id": "plain_ocr",
                "name": "Plain OCR",
                "description": "Simple text extraction without analysis"
            },
            {
                "id": "custom",
                "name": "Custom Prompt",
                "description": "Use custom analysis prompt"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to keep model in memory
        log_level="info"
    )
