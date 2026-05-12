"""
Face Verification Module
Handles face-recognition-based identity verification for check-ins.

Why separate module?
- Encapsulates AI/ML logic
- Easy to mock for testing
- Can be replaced without touching business logic
- Uses lightweight face-recognition library (dlib-based, no TensorFlow)
"""

import numpy as np
import face_recognition
from typing import Tuple, Optional
import base64
import io
from PIL import Image
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FaceVerificationError(Exception):
    """Custom exception for face verification failures."""
    pass


class FaceVerifier:
    """Handles face detection and verification."""
    
    def __init__(self):
        self.threshold = settings.FACE_MATCH_THRESHOLD
        # Note: face-recognition uses dlib internally, which is pre-trained
        
    def encode_face(self, image_bytes: bytes) -> np.ndarray:
        """
        Extract face encoding from image.
        
        Args:
            image_bytes: Raw image bytes (PNG/JPG)
            
        Returns:
            128-dimensional face encoding vector
            
        Raises:
            FaceVerificationError: If no face detected
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to numpy array (RGB format)
            img_array = np.array(image)
            
            # Ensure RGB format (face-recognition requires it)
            if len(img_array.shape) == 2:  # Grayscale
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]
            
            # Extract face encodings
            face_encodings = face_recognition.face_encodings(img_array)
            
            if not face_encodings:
                raise FaceVerificationError("No face detected in image")
            
            # Return first face encoding (128-dim)
            return face_encodings[0]
            
        except FaceVerificationError:
            raise
        except Exception as e:
            logger.error(f"Face encoding failed: {str(e)}")
            raise FaceVerificationError(f"Could not extract face: {str(e)}")
    
    def verify_face(
        self, 
        stored_embedding: np.ndarray,
        new_image_bytes: bytes
    ) -> Tuple[bool, float]:
        """
        Verify if new face matches stored embedding.
        
        Args:
            stored_embedding: 128-dim vector from enrollment
            new_image_bytes: Raw image bytes from check-in
            
        Returns:
            (is_match: bool, confidence: float)
            
        Confidence score:
        - 1.0: Perfect match
        - 0.6-1.0: Good match
        - < 0.6: No match
        
        The threshold is configurable in settings (default 0.6)
        """
        try:
            # Get new embedding
            new_embedding = self.encode_face(new_image_bytes)
            
            # Compute Euclidean distance (face-recognition standard)
            # Lower distance = better match
            distance = np.linalg.norm(stored_embedding - new_embedding)
            
            # Convert distance to similarity score (0-1)
            # Typical threshold for face-recognition: 0.6
            # distance 0 = identical (score 1.0)
            # distance 0.6 = match boundary (score 0)
            # We invert and clamp to 0-1 range
            similarity = max(0.0, 1.0 - (distance / 0.6))
            
            # Check if above threshold
            is_match = similarity >= self.threshold
            
            logger.info(f"Face verification: distance={distance:.3f}, similarity={similarity:.3f}, match={is_match}")
            
            return is_match, similarity
            
        except FaceVerificationError:
            raise
        except Exception as e:
            logger.error(f"Face verification failed: {str(e)}")
            raise FaceVerificationError(f"Verification failed: {str(e)}")


def base64_to_bytes(base64_str: str) -> bytes:
    """Convert base64 string to bytes."""
    try:
        return base64.b64decode(base64_str)
    except Exception as e:
        raise FaceVerificationError(f"Invalid base64 image: {str(e)}")


def bytes_to_base64(image_bytes: bytes) -> str:
    """Convert bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')


def base64_to_bytes(base64_str: str) -> bytes:
    """Convert base64 string to bytes."""
    try:
        return base64.b64decode(base64_str)
    except Exception as e:
        raise FaceVerificationError(f"Invalid base64 image: {str(e)}")


def bytes_to_base64(image_bytes: bytes) -> str:
    """Convert bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')
