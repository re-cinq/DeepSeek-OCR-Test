"""
FastAPI Backend for Qwen3-VL Technical Drawing Analysis
Uses Qwen3-VL for superior reasoning and conversational QA
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import uvicorn
import logging
from pathlib import Path
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta

from qwen_vision_service import QwenVisionService
from models import TechnicalDrawingResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session storage for uploaded images
# Format: {session_id: {"image_path": str, "uploaded_at": datetime, "metadata": dict}}
image_sessions: Dict[str, Dict] = {}
SESSION_EXPIRY_HOURS = 24

def cleanup_expired_sessions():
    """Remove expired image sessions"""
    now = datetime.now()
    expired = [
        sid for sid, data in image_sessions.items()
        if now - data["uploaded_at"] > timedelta(hours=SESSION_EXPIRY_HOURS)
    ]
    for sid in expired:
        session_data = image_sessions.pop(sid)
        if Path(session_data["image_path"]).exists():
            Path(session_data["image_path"]).unlink()
        logger.info(f"Cleaned up expired session: {sid}")

# Initialize FastAPI app
app = FastAPI(
    title="Qwen3-VL Technical Drawing API",
    description="Vision-Language API specialized for technical drawings with conversational QA capabilities",
    version="2.0.0"
)

# CORS configuration - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. For production, specify exact origins.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vision service (singleton)
vision_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize Vision service on startup"""
    global vision_service
    logger.info("Initializing Qwen3-VL Vision service with vLLM...")
    try:
        vision_service = QwenVisionService()
        logger.info("✓ Vision service initialized successfully")
        logger.info(f"✓ GPU available: {vision_service.gpu_available()}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Vision service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Vision service...")
    if vision_service:
        vision_service.cleanup()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Qwen3-VL Technical Drawing API",
        "version": "2.0.0",
        "model": "Qwen3-VL-30B-A3B-Instruct",
        "model_ready": vision_service is not None and vision_service.is_ready()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": vision_service is not None and vision_service.is_ready(),
        "gpu_available": vision_service.gpu_available() if vision_service else False
    }

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...)
):
    """
    Upload and store an image for conversational chat.
    Returns a session_id that can be used for subsequent queries.
    """
    if not vision_service:
        raise HTTPException(status_code=503, detail="Vision service not initialized")

    # Cleanup expired sessions periodically
    cleanup_expired_sessions()

    # Validate file type
    if not file.content_type or not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail=f"File must be an image or PDF (got {file.content_type})")

    # Create session
    session_id = str(uuid.uuid4())

    # Create persistent temp directory for this session
    session_dir = Path(tempfile.gettempdir()) / "deepseek_ocr_sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    image_path = session_dir / file.filename

    try:
        # Save uploaded file
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Uploaded {file.filename} - Session: {session_id}")

        # If PDF, convert first page to image
        if file.content_type == "application/pdf":
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(str(image_path))
            if len(pdf_doc) == 0:
                raise HTTPException(status_code=400, detail="PDF file is empty")

            # Convert first page to image
            page = pdf_doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better quality
            img_path = str(image_path).replace('.pdf', '_page0.png')
            pix.save(img_path)
            pdf_doc.close()

            logger.info(f"Converted PDF first page to image: {img_path}")
            process_path = img_path
        else:
            process_path = str(image_path)

        # Store session data
        image_sessions[session_id] = {
            "image_path": process_path,
            "original_filename": file.filename,
            "uploaded_at": datetime.now(),
            "content_type": file.content_type
        }

        return {
            "session_id": session_id,
            "filename": file.filename,
            "status": "ready",
            "message": "Bild erfolgreich hochgeladen. Sie können nun Fragen stellen."
        }

    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        # Cleanup on error
        if session_dir.exists():
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_image(
    session_id: str = Form(...),
    question: str = Form(...),
    use_grounding: bool = Form(True),
    base_size: int = Form(1024),
    image_size: int = Form(640),
    crop_mode: bool = Form(True)
):
    """
    Ask a question about a previously uploaded image.
    Requires a valid session_id from /api/upload
    """
    if not vision_service:
        raise HTTPException(status_code=503, detail="Vision service not initialized")

    # Check if session exists
    if session_id not in image_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload an image first.")

    session_data = image_sessions[session_id]
    image_path = session_data["image_path"]

    # Check if image file still exists
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Image file no longer exists. Please re-upload.")

    try:
        logger.info(f"Chat query for session {session_id}: {question}")

        # Build prompt with or without grounding
        custom_prompt = f"<image>\n{'<|grounding|>' if use_grounding else ''}{question}"

        # Process with OCR service
        result = await vision_service.process_technical_drawing(
            image_path=image_path,
            mode="custom",
            custom_prompt=custom_prompt,
            grounding=use_grounding,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode
        )

        logger.info(f"✓ Chat response in {result.processing_time:.2f}s - {len(result.detected_elements)} elements")

        return result

    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its associated image"""
    if session_id not in image_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = image_sessions.pop(session_id)

    # Delete the session directory
    session_dir = Path(session_data["image_path"]).parent
    if session_dir.exists():
        shutil.rmtree(session_dir)

    logger.info(f"Deleted session: {session_id}")

    return {"status": "deleted", "session_id": session_id}

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
    if not vision_service:
        raise HTTPException(status_code=503, detail="Vision service not initialized")

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
        result = await vision_service.process_technical_drawing(
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
    if not vision_service:
        raise HTTPException(status_code=503, detail="Vision service not initialized")

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
        results = await vision_service.process_batch(
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
    if not vision_service:
        raise HTTPException(status_code=503, detail="Vision service not initialized")

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
        result = await vision_service.process_pdf(
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
