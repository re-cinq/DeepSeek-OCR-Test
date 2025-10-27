# View Detection with Qwen3-VL

This document describes the view detection and grounding capabilities added to the Qwen3-VL backend.

## Overview

Qwen3-VL-8B-Thinking has "Advanced Spatial Perception" and "2D grounding" capabilities that allow it to:
- Identify different views in technical drawings (front, side, top, section, detail views)
- Return bounding box coordinates for detected elements
- Provide structured JSON output for visualization

## Features

### 1. **View Detection Mode**
A specialized prompt mode that detects and localizes all views in a technical drawing:
- Front view, side view, top view
- Section views (A-A, B-B, etc.)
- Detail views
- Isometric/3D views
- Auxiliary views

### 2. **Grounding Support**
When grounding is enabled, the model returns bounding boxes in JSON format:
```json
[
  {
    "bbox_2d": [x1, y1, x2, y2],
    "label": "front view",
    "sub_label": "main assembly"
  },
  {
    "bbox_2d": [x1, y1, x2, y2],
    "label": "section A-A",
    "sub_label": "detail of connection"
  }
]
```

**Coordinate System:**
- Format: `[x1, y1, x2, y2]` (top-left corner to bottom-right corner)
- Type: Absolute pixel coordinates
- Origin: Top-left (0, 0)

### 3. **Element Classification**
Detected elements are automatically classified by type for color-coded visualization:

| Element Type | Color | Examples |
|--------------|-------|----------|
| `view` | Red (#ef4444) | Front view, side view, section A-A |
| `dimension` | Green (#10b981) | Measurements, diameters, tolerances |
| `part_number` | Blue (#3b82f6) | Item numbers, callouts, positions |
| `table` | Amber (#f59e0b) | BOM tables, revision tables |
| `title` | Purple (#8b5cf6) | Title block, drawing number |
| `text` | Gray (#6b7280) | General text |

## Usage

### Backend API

#### Chat Endpoint with Grounding
```bash
curl -X POST http://localhost:8000/api/chat \
  -F "session_id=abc123" \
  -F "question=Show me all views in this drawing" \
  -F "use_grounding=true"
```

#### Process Endpoint with View Detection Mode
```bash
curl -X POST http://localhost:8000/api/ocr/process \
  -F "file=@drawing.pdf" \
  -F "mode=view_detection" \
  -F "grounding=true"
```

### Frontend Usage

The frontend automatically enables grounding when certain keywords are detected in questions:

**German Keywords:**
- `ansicht` (view)
- `zeige` (show)
- `wo ist` (where is)
- `finde` (find)

**English Keywords:**
- `view`
- `locate`
- `show`
- `find`

**Example Questions:**
- "Zeige mir alle Ansichten (Views) in dieser Zeichnung"
- "Show me all views in this drawing"
- "Where is the front view?"
- "Wo ist die Seitenansicht?"

### Predefined Questions

A new predefined question has been added:
```javascript
"Zeige mir alle Ansichten (Views) in dieser Zeichnung"
```

This automatically enables grounding and requests view detection.

## Implementation Details

### Backend Components

#### 1. `qwen_vision_service.py`

**New Methods:**
- `parse_grounding_json()` - Parses JSON bbox output from Qwen3-VL
- `_classify_element_type()` - Classifies elements by label for color coding

**New Prompt Mode:**
```python
"view_detection": "Detect all views in this technical drawing including:
front view, side view, top view, section views (A-A, B-B, etc.), detail views,
isometric/3D views, and any auxiliary views. Return their locations and labels
in JSON format: [{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"view name\",
\"sub_label\": \"additional info\"}]. Be precise with the bounding box coordinates."
```

**Updated Processing:**
```python
# Parse detections if grounding is enabled
detected_elements = []
if grounding:
    detected_elements = self.parse_grounding_json(output_text, img_width, img_height)
```

#### 2. `main.py`

**Updated Chat Endpoint:**
```python
# Build prompt for Qwen3-VL
if use_grounding:
    custom_prompt = f"{question}\n\nReturn the locations in JSON format: [{{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"description\"}}]"
else:
    custom_prompt = question
```

### Frontend Components

#### 1. `ConversationalMode.jsx`

**Automatic Grounding Detection:**
```javascript
const enableGrounding = userQuestion.toLowerCase().includes('ansicht') ||
                       userQuestion.toLowerCase().includes('view') ||
                       userQuestion.toLowerCase().includes('zeige') ||
                       userQuestion.toLowerCase().includes('locate') ||
                       userQuestion.toLowerCase().includes('wo ist') ||
                       userQuestion.toLowerCase().includes('finde');
```

#### 2. `BoundingBoxOverlay.jsx`

**Added View Element Color:**
```javascript
const ELEMENT_COLORS = {
  // ... other colors
  view: '#ef4444', // red - for different views
};
```

## Example Workflow

1. **User uploads technical drawing** with multiple views (front, side, top)
2. **User asks:** "Zeige mir alle Ansichten (Views) in dieser Zeichnung"
3. **Frontend detects keyword** "Ansichten" and enables grounding
4. **Backend adds JSON instruction** to the prompt
5. **Qwen3-VL analyzes** the drawing and returns:
   ```json
   [
     {"bbox_2d": [50, 100, 400, 500], "label": "front view"},
     {"bbox_2d": [450, 100, 800, 500], "label": "side view"},
     {"bbox_2d": [50, 550, 400, 900], "label": "top view"},
     {"bbox_2d": [450, 550, 650, 750], "label": "section A-A"}
   ]
   ```
6. **Backend parses JSON** and creates `DetectedElement` objects
7. **Frontend receives response** with `detected_elements` array
8. **BoundingBoxOverlay draws** red bounding boxes on each view
9. **User sees visual overlay** showing exactly where each view is located

## Testing

### Test View Detection

1. Upload a technical drawing with multiple views
2. Click the predefined question: "Zeige mir alle Ansichten (Views) in dieser Zeichnung"
3. Wait for response
4. Check that:
   - Red bounding boxes appear around different views
   - Each box is labeled with the view name
   - Console shows: `DEBUG: Parsed N grounding elements from JSON`

### Test Custom Grounding Queries

Try questions like:
- "Where are the dimensions located?" (enables grounding automatically)
- "Zeige mir die Stückliste" (show me the BOM)
- "Find all part numbers"
- "Wo ist der Maßstab?" (where is the scale?)

### Debug Output

The backend logs grounding operations:
```
DEBUG: Parsed 4 grounding elements from JSON
DEBUG: Parsed 4 grounded elements
✓ Chat response in 2.34s - 4 elements
```

## Limitations

1. **Accuracy depends on model performance** - Qwen3-VL-8B-Thinking may not always perfectly identify all views
2. **Coordinate precision** - Bounding boxes may not be pixel-perfect
3. **Complex drawings** - Very dense drawings with many overlapping views may be challenging
4. **Language understanding** - Works best with clear, explicit prompts requesting view detection

## Comparison: DeepSeek-OCR vs Qwen3-VL Grounding

| Feature | DeepSeek-OCR | Qwen3-VL |
|---------|--------------|----------|
| **Activation** | `<\|grounding\|>` tag | JSON instruction in prompt |
| **Output Format** | `<ref>label</ref><box>(x1,y1),(x2,y2)</box>` | JSON: `{"bbox_2d": [x1,y1,x2,y2], "label": "..."}` |
| **Coordinates** | Normalized 0-999 | Absolute pixels |
| **Parsing** | Regex for special tags | JSON extraction |
| **Flexibility** | Fixed element types | Flexible labels based on prompt |

## Future Enhancements

Potential improvements:
1. **UI toggle** for grounding in settings
2. **Confidence scores** in bounding box output
3. **Click-to-highlight** interaction with bounding boxes
4. **Export grounding data** to JSON/CSV
5. **Custom element type definitions** by user
6. **View relationship detection** (which view shows what part)

## References

- [Qwen3-VL Model Card](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking)
- [Qwen2.5-VL Grounding Documentation](https://qwenlm.github.io/blog/qwen2.5-vl/)
- [PyImageSearch: Object Detection with Qwen 2.5](https://pyimagesearch.com/2025/06/09/object-detection-and-visual-grounding-with-qwen-2-5/)
