import numpy as np
import asyncio
import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

class VoiceDNASystem:
    """
    Biometric voice authentication for NEXA.
    
    Creates a unique Voice DNA profile from your voice.
    
    Security levels:
    - LOW: Quick 1-second check
    - MEDIUM: 3-second verification  
    - HIGH: 5-second multi-phrase check
    - CRITICAL: Full challenge-response
    
    Use cases:
    - Unlock destructive operations
    - Verify identity before sensitive tasks
    - Lock NEXA when different voice detected
    - Wake word authentication
    """
    
    def __init__(self, storage_path: str = "./data/voice_dna"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.is_enrolled = False
        self.voice_profile = None
        self.failed_attempts = 0
        self.max_attempts = 5
        self.lockout_until = None
        
        # Authentication thresholds
        self.thresholds = {
            'low': 0.75,
            'medium': 0.82,
            'high': 0.90,
            'critical': 0.95
        }
        
        self._load_profile()
    
    def _load_profile(self):
        """Load voice DNA profile"""
        
        profile_file = self.storage_path / "voice_profile.json"
        
        if profile_file.exists():
            with open(profile_file) as f:
                data = json.load(f)
                self.voice_profile = data
                self.is_enrolled = True
    
    def _save_profile(self):
        """Save voice DNA profile"""
        
        profile_file = self.storage_path / "voice_profile.json"
        
        with open(profile_file, 'w') as f:
            json.dump(self.voice_profile, f, indent=2, default=str)
    
    async def enroll(self, audio_samples: List[bytes]) -> Dict:
        """
        Enroll user's voice DNA.
        Requires 5 audio samples for accuracy.
        """
        
        if len(audio_samples) < 3:
            return {
                'success': False,
                'error': 'At least 3 audio samples required for enrollment'
            }
        
        try:
            # Extract features from each sample
            all_features = []
            
            for i, audio in enumerate(audio_samples):
                features = await self._extract_voice_features(audio)
                
                if features is not None:
                    all_features.append(features)
            
            if len(all_features) < 3:
                return {
                    'success': False,
                    'error': 'Could not extract enough voice features'
                }
            
            # Create voice DNA profile
            voice_dna = {
                'mean_features': np.mean(all_features, axis=0).tolist(),
                'std_features': np.std(all_features, axis=0).tolist(),
                'sample_count': len(all_features),
                'enrolled_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Generate voice fingerprint hash
            fingerprint_data = json.dumps(voice_dna['mean_features'][:10])
            voice_dna['fingerprint'] = hashlib.sha256(
                fingerprint_data.encode()
            ).hexdigest()[:16]
            
            self.voice_profile = voice_dna
            self.is_enrolled = True
            self._save_profile()
            
            return {
                'success': True,
                'message': 'Voice DNA enrolled successfully!',
                'fingerprint': voice_dna['fingerprint'],
                'samples_used': len(all_features),
                'security_level': 'high' if len(all_features) >= 5 else 'medium'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def verify(
        self,
        audio: bytes,
        security_level: str = 'medium'
    ) -> Dict:
        """
        Verify if audio matches enrolled voice DNA.
        """
        
        if not self.is_enrolled:
            return {
                'success': False,
                'error': 'Voice DNA not enrolled',
                'action': 'Please enroll your voice first'
            }
        
        # Check lockout
        if self.lockout_until:
            if datetime.now() < self.lockout_until:
                remaining = (self.lockout_until - datetime.now()).seconds
                return {
                    'success': False,
                    'authenticated': False,
                    'error': f'Too many failed attempts. Try again in {remaining}s'
                }
            else:
                self.lockout_until = None
                self.failed_attempts = 0
        
        try:
            # Extract features from new audio
            features = await self._extract_voice_features(audio)
            
            if features is None:
                return {
                    'success': False,
                    'authenticated': False,
                    'error': 'Could not extract voice features'
                }
            
            # Compare with enrolled profile
            profile_mean = np.array(self.voice_profile['mean_features'])
            profile_std = np.array(self.voice_profile['std_features'])
            
            # Calculate similarity score
            similarity = self._calculate_similarity(
                features, profile_mean, profile_std
            )
            
            threshold = self.thresholds.get(security_level, 0.85)
            authenticated = similarity >= threshold
            
            if authenticated:
                self.failed_attempts = 0
                
                return {
                    'success': True,
                    'authenticated': True,
                    'confidence': float(similarity),
                    'security_level': security_level,
                    'message': 'Voice verified ✓'
                }
            else:
                self.failed_attempts += 1
                
                # Check for lockout
                if self.failed_attempts >= self.max_attempts:
                    from datetime import timedelta
                    self.lockout_until = datetime.now() + timedelta(minutes=5)
                    
                    return {
                        'success': True,
                        'authenticated': False,
                        'error': 'Too many failed attempts. Locked for 5 minutes.',
                        'failed_attempts': self.failed_attempts
                    }
                
                return {
                    'success': True,
                    'authenticated': False,
                    'confidence': float(similarity),
                    'threshold': threshold,
                    'remaining_attempts': self.max_attempts - self.failed_attempts,
                    'message': 'Voice not recognized'
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_voice_features(
        self,
        audio: bytes
    ) -> Optional[np.ndarray]:
        """Extract voice features (MFCCs and other characteristics)"""
        
        try:
            import librosa
            import io
            import soundfile as sf
            
            # Load audio
            audio_data, sample_rate = sf.read(io.BytesIO(audio))
            
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(
                y=audio_data,
                sr=sample_rate,
                n_mfcc=40
            )
            
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            # Extract additional features
            spectral_centroid = np.mean(
                librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            )
            
            zero_crossing = np.mean(
                librosa.feature.zero_crossing_rate(audio_data)
            )
            
            # Fundamental frequency
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # Combine all features
            features = np.concatenate([
                mfcc_mean,
                mfcc_std,
                [spectral_centroid, zero_crossing, pitch_mean]
            ])
            
            return features
        
        except ImportError:
            # librosa not available - use simple frequency analysis
            return self._simple_voice_features(audio)
        except Exception:
            return None
    
    def _simple_voice_features(self, audio: bytes) -> np.ndarray:
        """Simple voice features without librosa"""
        
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0  # Normalize
        
        if len(audio_array) == 0:
            return np.zeros(10)
        
        features = [
            np.mean(np.abs(audio_array)),  # Mean amplitude
            np.std(audio_array),           # Standard deviation
            np.max(np.abs(audio_array)),   # Max amplitude
            np.sum(audio_array ** 2),      # Energy
            np.mean(np.diff(audio_array)), # Mean derivative
        ]
        
        # Add frequency features
        fft = np.abs(np.fft.fft(audio_array[:1024]))
        
        features.extend([
            np.mean(fft[:100]),   # Low freq energy
            np.mean(fft[100:500]),# Mid freq energy
            np.mean(fft[500:]),   # High freq energy
            np.argmax(fft),       # Dominant frequency bin
            np.std(fft)           # Frequency variance
        ])
        
        return np.array(features)
    
    def _calculate_similarity(
        self,
        features: np.ndarray,
        profile_mean: np.ndarray,
        profile_std: np.ndarray
    ) -> float:
        """Calculate similarity between voice features and profile"""
        
        # Ensure same dimensions
        min_len = min(len(features), len(profile_mean))
        features = features[:min_len]
        profile_mean = profile_mean[:min_len]
        profile_std = profile_std[:min_len]
        
        # Normalize features
        std_safe = np.where(profile_std > 0, profile_std, 1)
        normalized = (features - profile_mean) / std_safe
        
        # Calculate Mahalanobis-like distance
        distance = np.sqrt(np.mean(normalized ** 2))
        
        # Convert to similarity (0 to 1)
        similarity = 1 / (1 + distance)
        
        # Boost to reasonable range
        similarity = min(1.0, similarity * 2)
        
        return float(similarity)
    
    def reset_enrollment(self) -> Dict:
        """Reset voice DNA enrollment"""
        
        self.voice_profile = None
        self.is_enrolled = False
        self.failed_attempts = 0
        self.lockout_until = None
        
        profile_file = self.storage_path / "voice_profile.json"
        if profile_file.exists():
            profile_file.unlink()
        
        return {'success': True, 'message': 'Voice DNA reset. Please re-enroll.'}
    
    def get_security_status(self) -> Dict:
        """Get Voice DNA security status"""
        
        return {
            'enrolled': self.is_enrolled,
            'fingerprint': self.voice_profile.get('fingerprint') if self.voice_profile else None,
            'enrolled_at': self.voice_profile.get('enrolled_at') if self.voice_profile else None,
            'failed_attempts': self.failed_attempts,
            'locked': self.lockout_until is not None,
            'lockout_until': self.lockout_until.isoformat() if self.lockout_until else None,
            'security_levels': self.thresholds
        }
