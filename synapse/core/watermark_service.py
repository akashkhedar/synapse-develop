"""
Watermarking Service for Data Traceability

Provides visible and invisible watermarking for images to trace data leaks.
"""

import base64
import hashlib
import io
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

logger = logging.getLogger(__name__)


class WatermarkService:
    """
    Watermarking service for tracing data leaks.

    Provides:
    - Visible watermarks with user info
    - Invisible (steganographic) watermarks for forensic tracing
    - Watermark extraction for leak investigation

    Usage:
        # Apply visible watermark
        watermarked = WatermarkService.apply_visible_watermark(
            image_bytes, user_id="123", session_id="abc"
        )

        # Apply invisible watermark
        watermarked = WatermarkService.apply_invisible_watermark(
            image_bytes, payload={"user_id": "123", "timestamp": "..."}
        )

        # Extract invisible watermark
        payload = WatermarkService.extract_watermark(watermarked_bytes)
    """

    # Watermark styling
    FONT_SIZE = 14
    WATERMARK_OPACITY = 40  # 0-255
    WATERMARK_COLOR = (128, 128, 128)  # Gray

    # For invisible watermarking
    MAGIC_HEADER = b"SYN_WM_V1"

    @classmethod
    def apply_visible_watermark(
        cls,
        image_data: bytes,
        user_id: str,
        session_id: str = None,
        timestamp: datetime = None,
        position: str = "tiled",
    ) -> bytes:
        """
        Apply visible watermark with user info.

        Args:
            image_data: Image bytes
            user_id: User identifier (will be partially masked)
            session_id: Optional session identifier
            timestamp: Optional timestamp (defaults to now)
            position: "tiled", "corner", or "center"

        Returns:
            Watermarked image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGBA for transparency support
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Create watermark text
            if timestamp is None:
                timestamp = datetime.now()

            # Mask user ID for privacy (show first 3 and last 2 chars)
            masked_id = cls._mask_identifier(user_id)

            watermark_text = f"{masked_id} | {timestamp.strftime('%Y-%m-%d %H:%M')}"
            if session_id:
                watermark_text += f" | {session_id[:8]}"

            # Apply watermark based on position
            if position == "tiled":
                result = cls._apply_tiled_watermark(image, watermark_text)
            elif position == "corner":
                result = cls._apply_corner_watermark(image, watermark_text)
            else:
                result = cls._apply_center_watermark(image, watermark_text)

            # Convert back to original format
            output = io.BytesIO()
            result.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to apply visible watermark: {e}")
            return image_data

    @classmethod
    def apply_invisible_watermark(
        cls,
        image_data: bytes,
        payload: Dict[str, Any],
    ) -> bytes:
        """
        Apply invisible steganographic watermark.

        Embeds payload data in the least significant bits of pixel values.

        Args:
            image_data: Image bytes
            payload: Metadata to embed (will be JSON encoded)

        Returns:
            Watermarked image bytes
        """
        import json

        try:
            image = Image.open(io.BytesIO(image_data))

            if image.mode != "RGB":
                image = image.convert("RGB")

            # Prepare payload
            payload_json = json.dumps(payload, separators=(",", ":"))
            payload_bytes = cls.MAGIC_HEADER + payload_json.encode("utf-8")

            # Add length prefix and checksum
            length = len(payload_bytes)
            checksum = hashlib.md5(payload_bytes).digest()[:4]
            data_to_embed = length.to_bytes(4, "big") + checksum + payload_bytes

            # Convert to bits
            bits = "".join(format(byte, "08b") for byte in data_to_embed)

            # Check if image can hold the data
            pixels = image.load()
            width, height = image.size
            max_bits = width * height * 3  # 3 channels

            if len(bits) > max_bits:
                logger.warning("Image too small for steganographic watermark")
                return image_data

            # Embed bits in LSB
            bit_index = 0
            for y in range(height):
                for x in range(width):
                    if bit_index >= len(bits):
                        break

                    r, g, b = pixels[x, y]

                    # Modify LSB of each channel
                    if bit_index < len(bits):
                        r = (r & 0xFE) | int(bits[bit_index])
                        bit_index += 1
                    if bit_index < len(bits):
                        g = (g & 0xFE) | int(bits[bit_index])
                        bit_index += 1
                    if bit_index < len(bits):
                        b = (b & 0xFE) | int(bits[bit_index])
                        bit_index += 1

                    pixels[x, y] = (r, g, b)

            # Save as PNG to preserve LSB data
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to apply invisible watermark: {e}")
            return image_data

    @classmethod
    def extract_watermark(cls, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Extract invisible watermark from image.

        Args:
            image_data: Potentially watermarked image bytes

        Returns:
            Extracted payload dict, or None if not found
        """
        import json

        try:
            image = Image.open(io.BytesIO(image_data))

            if image.mode != "RGB":
                image = image.convert("RGB")

            pixels = image.load()
            width, height = image.size

            # Extract LSB bits
            bits = []
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    bits.extend([r & 1, g & 1, b & 1])

                    # Stop once we have enough for header check
                    if len(bits) >= 512:  # Enough for length + checksum + header
                        break
                if len(bits) >= 512:
                    break

            # Convert bits to bytes
            extracted_bytes = bytes(
                int("".join(str(b) for b in bits[i : i + 8]), 2)
                for i in range(0, len(bits), 8)
            )

            # Parse length and checksum
            length = int.from_bytes(extracted_bytes[:4], "big")
            stored_checksum = extracted_bytes[4:8]

            # Validate
            if length > width * height * 3 // 8:
                return None

            # Extract full payload
            bits = []
            total_bytes_needed = 8 + length
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    bits.extend([r & 1, g & 1, b & 1])
                    if len(bits) >= total_bytes_needed * 8:
                        break
                if len(bits) >= total_bytes_needed * 8:
                    break

            extracted_bytes = bytes(
                int("".join(str(b) for b in bits[i : i + 8]), 2)
                for i in range(0, len(bits), 8)
            )

            payload_bytes = extracted_bytes[8 : 8 + length]

            # Verify checksum
            computed_checksum = hashlib.md5(payload_bytes).digest()[:4]
            if stored_checksum != computed_checksum:
                return None

            # Check magic header
            if not payload_bytes.startswith(cls.MAGIC_HEADER):
                return None

            # Parse JSON payload
            json_str = payload_bytes[len(cls.MAGIC_HEADER) :].decode("utf-8")
            return json.loads(json_str)

        except Exception as e:
            logger.debug(f"Failed to extract watermark: {e}")
            return None

    @classmethod
    def _mask_identifier(cls, identifier: str) -> str:
        """Mask identifier for privacy"""
        if len(identifier) <= 5:
            return identifier[0] + "*" * (len(identifier) - 1)
        return identifier[:3] + "***" + identifier[-2:]

    @classmethod
    def _apply_tiled_watermark(cls, image: Image.Image, text: str) -> Image.Image:
        """Apply watermark in a diagonal tiled pattern"""
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", cls.FONT_SIZE)
        except:
            font = ImageFont.load_default()

        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate spacing
        spacing_x = text_width + 100
        spacing_y = text_height + 80

        # Draw tiled pattern
        for y in range(-text_height, image.height + text_height, spacing_y):
            for x in range(-text_width, image.width + text_width, spacing_x):
                # Offset every other row
                offset = (spacing_x // 2) if (y // spacing_y) % 2 else 0
                draw.text(
                    (x + offset, y),
                    text,
                    font=font,
                    fill=(*cls.WATERMARK_COLOR, cls.WATERMARK_OPACITY),
                )

        # Composite
        return Image.alpha_composite(image, overlay)

    @classmethod
    def _apply_corner_watermark(cls, image: Image.Image, text: str) -> Image.Image:
        """Apply watermark in bottom-right corner"""
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", cls.FONT_SIZE)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = image.width - text_width - 10
        y = image.height - text_height - 10

        draw.text(
            (x, y), text, font=font, fill=(*cls.WATERMARK_COLOR, cls.WATERMARK_OPACITY)
        )

        return Image.alpha_composite(image, overlay)

    @classmethod
    def _apply_center_watermark(cls, image: Image.Image, text: str) -> Image.Image:
        """Apply watermark in center"""
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", cls.FONT_SIZE * 2)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2

        draw.text(
            (x, y),
            text,
            font=font,
            fill=(*cls.WATERMARK_COLOR, cls.WATERMARK_OPACITY + 20),
        )

        return Image.alpha_composite(image, overlay)

    @classmethod
    def create_forensic_watermark(
        cls,
        user_id: str,
        session_id: str,
        project_id: str = None,
        task_id: str = None,
    ) -> Dict[str, Any]:
        """
        Create forensic watermark payload for invisible embedding.

        Args:
            user_id: User identifier
            session_id: Session identifier
            project_id: Optional project ID
            task_id: Optional task ID

        Returns:
            Payload dict for invisible watermarking
        """
        return {
            "u": user_id,
            "s": session_id[:16] if session_id else None,
            "p": project_id,
            "t": task_id,
            "ts": datetime.utcnow().isoformat(),
            "v": 1,  # Watermark version
        }
