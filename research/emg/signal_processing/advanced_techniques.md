# Advanced EMG Signal Processing Techniques

## Overview

This document covers advanced signal processing techniques specifically for EMG signals in silent speech recognition and brain-computer interface applications.

## Preprocessing Pipeline

### 1. Artifact Removal

**Motion Artifacts**:
- **Source**: Electrode movement, cable motion, body movement
- **Characteristics**: Low frequency (<10 Hz), high amplitude
- **Removal**: High-pass filtering (>10-20 Hz), adaptive filtering

**Power Line Interference**:
- **Source**: 50/60 Hz electrical noise from power lines
- **Characteristics**: Narrow-band sinusoidal interference
- **Removal**: Notch filtering, adaptive line enhancers

**ECG Artifacts**:
- **Source**: Cardiac electrical activity
- **Characteristics**: ~1 Hz repetition rate, QRS complex pattern
- **Removal**: Template subtraction, ICA, adaptive filtering

**EOG Artifacts**:
- **Source**: Eye movement and blinking
- **Characteristics**: Low frequency, large amplitude
- **Removal**: Regression-based removal, ICA

### 2. Advanced Filtering Techniques

**Adaptive Filtering**:
```python
# Least Mean Squares (LMS) adaptive filter
def lms_filter(signal, reference, mu=0.01, order=32):
    """
    LMS adaptive filter for noise cancellation
    
    Args:
        signal: Primary input (EMG + noise)
        reference: Reference noise signal
        mu: Step size parameter
        order: Filter order
    """
    n_samples = len(signal)
    w = np.zeros(order)  # Filter weights
    filtered_signal = np.zeros(n_samples)
    
    for i in range(order, n_samples):
        x = reference[i-order:i][::-1]  # Reference vector
        y = np.dot(w, x)  # Filter output
        e = signal[i] - y  # Error signal
        w += mu * e * x  # Weight update
        filtered_signal[i] = e
    
    return filtered_signal
```

**Kalman Filtering**:
```python
# Kalman filter for EMG signal enhancement
class EMGKalmanFilter:
    def __init__(self, process_noise=1e-5, measurement_noise=1e-1):
        self.Q = process_noise  # Process noise covariance
        self.R = measurement_noise  # Measurement noise covariance
        self.P = 1.0  # Error covariance
        self.x = 0.0  # State estimate
        
    def update(self, measurement):
        # Prediction step
        self.P += self.Q
        
        # Update step
        K = self.P / (self.P + self.R)  # Kalman gain
        self.x += K * (measurement - self.x)
        self.P *= (1 - K)
        
        return self.x
```

**Wavelet Denoising**:
```python
import pywt

def wavelet_denoise(signal, wavelet='db4', threshold_mode='soft'):
    """
    Wavelet-based denoising for EMG signals
    
    Args:
        signal: Input EMG signal
        wavelet: Wavelet type
        threshold_mode: 'soft' or 'hard' thresholding
    """
    # Decompose signal
    coeffs = pywt.wavedec(signal, wavelet, level=6)
    
    # Estimate noise level using median absolute deviation
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    
    # Calculate threshold
    threshold = sigma * np.sqrt(2 * np.log(len(signal)))
    
    # Apply thresholding
    coeffs_thresh = list(coeffs)
    coeffs_thresh[1:] = [pywt.threshold(detail, threshold, threshold_mode) 
                         for detail in coeffs_thresh[1:]]
    
    # Reconstruct signal
    return pywt.waverec(coeffs_thresh, wavelet)
```

## Feature Extraction Methods

### 1. Time-Domain Features

**Advanced Statistical Features**:
```python
def extract_time_features(signal, window_size=250):
    """Extract comprehensive time-domain features"""
    features = {}
    
    # Basic statistical features
    features['mean'] = np.mean(signal)
    features['std'] = np.std(signal)
    features['var'] = np.var(signal)
    features['rms'] = np.sqrt(np.mean(signal**2))
    features['mav'] = np.mean(np.abs(signal))
    
    # Higher-order statistics
    features['skewness'] = scipy.stats.skew(signal)
    features['kurtosis'] = scipy.stats.kurtosis(signal)
    
    # Complexity measures
    features['zero_crossings'] = np.sum(np.diff(np.sign(signal)) != 0)
    features['slope_sign_changes'] = np.sum(np.diff(np.sign(np.diff(signal))) != 0)
    features['waveform_length'] = np.sum(np.abs(np.diff(signal)))
    
    # Hjorth parameters
    diff1 = np.diff(signal)
    diff2 = np.diff(diff1)
    features['hjorth_activity'] = np.var(signal)
    features['hjorth_mobility'] = np.sqrt(np.var(diff1) / np.var(signal))
    features['hjorth_complexity'] = (np.sqrt(np.var(diff2) / np.var(diff1)) / 
                                   features['hjorth_mobility'])
    
    return features
```

**Autoregressive (AR) Features**:
```python
from scipy.signal import lfilter

def ar_features(signal, order=4):
    """Extract autoregressive model coefficients as features"""
    # Estimate AR coefficients using Yule-Walker method
    ar_coeffs = np.correlate(signal, signal, mode='full')
    ar_coeffs = ar_coeffs[ar_coeffs.size // 2:]
    
    # Solve Yule-Walker equations
    R = np.array([ar_coeffs[abs(i-j)] for i in range(order) for j in range(order)])
    R = R.reshape(order, order)
    r = ar_coeffs[1:order+1]
    
    try:
        ar_params = np.linalg.solve(R, r)
        return ar_params
    except np.linalg.LinAlgError:
        return np.zeros(order)
```

### 2. Frequency-Domain Features

**Power Spectral Density Analysis**:
```python
def extract_frequency_features(signal, fs=1000):
    """Extract comprehensive frequency-domain features"""
    features = {}
    
    # Compute power spectral density
    freqs, psd = scipy.signal.welch(signal, fs=fs, nperseg=256)
    
    # Frequency bands for EMG
    bands = {
        'low': (20, 80),
        'mid': (80, 150),
        'high': (150, 300),
        'very_high': (300, 500)
    }
    
    total_power = np.sum(psd)
    
    for band_name, (low_freq, high_freq) in bands.items():
        band_mask = (freqs >= low_freq) & (freqs <= high_freq)
        band_power = np.sum(psd[band_mask])
        features[f'{band_name}_power'] = band_power
        features[f'{band_name}_power_ratio'] = band_power / total_power
    
    # Spectral moments
    features['mean_freq'] = np.sum(freqs * psd) / total_power
    features['median_freq'] = freqs[np.where(np.cumsum(psd) >= total_power/2)[0][0]]
    features['peak_freq'] = freqs[np.argmax(psd)]
    
    # Spectral edge frequency (95% of power)
    features['spectral_edge'] = freqs[np.where(np.cumsum(psd) >= 0.95*total_power)[0][0]]
    
    # Spectral entropy
    psd_norm = psd / np.sum(psd)
    features['spectral_entropy'] = -np.sum(psd_norm * np.log2(psd_norm + 1e-12))
    
    return features
```

**Cepstral Analysis**:
```python
def cepstral_features(signal, n_coeffs=12):
    """Extract cepstral coefficients (similar to MFCC for speech)"""
    # Compute power spectrum
    fft = np.fft.fft(signal)
    power_spectrum = np.abs(fft)**2
    
    # Apply mel-scale filtering (adapted for EMG frequencies)
    mel_filters = create_mel_filterbank(len(power_spectrum)//2, 20, 500, n_coeffs)
    mel_spectrum = np.dot(mel_filters, power_spectrum[:len(power_spectrum)//2])
    
    # Log and DCT
    log_mel = np.log(mel_spectrum + 1e-12)
    cepstral_coeffs = scipy.fft.dct(log_mel, type=2, norm='ortho')
    
    return cepstral_coeffs

def create_mel_filterbank(nfft, low_freq, high_freq, n_filters):
    """Create mel-scale filterbank for EMG signals"""
    # Convert to mel scale
    low_mel = 2595 * np.log10(1 + low_freq / 700)
    high_mel = 2595 * np.log10(1 + high_freq / 700)
    
    # Create equally spaced mel points
    mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
    hz_points = 700 * (10**(mel_points / 2595) - 1)
    
    # Create filterbank
    filterbank = np.zeros((n_filters, nfft))
    for i in range(n_filters):
        left = int(hz_points[i] * nfft / (high_freq * 2))
        center = int(hz_points[i+1] * nfft / (high_freq * 2))
        right = int(hz_points[i+2] * nfft / (high_freq * 2))
        
        for j in range(left, center):
            filterbank[i, j] = (j - left) / (center - left)
        for j in range(center, right):
            filterbank[i, j] = (right - j) / (right - center)
    
    return filterbank
```

### 3. Time-Frequency Features

**Short-Time Fourier Transform (STFT)**:
```python
def stft_features(signal, fs=1000, window_size=128, overlap=64):
    """Extract features from STFT representation"""
    f, t, Zxx = scipy.signal.stft(signal, fs=fs, nperseg=window_size, 
                                  noverlap=overlap)
    
    # Magnitude spectrogram
    magnitude = np.abs(Zxx)
    
    features = {}
    
    # Spectral centroid over time
    spectral_centroids = np.sum(f[:, np.newaxis] * magnitude, axis=0) / np.sum(magnitude, axis=0)
    features['spectral_centroid_mean'] = np.mean(spectral_centroids)
    features['spectral_centroid_std'] = np.std(spectral_centroids)
    
    # Spectral rolloff over time
    cumsum_magnitude = np.cumsum(magnitude, axis=0)
    total_magnitude = np.sum(magnitude, axis=0)
    rolloff_indices = np.argmax(cumsum_magnitude >= 0.85 * total_magnitude, axis=0)
    spectral_rolloff = f[rolloff_indices]
    features['spectral_rolloff_mean'] = np.mean(spectral_rolloff)
    features['spectral_rolloff_std'] = np.std(spectral_rolloff)
    
    # Spectral flux (measure of spectral change)
    spectral_flux = np.sum(np.diff(magnitude, axis=1)**2, axis=0)
    features['spectral_flux_mean'] = np.mean(spectral_flux)
    features['spectral_flux_std'] = np.std(spectral_flux)
    
    return features
```

**Continuous Wavelet Transform (CWT)**:
```python
def cwt_features(signal, fs=1000, scales=None):
    """Extract features from continuous wavelet transform"""
    if scales is None:
        scales = np.arange(1, 128)
    
    # Compute CWT using Morlet wavelet
    coefficients, frequencies = pywt.cwt(signal, scales, 'morl', 1/fs)
    
    features = {}
    
    # Energy in different frequency bands
    for i, freq_range in enumerate([(20, 50), (50, 100), (100, 200), (200, 400)]):
        freq_mask = (frequencies >= freq_range[0]) & (frequencies <= freq_range[1])
        band_energy = np.sum(np.abs(coefficients[freq_mask, :])**2)
        features[f'cwt_energy_band_{i}'] = band_energy
    
    # Wavelet entropy
    total_energy = np.sum(np.abs(coefficients)**2)
    relative_energies = np.sum(np.abs(coefficients)**2, axis=1) / total_energy
    features['wavelet_entropy'] = -np.sum(relative_energies * np.log2(relative_energies + 1e-12))
    
    # Dominant frequency over time
    dominant_freqs = frequencies[np.argmax(np.abs(coefficients), axis=0)]
    features['dominant_freq_mean'] = np.mean(dominant_freqs)
    features['dominant_freq_std'] = np.std(dominant_freqs)
    
    return features
```

## Advanced Classification Techniques

### 1. Deep Learning Approaches

**Convolutional Neural Network for EMG**:
```python
import tensorflow as tf

def create_emg_cnn(input_shape, num_classes):
    """Create CNN for EMG signal classification"""
    model = tf.keras.Sequential([
        # First convolutional block
        tf.keras.layers.Conv1D(32, 3, activation='relu', input_shape=input_shape),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(2),
        tf.keras.layers.Dropout(0.25),
        
        # Second convolutional block
        tf.keras.layers.Conv1D(64, 3, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(2),
        tf.keras.layers.Dropout(0.25),
        
        # Third convolutional block
        tf.keras.layers.Conv1D(128, 3, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(2),
        tf.keras.layers.Dropout(0.25),
        
        # Dense layers
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    return model
```

**LSTM for Temporal Modeling**:
```python
def create_emg_lstm(input_shape, num_classes):
    """Create LSTM for EMG sequence classification"""
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, return_sequences=True, input_shape=input_shape),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(32, return_sequences=False),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    return model
```

### 2. Ensemble Methods

**Multi-Channel Fusion**:
```python
class MultiChannelEMGClassifier:
    def __init__(self, n_channels=4):
        self.n_channels = n_channels
        self.channel_classifiers = []
        self.fusion_classifier = None
        
    def train(self, X_multichannel, y):
        """Train individual channel classifiers and fusion model"""
        channel_predictions = []
        
        # Train classifier for each channel
        for ch in range(self.n_channels):
            clf = RandomForestClassifier(n_estimators=100)
            clf.fit(X_multichannel[:, ch, :], y)
            self.channel_classifiers.append(clf)
            
            # Get predictions for fusion training
            pred_proba = clf.predict_proba(X_multichannel[:, ch, :])
            channel_predictions.append(pred_proba)
        
        # Train fusion classifier
        fusion_features = np.concatenate(channel_predictions, axis=1)
        self.fusion_classifier = LogisticRegression()
        self.fusion_classifier.fit(fusion_features, y)
    
    def predict(self, X_multichannel):
        """Predict using ensemble of channel classifiers"""
        channel_predictions = []
        
        for ch in range(self.n_channels):
            pred_proba = self.channel_classifiers[ch].predict_proba(X_multichannel[:, ch, :])
            channel_predictions.append(pred_proba)
        
        fusion_features = np.concatenate(channel_predictions, axis=1)
        return self.fusion_classifier.predict(fusion_features)
```

## Real-Time Processing Considerations

### 1. Computational Efficiency

**Sliding Window Processing**:
```python
class RealTimeEMGProcessor:
    def __init__(self, window_size=250, overlap=125, fs=1000):
        self.window_size = window_size
        self.overlap = overlap
        self.fs = fs
        self.buffer = deque(maxlen=window_size)
        self.feature_extractor = FeatureExtractor()
        self.classifier = None
        
    def process_sample(self, sample):
        """Process single EMG sample in real-time"""
        self.buffer.append(sample)
        
        if len(self.buffer) == self.window_size:
            # Extract features from current window
            window_data = np.array(self.buffer)
            features = self.feature_extractor.extract(window_data)
            
            # Classify if model is available
            if self.classifier is not None:
                prediction = self.classifier.predict([features])
                return prediction[0]
        
        return None
    
    def update_buffer(self, new_samples):
        """Update buffer with multiple samples"""
        for sample in new_samples:
            result = self.process_sample(sample)
            if result is not None:
                yield result
```

### 2. Adaptive Learning

**Online Learning with Concept Drift**:
```python
class AdaptiveEMGClassifier:
    def __init__(self, base_classifier, adaptation_rate=0.1):
        self.base_classifier = base_classifier
        self.adaptation_rate = adaptation_rate
        self.performance_history = deque(maxlen=100)
        
    def predict_and_adapt(self, X, y_true=None):
        """Predict and adapt based on feedback"""
        predictions = self.base_classifier.predict(X)
        
        if y_true is not None:
            # Calculate current performance
            accuracy = np.mean(predictions == y_true)
            self.performance_history.append(accuracy)
            
            # Detect concept drift
            if len(self.performance_history) >= 50:
                recent_performance = np.mean(list(self.performance_history)[-25:])
                historical_performance = np.mean(list(self.performance_history)[:-25])
                
                if recent_performance < historical_performance - 0.1:
                    # Concept drift detected, retrain with recent data
                    self.base_classifier.partial_fit(X, y_true)
        
        return predictions
```

## Quality Assessment and Validation

### 1. Signal Quality Metrics

**Signal-to-Noise Ratio (SNR)**:
```python
def calculate_snr(signal, noise_freq_range=(400, 500), fs=1000):
    """Calculate SNR for EMG signal"""
    # Compute power spectral density
    freqs, psd = scipy.signal.welch(signal, fs=fs)
    
    # Signal power (EMG frequency range: 20-400 Hz)
    signal_mask = (freqs >= 20) & (freqs <= 400)
    signal_power = np.sum(psd[signal_mask])
    
    # Noise power (high frequency range)
    noise_mask = (freqs >= noise_freq_range[0]) & (freqs <= noise_freq_range[1])
    noise_power = np.sum(psd[noise_mask])
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db
```

**Electrode Contact Quality**:
```python
def assess_electrode_quality(signal, fs=1000):
    """Assess electrode-skin contact quality"""
    # Check for saturation
    max_val = np.max(np.abs(signal))
    saturation_ratio = np.sum(np.abs(signal) > 0.95 * max_val) / len(signal)
    
    # Check for excessive noise
    high_freq_power = np.sum(np.abs(np.fft.fft(signal)[fs//2:]))**2
    total_power = np.sum(np.abs(np.fft.fft(signal)))**2
    noise_ratio = high_freq_power / total_power
    
    # Check for baseline drift
    baseline_trend = np.polyfit(np.arange(len(signal)), signal, 1)[0]
    
    quality_score = 1.0
    if saturation_ratio > 0.01:
        quality_score -= 0.3
    if noise_ratio > 0.2:
        quality_score -= 0.3
    if abs(baseline_trend) > 0.1:
        quality_score -= 0.2
    
    return max(0, quality_score)
```

### 2. Cross-Validation Strategies

**Subject-Independent Validation**:
```python
def subject_independent_cv(X, y, subjects, n_folds=5):
    """Cross-validation leaving out entire subjects"""
    unique_subjects = np.unique(subjects)
    fold_size = len(unique_subjects) // n_folds
    
    results = []
    
    for fold in range(n_folds):
        # Select test subjects for this fold
        start_idx = fold * fold_size
        end_idx = start_idx + fold_size if fold < n_folds - 1 else len(unique_subjects)
        test_subjects = unique_subjects[start_idx:end_idx]
        
        # Split data
        test_mask = np.isin(subjects, test_subjects)
        train_mask = ~test_mask
        
        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]
        
        # Train and evaluate
        classifier = RandomForestClassifier(n_estimators=100)
        classifier.fit(X_train, y_train)
        accuracy = classifier.score(X_test, y_test)
        
        results.append(accuracy)
    
    return np.mean(results), np.std(results)
```

## References and Further Reading

1. **Merletti, R., & Farina, D. (2016)**. Surface Electromyography: Physiology, Engineering, and Applications. John Wiley & Sons.

2. **Phinyomark, A., Phukpattaranont, P., & Limsakul, C. (2012)**. Feature reduction and selection for EMG signal classification. Expert Systems with Applications, 39(8), 7420-7431.

3. **Hudgins, B., Parker, P., & Scott, R. N. (1993)**. A new strategy for multifunction myoelectric control. IEEE Transactions on Biomedical Engineering, 40(1), 82-94.

4. **Englehart, K., & Hudgins, B. (2003)**. A robust, real-time control scheme for multifunction myoelectric control. IEEE Transactions on Biomedical Engineering, 50(7), 848-854.

5. **Scheme, E., & Englehart, K. (2011)**. Electromyogram pattern recognition for control of powered upper-limb prostheses: state of the art and challenges for clinical use. Journal of Rehabilitation Research & Development, 48(6), 643-660.

6. **Farina, D., Jiang, N., Rehbaum, H., Holobar, A., Graimann, B., Dietl, H., & Aszmann, O. C. (2014)**. The extraction of neural information from the surface EMG for the control of upper-limb prostheses: emerging avenues and challenges. IEEE Transactions on Neural Systems and Rehabilitation Engineering, 22(4), 797-809.

7. **Kapur, A., Kapur, S., & Maes, P. (2018)**. AlterEgo: A personalized wearable silent speech interface. In Proceedings of the 23rd International Conference on Intelligent User Interfaces (pp. 43-53).

8. **Jorgensen, C., Lee, D. D., & Agabon, S. (2003)**. Sub auditory speech recognition based on EMG signals. In Proceedings of the International Joint Conference on Neural Networks (Vol. 4, pp. 3128-3133).
