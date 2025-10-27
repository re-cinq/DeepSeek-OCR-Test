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

# V1 engine is auto-selected for Qwen3-VL, accept it and disable flash-attn
os.environ['VLLM_USE_V1'] = '1'

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs

from models import (
    TechnicalDrawingResponse,
    DetectedElement,
    BoundingBox,
)


class QwenVisionService:
    """Service class for Qwen3-VL Vision operations"""

    def __init__(self, model_path: str = "Qwen/Qwen3-VL-8B-Instruct"):
        """Initialize the Vision service with vLLM model"""
        self.model = None
        self.processor = None
        self.model_path = model_path

        # Short, concise system prompt to avoid exceeding token limits
        self.system_prompt = """You are a technical drawing analyst. Be extremely concise. Give direct answers only. For measurements: just state the value and unit (e.g., "90 mm"). No reasoning, no explanations."""

        self._initialize_model()
        self._initialize_processor()

    def _initialize_model(self):
        """Initialize vLLM AsyncLLMEngine for Qwen3-VL"""
        print(f"Initializing Qwen3-VL model: {self.model_path}")

        # Try with flash-attn first for better performance
        try:
            print("Attempting to use flash-attn for optimal performance...")
            engine_args = AsyncEngineArgs(
                model=self.model_path,
                trust_remote_code=True,
                tensor_parallel_size=1,  # 8B model runs on 1 GPU
                gpu_memory_utilization=0.90,
                max_model_len=8192,
                enforce_eager=False,  # Try with CUDA graphs and flash-attn
            )
            self.model = AsyncLLMEngine.from_engine_args(engine_args)
            print("✓ Qwen3-VL AsyncLLMEngine initialized with flash-attn!")

        except Exception as e:
            print(f"⚠️  flash-attn failed ({str(e)[:100]}), falling back to eager mode...")
            print("Note: Performance will be ~20-30% slower without flash-attn")
            print("Run ./fix_flash_attn.sh to fix flash-attn installation")

            # Fallback to eager mode
            engine_args = AsyncEngineArgs(
                model=self.model_path,
                trust_remote_code=True,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.90,
                max_model_len=8192,
                enforce_eager=True,  # Disable flash-attn as fallback
            )
            self.model = AsyncLLMEngine.from_engine_args(engine_args)
            print("✓ Qwen3-VL AsyncLLMEngine initialized in eager mode (slower)")

    def _initialize_processor(self):
        """Initialize the AutoProcessor for Qwen3-VL"""
        from transformers import AutoProcessor
        print(f"Loading processor for {self.model_path}")
        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        print("Processor initialized successfully!")

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

    def parse_grounding_json(self, text: str, img_width: int, img_height: int) -> List[DetectedElement]:
        """Parse JSON bbox format from Qwen3-VL grounding output"""
        import json

        elements = []
        try:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array directly
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return elements

            # Parse JSON
            bbox_data = json.loads(json_str)

            if not isinstance(bbox_data, list):
                bbox_data = [bbox_data]

            # Convert to DetectedElement objects
            for item in bbox_data:
                if 'bbox_2d' not in item:
                    continue

                x1, y1, x2, y2 = item['bbox_2d']
                label = item.get('label', 'unknown')
                sub_label = item.get('sub_label', '')

                # Classify element type based on label
                element_type = self._classify_element_type(label)

                # Create full label
                full_label = f"{label} {sub_label}".strip() if sub_label else label

                bbox = BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
                elements.append(DetectedElement(
                    label=full_label,
                    element_type=element_type,
                    bbox=bbox
                ))

            print(f"DEBUG: Parsed {len(elements)} grounding elements from JSON")

        except Exception as e:
            print(f"ERROR: Failed to parse grounding JSON: {e}")
            print(f"DEBUG: Text snippet: {text[:500]}")

        return elements

    def _classify_element_type(self, label: str) -> str:
        """Classify element type based on label for color coding"""
        label_lower = label.lower()

        # View types
        if any(view in label_lower for view in ['view', 'section', 'detail', 'isometric', 'perspective']):
            return 'view'

        # Dimensions
        if any(dim in label_lower for dim in ['dimension', 'measurement', 'ø', 'diameter', 'radius', 'r', '±']):
            return 'dimension'

        # Part numbers
        if any(part in label_lower for part in ['part', 'item', 'pos', 'callout']):
            return 'part_number'

        # Tables
        if any(table in label_lower for table in ['table', 'bom', 'bill of material']):
            return 'table'

        # Title blocks
        if any(title in label_lower for title in ['title', 'drawing number', 'revision']):
            return 'title'

        return 'text'

    def _strip_reasoning(self, text: str) -> str:
        """
        Strip internal reasoning from Qwen3-VL-8B-Thinking model output.
        The Thinking model outputs reasoning followed by final answer.

        Common patterns:
        - "Got it, let's look at..." followed by answer
        - Long reasoning paragraphs followed by structured answer
        - Multiple reasoning steps before final conclusion
        """
        if not text:
            return text

        # Split by common section markers
        lines = text.split('\n')

        # Strategy 1: Look for markdown headers or structured sections
        # Often the final answer starts with a header or structured format
        answer_start = -1
        for i, line in enumerate(lines):
            # Check for markdown headers (## or **bold**)
            if line.strip().startswith('##') or line.strip().startswith('**'):
                answer_start = i
                break
            # Check for numbered lists at start of line (structured answers)
            if re.match(r'^\d+\.', line.strip()) and i > 5:
                answer_start = i
                break
            # Check for bullet points
            if line.strip().startswith('- ') and i > 5:
                answer_start = i
                break

        if answer_start > 0:
            return '\n'.join(lines[answer_start:]).strip()

        # Strategy 2: Look for common reasoning patterns to skip
        reasoning_indicators = [
            "Got it, let's",
            "Let me check",
            "Let me look",
            "First, check",
            "Looking at",
            "Wait,",
            "The user wants",
            "The question is",
        ]

        # Find the last reasoning indicator
        last_reasoning_idx = -1
        for i, line in enumerate(lines):
            if any(indicator in line for indicator in reasoning_indicators):
                last_reasoning_idx = i

        # If we found reasoning, skip past it
        if last_reasoning_idx > 0 and last_reasoning_idx < len(lines) - 3:
            # Look for the answer after the last reasoning
            # Usually there's a blank line or structured text
            for i in range(last_reasoning_idx + 1, len(lines)):
                line = lines[i].strip()
                if line and not any(indicator in line for indicator in reasoning_indicators):
                    # This looks like the start of the answer
                    return '\n'.join(lines[i:]).strip()

        # Strategy 3: If text is very long (>500 chars), likely has reasoning
        # Take the last significant section
        if len(text) > 500:
            # Split on double newlines (paragraph breaks)
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 2:
                # Return last 1-2 paragraphs (likely the answer)
                return '\n\n'.join(paragraphs[-2:]).strip()

        # If no reasoning detected, return original
        return text

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
                "technical_drawing": "Analyze this technical drawing thoroughly. Extract all dimensions, part numbers, tables (especially BOMs), drawing metadata (title, number, revision, scale), and annotations. Provide a structured markdown output." if not grounding else "Analyze this technical drawing thoroughly. Detect and locate all important elements including dimensions, part numbers, tables, and annotations. Return their locations in JSON format: [{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"element description\"}]",
                "dimensions_only": "Extract all dimensions and measurements from this technical drawing including linear dimensions, diameters (Ø), radii (R), angular dimensions, tolerances (±), and units. List them clearly.",
                "part_numbers": "Identify and extract all part numbers, item numbers, and callouts from this technical drawing with their descriptions.",
                "bom_extraction": "Extract all tables from this drawing, especially Bills of Materials (BOMs). Preserve the table structure with headers and all rows in markdown format.",
                "plain_ocr": "Read and transcribe all text visible in this image.",
                "view_detection": "Detect all views in this technical drawing including: front view, side view, top view, section views (A-A, B-B, etc.), detail views, isometric/3D views, and any auxiliary views. Return their locations and labels in JSON format: [{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"view name\", \"sub_label\": \"additional info\"}]. Be precise with the bounding box coordinates.",
            }
            user_prompt = prompts.get(mode, prompts["technical_drawing"])

        # Build messages in Qwen3-VL format
        # Qwen3-VL uses OpenAI-style messages with image content type
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path  # Can be path, URL, or PIL Image
                    },
                    {
                        "type": "text",
                        "text": f"{self.system_prompt}\n\n{user_prompt}"
                    }
                ]
            }
        ]

        # Apply chat template to format the prompt
        text_prompt = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Process vision inputs using qwen_vl_utils
        from qwen_vl_utils import process_vision_info

        image_inputs, video_inputs, video_kwargs = process_vision_info(
            messages,
            image_patch_size=self.processor.image_processor.patch_size,
            return_video_kwargs=True,
            return_video_metadata=True
        )

        # Build multi_modal_data dict
        mm_data = {}
        if image_inputs is not None:
            mm_data['image'] = image_inputs
        if video_inputs is not None:
            mm_data['video'] = video_inputs

        # Prepare sampling params
        sampling_params = SamplingParams(
            temperature=0.0,  # Zero temp for most concise, deterministic responses
            top_p=0.9,
            max_tokens=512,  # Reduced from 4096 to encourage shorter answers
            skip_special_tokens=True,
        )

        # Generate with AsyncLLMEngine
        request_id = f"request-{int(time.time() * 1000)}"

        # Prepare request with proper format
        request = {
            "prompt": text_prompt,
            "multi_modal_data": mm_data,
            "mm_processor_kwargs": video_kwargs
        }

        # Stream generate and collect output
        output_text = ""
        async for request_output in self.model.generate(
            request, sampling_params, request_id
        ):
            if request_output.outputs:
                output_text = request_output.outputs[0].text

        print(f"DEBUG: Qwen3-VL raw output length: {len(output_text)}")
        print(f"DEBUG: First 500 chars: {output_text[:500]}")

        # Strip reasoning from Qwen3-VL-8B-Thinking model
        # The "Thinking" model outputs internal reasoning followed by final answer
        cleaned_text = self._strip_reasoning(output_text)
        print(f"DEBUG: After stripping reasoning: {len(cleaned_text)} chars")

        # Parse detections if grounding is enabled
        detected_elements = []
        if grounding:
            detected_elements = self.parse_grounding_json(output_text, img_width, img_height)
            print(f"DEBUG: Parsed {len(detected_elements)} grounded elements")

        processing_time = time.time() - start_time

        return TechnicalDrawingResponse(
            text=cleaned_text,
            markdown=cleaned_text,
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
