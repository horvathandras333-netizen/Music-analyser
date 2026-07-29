from pathlib import Path

import numpy as np
import soundfile as sf


def load_audio(path: str | Path) -> tuple[np.ndarray, int]:
    """Load an audio file, converting multi-channel audio to mono float32.

    Args:
        path: Path to the audio file.

    Returns:
        Tuple of (audio_samples, sample_rate) where audio_samples is a 1D float32 numpy array.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If the audio file cannot be read or is empty.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    data, samplerate = sf.read(file_path, dtype="float32")

    if data.ndim > 1:
        data = np.mean(data, axis=1, dtype=np.float32)
    elif data.dtype != np.float32:
        data = data.astype(np.float32)

    if data.size == 0:
        raise ValueError(f"Audio file is empty: {file_path}")

    return data, int(samplerate)
