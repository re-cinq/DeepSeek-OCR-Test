"""
Vision Service - Qwen3-VL for Technical Drawing Analysis
Replaces DeepSeek-OCR with Qwen3-VL for better conversational reasoning
"""
import os
import time
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image, ImageOps
import torch
import base64
from io import BytesIO

# Use V0 engine for better stability with flash-attn
os.environ['VLLM_USE_V1'] = '0'

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs

from models import (
    TechnicalDrawingResponse,
    DetectedElement,
    BoundingBox,
)


class QwenVisionService:
    """Service class for Qwen3-VL Vision operations"""

    def __init__(self, model_path: str = "Qwen/Qwen3-VL-8B-Thinking"):
        """Initialize the Vision service with vLLM model"""
        self.model = None
        self.model_path = model_path

        # Technical drawing specific system prompts
        self.system_prompt = """You are an expert technical drawing analyst. You specialize in reading and interpreting engineering drawings, CAD diagrams, blueprints, and technical schematics.

Your capabilities include:
- Reading dimensions, tolerances, and measurements
- Identifying part numbers and callouts
- Extracting Bills of Materials (BOMs) and tables
- Understanding engineering symbols and annotations
- Identifying drawing metadata (title, revision, scale, standards)
- Analyzing geometric tolerancing (GD&T)
- Reading material specifications

Always provide precise, structured answers. When asked about specific measurements or data, extract the exact values from the drawing."""

        self._initialize_model()

    def _initialize_model(self):
        """Initialize vLLM AsyncLLMEngine for Qwen3-VL"""
        print(f"Initializing Qwen3-VL model: {self.model_path}")

        # Initialize AsyncLLMEngine
        engine_args = AsyncEngineArgs(
            model=self.model_path,
            trust_remote_code=True,
            tensor_parallel_size=1,  # 30B-A3B MoE runs efficiently on 1 GPU
            gpu_memory_utilization=0.90,
            max_model_len=8192,
            enforce_eager=False,
        )
        self.model = AsyncLLMEngine.from_engine_args(engine_args)

        print("Qwen3-VL AsyncLLMEngine initialized successfully!")

    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.model is not None

    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()

    def load_image(self, image_path: str) -> Tuple[Image.Image, int, int]:
        """Load image and handle EXIF rotation"""
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        return img, width, height

    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 data URL"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    async def process_technical_drawing(
        self,
        image_path: str,
        mode: str = "technical_drawing",
        custom_prompt: Optional[str] = None,
        extract_dimensions: bool = True,
        extract_part_numbers: bool = True,
        extract_tables: bool = True,
        grounding: bool = True,
        base_size: int = 1024,
        image_size: int = 640,
        crop_mode: bool = True
    ) -> TechnicalDrawingResponse:
        """Process a technical drawing image with Qwen3-VL"""
        start_time = time.time()

        # Load image
        img, img_width, img_height = self.load_image(image_path)

        # Build user prompt based on mode or custom prompt
        if custom_prompt:
            # Custom prompt for conversational mode
            # Remove <image> and <|grounding|> tags as Qwen3-VL uses different format
            user_prompt = custom_prompt.replace('<image>', '').replace('<|grounding|>', '').strip()
        else:
            # Predefined prompts based on mode
            prompts = {
                "technical_drawing": "Analyze this technical drawing thoroughly. Extract all dimensions, part numbers, tables (especially BOMs), drawing metadata (title, number, revision, scale), and annotations. Provide a structured markdown output.",
                "dimensions_only": "Extract all dimensions and measurements from this technical drawing including linear dimensions, diameters (Ø), radii (R), angular dimensions, tolerances (±), and units. List them clearly.",
                "part_numbers": "Identify and extract all part numbers, item numbers, and callouts from this technical drawing with their descriptions.",
                "bom_extraction": "Extract all tables from this drawing, especially Bills of Materials (BOMs). Preserve the table structure with headers and all rows in markdown format.",
                "plain_ocr": "Read and transcribe all text visible in this image.",
            }
            user_prompt = prompts.get(mode, prompts["technical_drawing"])

        # Build the conversation with Qwen3-VL format
        # Qwen3-VL uses OpenAI-style messages with image URLs
        image_url = image_to_base64_url(image_path)

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]

        # Build prompt string for vLLM (Qwen3-VL format)
        # For AsyncLLMEngine, we need to format as a single prompt string
        prompt = f"{self.system_prompt}\n\nUser: [Image: {image_path}]\n{user_prompt}\n\nAssistant:"

        # Prepare sampling params
        sampling_params = SamplingParams(
            temperature=0.1,  # Low temp for more factual responses
            top_p=0.9,
            max_tokens=4096,
            skip_special_tokens=True,
        )

        # Generate with AsyncLLMEngine
        request_id = f"request-{int(time.time() * 1000)}"

        # For Qwen3-VL multimodal, we need to pass image in multi_modal_data
        # The format is: {"image": <PIL.Image or image path>}
        request = {
            "prompt": prompt,
            "multi_modal_data": {
                "image": img  # Pass PIL Image directly
            }
        }

        # Stream generate and collect output
        output_text = ""
        async for request_output in self.model.generate(
            request, sampling_params, request_id
        ):
            if request_output.outputs:
                output_text = request_output.outputs[0].text

        print(f"DEBUG: Qwen3-VL output length: {len(output_text)}")
        print(f"DEBUG: First 500 chars: {output_text[:500]}")

        # Note: Qwen3-VL doesn't use grounding tags like DeepSeek-OCR
        # It returns natural language responses
        detected_elements = []  # No bounding boxes from Qwen3-VL in standard mode

        processing_time = time.time() - start_time

        return TechnicalDrawingResponse(
            text=output_text,
            markdown=output_text,
            detected_elements=detected_elements,
            image_width=img_width,
            image_height=img_height,
            processing_time=processing_time,
            dimensions=[],
            part_numbers=[],
            tables=[],
            annotations=[],
            drawing_title=None,
            drawing_number=None,
            revision=None,
            scale=None
        )

    async def process_batch(
        self,
        image_paths: List[str],
        mode: str = "technical_drawing",
        grounding: bool = True
    ) -> List[TechnicalDrawingResponse]:
        """Process multiple images in batch"""
        results = []

        for image_path in image_paths:
            try:
                result = await self.process_technical_drawing(
                    image_path=image_path,
                    mode=mode,
                    grounding=grounding
                )
                results.append(result)
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue

        return results

    async def process_pdf(
        self,
        pdf_path: str,
        mode: str = "technical_drawing",
        dpi: int = 144,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """Process PDF document"""
        import fitz  # PyMuPDF

        # Convert PDF to images
        pdf_doc = fitz.open(pdf_path)
        temp_image_paths = []

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))

            temp_path = f"/tmp/qwen_page_{page_num}.png"
            pix.save(temp_path)
            temp_image_paths.append(temp_path)

        pdf_doc.close()

        # Process all pages
        results = await self.process_batch(temp_image_paths, mode=mode)

        # Combine markdown
        combined_md = "\n\n---\n\n".join([r.markdown for r in results])

        # Cleanup
        for path in temp_image_paths:
            if os.path.exists(path):
                os.remove(path)

        return {
            "pages": results,
            "total_pages": len(results),
            "combined_markdown": combined_md
        }

    def cleanup(self):
        """Cleanup resources"""
        pass


def image_to_base64_url(image_path: str) -> str:
    """Convert image file to base64 data URL"""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
