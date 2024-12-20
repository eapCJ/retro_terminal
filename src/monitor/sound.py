import math
import logging
import threading
import array
import queue
import numpy as np
from typing import Optional, NamedTuple
import simpleaudio as sa
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class SoundRequest(NamedTuple):
    frequency: int
    duration: int
    volume: float
    priority: int  # Higher number = higher priority
    timestamp: float

class SoundPlayer:
    def __init__(self, max_queue_size: int = 100):
        self.sound_supported = True
        self._audio_lock = threading.Lock()
        self._wave_cache = {}  # Cache for generated wave objects
        self._sound_queue = queue.PriorityQueue(maxsize=max_queue_size)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sound_worker")
        self._running = True
        self._start_sound_worker()
        
    def _start_sound_worker(self):
        """Start the background sound processing worker"""
        self._executor.submit(self._process_sound_queue)
    
    def _process_sound_queue(self):
        """Process sound requests from the queue"""
        while self._running:
            try:
                # Get the next sound request (blocks until one is available)
                _, sound_request = self._sound_queue.get(timeout=1.0)
                if self.sound_supported:
                    with self._audio_lock:
                        wave_obj = self._generate_sine_wave(
                            sound_request.frequency,
                            sound_request.duration,
                            sound_request.volume
                        )
                        play_obj = wave_obj.play()
                        play_obj.wait_done()  # Wait for sound to complete before processing next
                self._sound_queue.task_done()
            except queue.Empty:
                continue  # No sound requests, keep waiting
            except Exception as e:
                logger.error(f"Error processing sound queue: {e}")
                continue
    
    def _generate_sine_wave(self, frequency: int, duration_ms: int, volume: float = 1.0) -> sa.WaveObject:
        """Generate a sine wave with the given frequency and duration"""
        cache_key = (frequency, duration_ms, volume)
        if cache_key in self._wave_cache:
            return self._wave_cache[cache_key]
            
        try:
            sample_rate = 44100
            num_samples = int((duration_ms / 1000.0) * sample_rate)
            
            # Generate time array and envelope more efficiently
            t = np.linspace(0, duration_ms / 1000.0, num_samples, False)
            attack_samples = int(num_samples * 0.1)
            release_samples = int(num_samples * 0.1)
            sustain_samples = num_samples - attack_samples - release_samples
            
            envelope = np.concatenate([
                np.linspace(0, 1, attack_samples),
                np.ones(sustain_samples),
                np.linspace(1, 0, release_samples)
            ])
            
            samples = np.sin(2 * np.pi * frequency * t) * volume * envelope
            audio_data = (samples * 32767).astype(np.int16)
            stereo_data = np.column_stack((audio_data, audio_data))
            
            wave_obj = sa.WaveObject(stereo_data.tobytes(), 2, 2, sample_rate)
            self._wave_cache[cache_key] = wave_obj
            return wave_obj
            
        except Exception as e:
            logger.error(f"Error generating sine wave: {e}")
            self.sound_supported = False
            raise
    
    def play_notification(self, frequency: int = 1000, duration: int = 100, volume: float = 1.0, priority: int = 1):
        """Queue a notification sound with given parameters and priority"""
        if not self.sound_supported:
            return
            
        try:
            # Create sound request with negative priority for proper queue ordering (higher numbers = higher priority)
            sound_request = SoundRequest(frequency, duration, volume, priority, time.time())
            # Use negative priority so higher numbers have higher priority in the queue
            self._sound_queue.put_nowait((-priority, sound_request))
        except queue.Full:
            logger.warning("Sound queue full, dropping notification")
        except Exception as e:
            logger.error(f"Error queueing sound: {e}")
            self.sound_supported = False
    
    def shutdown(self):
        """Cleanup resources"""
        self._running = False
        self._executor.shutdown(wait=True)
        self._wave_cache.clear()

# Global sound player instance
sound_player = SoundPlayer()

# Ensure cleanup on program exit
import atexit
atexit.register(sound_player.shutdown) 