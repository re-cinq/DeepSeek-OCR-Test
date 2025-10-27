"""
OCR Service - Wraps existing DeepSeek-OCR vLLM scripts
"""
import sys
import os
from pathlib import Path
import time
import re
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image
import torch

# Set environment variables (required for vLLM)
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"
os.environ['VLLM_USE_V1'] = '0'

# Add DeepSeek-OCR vLLM directory to path
DEEPSEEK_VLLM_DIR = Path(__file__).parent.parent / "DeepSeek-OCR-master" / "DeepSeek-OCR-vllm"
sys.path.insert(0, str(DEEPSEEK_VLLM_DIR))

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM
from process.image_process import DeepseekOCRProcessor
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
import config

# Register the custom DeepSeek-OCR model with vLLM
ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

from models import (
    TechnicalDrawingResponse,
    DetectedElement,
    BoundingBox,
    Dimension,
    PartNumber,
    ExtractedTable,
    TableRow
)

class DeepSeekOCRService:
    """Service class for DeepSeek OCR operations"""

    def __init__(self):
        """Initialize the OCR service with vLLM model"""
        self.model = None
        self.processor = None
        self.tokenizer = None

        # Load config from module
        self.model_path = config.MODEL_PATH
        self.base_size = config.BASE_SIZE
        self.image_size = config.IMAGE_SIZE
        self.crop_mode = config.CROP_MODE

        # Technical drawing specific prompts
        # NOTE: <|grounding|> tag is REQUIRED for bounding box annotations
        self.prompts = {
            "technical_drawing": """<image>
<|grounding|>Analyze this technical drawing or engineering diagram. Extract and identify all dimensions, part numbers, tables (especially BOMs), drawing metadata (title, number, revision, scale), and annotations. Convert the document to structured markdown.""",

            "dimensions_only": """<image>
<|grounding|>Extract all dimensions and measurements from this technical drawing including linear dimensions, diameters (Ø), radii (R), angular dimensions, tolerances (±), and units. Convert to markdown.""",

            "part_numbers": """<image>
<|grounding|>Identify and extract all part numbers, item numbers, and callouts from this technical drawing with their descriptions. Convert to markdown.""",

            "bom_extraction": """<image>
<|grounding|>Extract all tables from this drawing, especially Bills of Materials (BOMs). Preserve the table structure with headers and all rows. Convert to markdown.""",

            "plain_ocr": "<image>\n<|grounding|>Convert the document to markdown.",
        }

        self._initialize_model()

    def _initialize_model(self):
        """Initialize vLLM model and processor"""
        print("Initializing DeepSeek-OCR model with AsyncLLMEngine...")

        # Initialize processor
        self.processor = DeepseekOCRProcessor()
        self.tokenizer = config.TOKENIZER

        # Initialize AsyncLLMEngine with same params as original script
        engine_args = AsyncEngineArgs(
            model=self.model_path,
            hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
            block_size=256,
            max_model_len=8192,
            enforce_eager=False,
            trust_remote_code=True,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.75,  # Match original script
        )
        self.model = AsyncLLMEngine.from_engine_args(engine_args)

        print("AsyncLLMEngine initialized successfully!")

    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.model is not None

    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()

    def load_image(self, image_path: str) -> Tuple[Image.Image, int, int]:
        """Load image and handle EXIF rotation"""
        from PIL import ImageOps

        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if needed (handles RGBA, LA, L, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        return img, width, height

    def parse_detections(self, text: str, img_width: int, img_height: int) -> List[DetectedElement]:
        """Parse <|ref|> and <|det|> tags from OCR output"""
        elements = []

        # Pattern: <|ref|>label<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
        pattern = r'<\|ref\|>(.*?)<\|/ref\|><\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>'
        matches = re.finditer(pattern, text)

        for match in matches:
            label = match.group(1).strip()
            x1, y1, x2, y2 = map(int, match.groups()[1:])

            # Convert from 0-999 normalized coords to actual pixels
            bbox = BoundingBox(
                x1=x1 * img_width / 1000,
                y1=y1 * img_height / 1000,
                x2=x2 * img_width / 1000,
                y2=y2 * img_height / 1000
            )

            # Classify element type
            element_type = self._classify_element(label)

            elements.append(DetectedElement(
                label=label,
                element_type=element_type,
                bbox=bbox
            ))

        return elements

    def _classify_element(self, label: str) -> str:
        """Classify detected element by label content"""
        label_lower = label.lower()

        # Check for dimensions
        if any(unit in label for unit in ['mm', 'cm', 'm', 'in', 'ft', '"', "'"]):
            return "dimension"
        if any(sym in label for sym in ['Ø', '∅', 'R', '±', '°']):
            return "dimension"

        # Check for part numbers (common patterns)
        if re.search(r'(p/n|part|item|pos|no\.?)\s*[:#]?\s*[\w-]+', label_lower):
            return "part_number"

        # Check for table indicators
        if any(word in label_lower for word in ['item', 'qty', 'description', 'part number']):
            return "table"

        # Check for titles
        if any(word in label_lower for word in ['title', 'drawing', 'sheet', 'revision']):
            return "title"

        return "text"

    def extract_dimensions(self, text: str, elements: List[DetectedElement]) -> List[Dimension]:
        """Extract dimension information"""
        dimensions = []

        # Pattern for dimensions: numbers with units
        dim_pattern = r'(Ø|∅|R)?(\d+(?:\.\d+)?)\s*(mm|cm|m|in|ft|°|″|′)?(\s*±\s*\d+(?:\.\d+)?)?'

        for element in elements:
            if element.element_type == "dimension":
                match = re.search(dim_pattern, element.label)
                if match:
                    prefix, value, unit, tolerance = match.groups()

                    dim_type = None
                    if prefix == 'Ø' or prefix == '∅':
                        dim_type = "diameter"
                    elif prefix == 'R':
                        dim_type = "radius"
                    elif '°' in element.label:
                        dim_type = "angular"
                    else:
                        dim_type = "linear"

                    dimensions.append(Dimension(
                        value=element.label,
                        unit=unit,
                        tolerance=tolerance.strip() if tolerance else None,
                        dimension_type=dim_type,
                        bbox=element.bbox
                    ))

        return dimensions

    def extract_part_numbers(self, text: str, elements: List[DetectedElement]) -> List[PartNumber]:
        """Extract part numbers"""
        part_numbers = []

        for element in elements:
            if element.element_type == "part_number":
                # Try to extract structured part number
                match = re.search(r'(p/n|part|item|pos|no\.?)\s*[:#]?\s*([\w-]+)',
                                element.label, re.IGNORECASE)
                if match:
                    number = match.group(2)
                else:
                    number = element.label

                part_numbers.append(PartNumber(
                    number=number,
                    bbox=element.bbox
                ))

        return part_numbers

    def extract_tables(self, text: str) -> List[ExtractedTable]:
        """Extract table structures from markdown"""
        tables = []

        # Find markdown tables
        table_pattern = r'\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)'
        matches = re.finditer(table_pattern, text)

        for match in matches:
            header_line = match.group(1)
            body_lines = match.group(2)

            # Parse headers
            headers = [h.strip() for h in header_line.split('|') if h.strip()]

            # Parse rows
            rows = []
            for i, line in enumerate(body_lines.strip().split('\n')):
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if cells:
                    rows.append(TableRow(cells=cells, row_number=i))

            # Classify table type
            table_type = "general"
            header_text = ' '.join(headers).lower()
            if any(word in header_text for word in ['item', 'qty', 'part', 'description']):
                table_type = "bom"

            tables.append(ExtractedTable(
                headers=headers,
                rows=rows,
                table_type=table_type
            ))

        return tables

    def extract_drawing_metadata(self, text: str, elements: List[DetectedElement]) -> Dict[str, Optional[str]]:
        """Extract drawing title, number, revision, scale"""
        metadata = {
            "title": None,
            "number": None,
            "revision": None,
            "scale": None
        }

        # Look for title block information
        title_pattern = r'(?:title|drawing)[:\s]+(.+?)(?:\n|$)'
        number_pattern = r'(?:drawing|dwg|no\.?)[:\s#]+([\w-]+)'
        revision_pattern = r'(?:rev\.?|revision)[:\s]+([A-Z0-9]+)'
        scale_pattern = r'scale[:\s]+(1:\d+|\d+:\d+)'

        title_match = re.search(title_pattern, text, re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        number_match = re.search(number_pattern, text, re.IGNORECASE)
        if number_match:
            metadata["number"] = number_match.group(1).strip()

        revision_match = re.search(revision_pattern, text, re.IGNORECASE)
        if revision_match:
            metadata["revision"] = revision_match.group(1).strip()

        scale_match = re.search(scale_pattern, text, re.IGNORECASE)
        if scale_match:
            metadata["scale"] = scale_match.group(1).strip()

        return metadata

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
        """Process a technical drawing image"""
        start_time = time.time()

        # Load image
        img, img_width, img_height = self.load_image(image_path)

        # Select prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.prompts.get(mode, self.prompts["technical_drawing"])

        # Temporarily set config.PROMPT for the processor to use
        original_prompt = config.PROMPT
        config.PROMPT = prompt

        try:
            # Tokenize with processor (uses config.PROMPT internally)
            # Returns: [[input_ids, pixel_values, images_crop, images_seq_mask, images_spatial_crop, num_image_tokens, image_shapes]]
            image_data = self.processor.tokenize_with_images(
                images=[img],
                bos=True,
                eos=True,
                cropping=crop_mode
            )

            # Debug: log the structure of image_data
            print(f"DEBUG: FULL Prompt being used:\n{prompt}\n" + "="*50)
            print(f"DEBUG: Has <|grounding|> tag: {'<|grounding|>' in prompt}")
            print(f"DEBUG: image_data type: {type(image_data)}")
            if isinstance(image_data, list) and len(image_data) > 0:
                print(f"DEBUG: image_data[0] (should be list of 7): {type(image_data[0])}, len={len(image_data[0]) if isinstance(image_data[0], list) else 'N/A'}")
                if isinstance(image_data[0], list) and len(image_data[0]) >= 7:
                    # [input_ids, pixel_values, images_crop, images_seq_mask, images_spatial_crop, num_image_tokens, image_shapes]
                    input_ids, pixel_values, images_crop, images_seq_mask, images_spatial_crop, num_image_tokens, image_shapes = image_data[0]
                    print(f"DEBUG:   input_ids shape: {input_ids.shape if hasattr(input_ids, 'shape') else type(input_ids)}")
                    print(f"DEBUG:   pixel_values shape: {pixel_values.shape if hasattr(pixel_values, 'shape') else type(pixel_values)}")
                    print(f"DEBUG:   images_crop shape: {images_crop.shape if hasattr(images_crop, 'shape') else type(images_crop)}")
                    print(f"DEBUG:   num_image_tokens: {num_image_tokens}")
                    print(f"DEBUG:   image_shapes: {image_shapes}")

        finally:
            # Restore original prompt
            config.PROMPT = original_prompt

        # Prepare sampling params (match original script exactly)
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=30,
                window_size=90,
                whitelist_token_ids={128821, 128822}  # <td>, </td>
            )
        ]

        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
        )

        # Generate with AsyncLLMEngine (exactly like original script)
        request_id = f"request-{int(time.time())}"

        # Prepare request dict (NOT as a list - async engine takes dict directly)
        if '<image>' in prompt:
            request = {
                "prompt": prompt,
                "multi_modal_data": {"image": image_data}
            }
        else:
            request = {
                "prompt": prompt
            }

        # Stream generate (collect full output)
        output_text = ""
        async for request_output in self.model.generate(
            request, sampling_params, request_id
        ):
            if request_output.outputs:
                output_text = request_output.outputs[0].text

        # Debug logging
        print(f"DEBUG: Output text length: {len(output_text)}")
        print(f"DEBUG: First 500 chars: {output_text[:500]}")
        print(f"DEBUG: Contains <|ref|>: {'<|ref|>' in output_text}")
        print(f"DEBUG: Contains <|det|>: {'<|det|>' in output_text}")

        # Parse detections
        detected_elements = []
        if grounding:
            detected_elements = self.parse_detections(output_text, img_width, img_height)
            print(f"DEBUG: Parsed {len(detected_elements)} elements")

        # Extract structured data
        dimensions = []
        part_numbers_list = []
        tables = []

        if extract_dimensions:
            dimensions = self.extract_dimensions(output_text, detected_elements)

        if extract_part_numbers:
            part_numbers_list = self.extract_part_numbers(output_text, detected_elements)

        if extract_tables:
            tables = self.extract_tables(output_text)

        # Extract metadata
        metadata = self.extract_drawing_metadata(output_text, detected_elements)

        processing_time = time.time() - start_time

        return TechnicalDrawingResponse(
            text=output_text,
            markdown=output_text,
            detected_elements=detected_elements,
            image_width=img_width,
            image_height=img_height,
            processing_time=processing_time,
            dimensions=dimensions,
            part_numbers=part_numbers_list,
            tables=tables,
            annotations=[],
            drawing_title=metadata["title"],
            drawing_number=metadata["number"],
            revision=metadata["revision"],
            scale=metadata["scale"]
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
        images = []
        temp_image_paths = []

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))

            temp_path = f"/tmp/page_{page_num}.png"
            pix.save(temp_path)
            temp_image_paths.append(temp_path)

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
        # vLLM handles cleanup automatically
        pass
