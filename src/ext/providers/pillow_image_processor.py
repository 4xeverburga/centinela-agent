from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from app.domain.entities import ImagePayload
from app.ports.image_processor import ImageProcessor


class PillowImageProcessor(ImageProcessor):
    def __init__(self, max_long_edge: int, jpeg_quality: int):
        self._max_long_edge = max_long_edge
        self._jpeg_quality = jpeg_quality

    def compress(self, payload: ImagePayload) -> ImagePayload:
        img = Image.open(BytesIO(payload.data))
        img = img.convert("RGB")
        w, h = img.size
        long_edge = max(w, h)

        if long_edge > self._max_long_edge:
            scale = self._max_long_edge / long_edge
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            new_w, new_h = w, h

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=self._jpeg_quality)
        return ImagePayload(
            data=buf.getvalue(),
            mime_type="image/jpeg",
            width=new_w,
            height=new_h,
        )

    def sharpness(self, payload: ImagePayload) -> float:
        arr = np.frombuffer(payload.data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return cv2.Laplacian(img, cv2.CV_64F).var()
