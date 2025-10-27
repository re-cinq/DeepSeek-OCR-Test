"""
Image preprocessing to improve OCR quality
"""
from PIL import Image, ImageEnhance, ImageOps
import numpy as np
from typing import Tuple


class ImagePreprocessor:
    """Preprocess images to improve OCR quality"""

    @staticmethod
    def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Increase contrast to make text and lines more visible

        Args:
            image: PIL Image
            factor: Contrast factor (1.0 = original, >1.0 = more contrast)

        Returns:
            Enhanced image
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @staticmethod
    def enhance_sharpness(image: Image.Image, factor: float = 2.0) -> Image.Image:
        """
        Sharpen image to improve edge detection

        Args:
            image: PIL Image
            factor: Sharpness factor (1.0 = original, >1.0 = sharper)

        Returns:
            Sharpened image
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def adjust_brightness(image: Image.Image, factor: float = 1.2) -> Image.Image:
        """
        Adjust brightness for better visibility

        Args:
            image: PIL Image
            factor: Brightness factor (1.0 = original)

        Returns:
            Adjusted image
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def remove_noise(image: Image.Image) -> Image.Image:
        """
        Apply median filter to remove noise

        Args:
            image: PIL Image

        Returns:
            Denoised image
        """
        from PIL import ImageFilter
        return image.filter(ImageFilter.MedianFilter(size=3))

    @staticmethod
    def upscale_if_small(image: Image.Image, min_width: int = 1500) -> Image.Image:
        """
        Upscale image if it's too small (improves OCR on low-res images)

        Args:
            image: PIL Image
            min_width: Minimum width in pixels

        Returns:
            Upscaled image if necessary
        """
        width, height = image.size
        if width < min_width:
            scale_factor = min_width / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image

    @staticmethod
    def auto_rotate(image: Image.Image) -> Image.Image:
        """
        Auto-rotate based on EXIF orientation

        Args:
            image: PIL Image

        Returns:
            Correctly oriented image
        """
        return ImageOps.exif_transpose(image)

    @staticmethod
    def convert_to_rgb(image: Image.Image) -> Image.Image:
        """
        Ensure image is in RGB mode

        Args:
            image: PIL Image

        Returns:
            RGB image
        """
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    @classmethod
    def preprocess_for_technical_drawing(cls, image: Image.Image,
                                         aggressive: bool = False) -> Image.Image:
        """
        Complete preprocessing pipeline for technical drawings

        Args:
            image: PIL Image
            aggressive: If True, apply more aggressive enhancements

        Returns:
            Preprocessed image
        """
        # 1. Auto-rotate
        image = cls.auto_rotate(image)

        # 2. Convert to RGB
        image = cls.convert_to_rgb(image)

        # 3. Upscale if too small
        image = cls.upscale_if_small(image, min_width=1500)

        if aggressive:
            # Aggressive mode: for very poor quality images
            # 4. Remove noise
            image = cls.remove_noise(image)

            # 5. Increase contrast significantly
            image = cls.enhance_contrast(image, factor=2.0)

            # 6. Sharpen heavily
            image = cls.enhance_sharpness(image, factor=2.5)

            # 7. Adjust brightness
            image = cls.adjust_brightness(image, factor=1.3)
        else:
            # Normal mode: subtle improvements
            # 4. Slight contrast boost
            image = cls.enhance_contrast(image, factor=1.3)

            # 5. Mild sharpening
            image = cls.enhance_sharpness(image, factor=1.5)

        return image

    @classmethod
    def analyze_image_quality(cls, image: Image.Image) -> dict:
        """
        Analyze image quality metrics

        Args:
            image: PIL Image

        Returns:
            Dictionary with quality metrics
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Calculate metrics
        mean_brightness = img_array.mean()
        std_brightness = img_array.std()

        width, height = image.size

        # Quality assessment
        quality = {
            'width': width,
            'height': height,
            'mean_brightness': float(mean_brightness),
            'contrast': float(std_brightness),
            'is_low_res': width < 1000 or height < 1000,
            'is_low_contrast': std_brightness < 30,
            'is_too_dark': mean_brightness < 50,
            'is_too_bright': mean_brightness > 200,
            'recommended_preprocessing': 'normal'
        }

        # Recommend aggressive preprocessing if quality issues detected
        if quality['is_low_contrast'] or quality['is_too_dark'] or quality['is_low_res']:
            quality['recommended_preprocessing'] = 'aggressive'

        return quality
