# Available EMG Datasets for Silent Speech Research

## Overview

This document catalogs publicly available EMG datasets that can be used for silent speech recognition research, training machine learning models, and benchmarking algorithms. These datasets provide valuable training data for developing and validating EMG-based silent speech systems.

## Public EMG Datasets

### 1. CSL-EMG_Array Corpus

**Source**: University of Bremen, Germany
**Description**: Comprehensive EMG dataset for silent speech recognition
**Access**: Available upon request for research purposes

**Specifications**:
- **Subjects**: 45 participants
- **Sessions**: Multiple recording sessions per subject
- **Channels**: 8-channel EMG array
- **Sampling Rate**: 600 Hz
- **Vocabulary**: German phonemes and words
- **Duration**: ~20 hours total recording time

**Content**:
- Parallel EMG and audio recordings
- Silent speech (EMG only) recordings
- Phoneme-level annotations
- Word-level annotations
- Speaker demographics

**File Format**:
- EMG data: MATLAB .mat files
- Audio: WAV format
- Annotations: TextGrid format
- Metadata: CSV files

**Usage Example**:
```python
import scipy.io
import numpy as np

def load_csl_emg_data(file_path):
    """Load CSL-EMG dataset"""
    data = scipy.io.loadmat(file_path)
    
    emg_signals = data['emg_data']  # Shape: (n_samples, n_channels)
    timestamps = data['timestamps']
    labels = data['phoneme_labels']
    
    return {
        'emg': emg_signals,
        'timestamps': timestamps,
        'labels': labels,
        'sampling_rate': 600
    }

# Example usage
dataset = load_csl_emg_data('csl_emg_subject01_session01.mat')
print(f"EMG shape: {dataset['emg'].shape}")
print(f"Labels: {len(dataset['labels'])}")
```

### 2. EMG-UKA Dataset

**Source**: University of Karlsruhe, Germany
**Description**: Multi-modal dataset with EMG, EEG, and audio
**Access**: Research license required

**Specifications**:
- **Subjects**: 12 participants
- **Modalities**: EMG (8 channels), EEG (64 channels), Audio
- **Sampling Rate**: 1000 Hz (EMG), 1000 Hz (EEG)
- **Languages**: German, English
- **Tasks**: Reading, silent reading, imagination

**Content**:
- Overt speech recordings
- Silent speech (subvocalization)
- Imagined speech
- Rest periods for baseline
- Synchronized multi-modal data

### 3. Silent Speech EMG Database (SSED)

**Source**: Multiple research institutions
**Description**: Collaborative dataset for silent speech research
**Access**: Open access with registration

**Specifications**:
- **Subjects**: 25 participants
- **Channels**: 4-16 EMG channels (variable)
- **Sampling Rate**: 1000-2000 Hz
- **Vocabulary**: English words and phrases
- **Conditions**: Multiple recording environments

**Features**:
- Cross-subject variability analysis
- Different electrode configurations
- Environmental noise conditions
- Long-term stability studies

### 4. MyoVoice Dataset

**Source**: Facebook Reality Labs (Meta)
**Description**: High-density EMG for silent speech
**Access**: Limited research access

**Specifications**:
- **Subjects**: 10 participants
- **Channels**: 64-channel EMG array
- **Sampling Rate**: 2000 Hz
- **Vocabulary**: English sentences
- **Duration**: 5+ hours per subject

**Unique Features**:
- High spatial resolution
- Wrist-worn form factor
- Real-time processing benchmarks
- Consumer device simulation

### 5. BioPatRec EMG Database

**Source**: Chalmers University of Technology
**Description**: General EMG database with speech components
**Access**: Open source

**Specifications**:
- **Subjects**: 20+ participants
- **Channels**: 8-12 EMG channels
- **Applications**: Prosthetic control, speech recognition
- **Format**: MATLAB compatible

**Content**:
- Hand/arm movements
- Facial expressions
- Speech-related muscle activity
- Pattern recognition benchmarks

## Synthetic and Augmented Datasets

### 1. EMG-GAN Generated Data

**Description**: Synthetically generated EMG signals using GANs
**Purpose**: Data augmentation for training

**Advantages**:
- Unlimited data generation
- Controlled noise conditions
- Balanced class distributions
- Privacy preservation

**Implementation**:
```python
import tensorflow as tf

class EMGDataAugmentation:
    def __init__(self, original_data):
        self.original_data = original_data
        self.generator = self.build_generator()
        
    def build_generator(self):
        """Build GAN generator for EMG data augmentation"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(100,)),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.Dense(1000, activation='tanh'),  # EMG signal length
            tf.keras.layers.Reshape((1000, 1))
        ])
        return model
    
    def generate_synthetic_emg(self, n_samples=1000):
        """Generate synthetic EMG signals"""
        noise = tf.random.normal([n_samples, 100])
        synthetic_emg = self.generator(noise)
        return synthetic_emg.numpy()
    
    def augment_dataset(self, augmentation_factor=2):
        """Augment existing dataset with synthetic data"""
        n_synthetic = len(self.original_data) * augmentation_factor
        synthetic_data = self.generate_synthetic_emg(n_synthetic)
        
        augmented_dataset = np.concatenate([
            self.original_data,
            synthetic_data
        ], axis=0)
        
        return augmented_dataset
```

### 2. Noise Augmentation

**Purpose**: Improve robustness to real-world conditions

**Techniques**:
- Gaussian noise addition
- Power line interference simulation
- Motion artifact injection
- Electrode impedance variation

```python
def augment_emg_with_noise(emg_signal, noise_types=['gaussian', 'powerline', 'motion']):
    """Apply various noise types to EMG signals"""
    augmented_signals = []
    
    for noise_type in noise_types:
        if noise_type == 'gaussian':
            # Add Gaussian noise (SNR = 20 dB)
            signal_power = np.mean(emg_signal**2)
            noise_power = signal_power / 100  # 20 dB SNR
            noise = np.random.normal(0, np.sqrt(noise_power), emg_signal.shape)
            noisy_signal = emg_signal + noise
            
        elif noise_type == 'powerline':
            # Add 60 Hz power line interference
            t = np.arange(len(emg_signal)) / 1000  # Assuming 1000 Hz sampling
            powerline = 0.1 * np.sin(2 * np.pi * 60 * t)
            noisy_signal = emg_signal + powerline
            
        elif noise_type == 'motion':
            # Add low-frequency motion artifacts
            motion_freq = np.random.uniform(0.5, 5)  # 0.5-5 Hz
            t = np.arange(len(emg_signal)) / 1000
            motion_artifact = 0.2 * np.sin(2 * np.pi * motion_freq * t)
            noisy_signal = emg_signal + motion_artifact
            
        augmented_signals.append(noisy_signal)
    
    return augmented_signals
```

## Dataset Preprocessing Pipelines

### 1. Standardized Preprocessing

```python
class EMGDatasetPreprocessor:
    def __init__(self, sampling_rate=1000):
        self.sampling_rate = sampling_rate
        self.filters_designed = False
        
    def design_filters(self):
        """Design standard EMG filters"""
        from scipy.signal import butter, iirnotch
        
        # Band-pass filter (20-500 Hz)
        nyquist = self.sampling_rate / 2
        low = 20 / nyquist
        high = 500 / nyquist
        self.bp_b, self.bp_a = butter(4, [low, high], btype='band')
        
        # Notch filter (60 Hz)
        self.notch_b, self.notch_a = iirnotch(60, 30, self.sampling_rate)
        
        self.filters_designed = True
    
    def preprocess_signal(self, emg_signal):
        """Apply standard preprocessing pipeline"""
        if not self.filters_designed:
            self.design_filters()
        
        # Apply band-pass filter
        filtered = filtfilt(self.bp_b, self.bp_a, emg_signal)
        
        # Apply notch filter
        filtered = filtfilt(self.notch_b, self.notch_a, filtered)
        
        # Rectification
        rectified = np.abs(filtered)
        
        # Normalization (z-score)
        normalized = (rectified - np.mean(rectified)) / np.std(rectified)
        
        return normalized
    
    def segment_signal(self, signal, window_size=250, overlap=125):
        """Segment signal into overlapping windows"""
        segments = []
        step_size = window_size - overlap
        
        for i in range(0, len(signal) - window_size + 1, step_size):
            segment = signal[i:i + window_size]
            segments.append(segment)
        
        return np.array(segments)
    
    def extract_features(self, signal_segments):
        """Extract features from signal segments"""
        features = []
        
        for segment in signal_segments:
            # Time-domain features
            rms = np.sqrt(np.mean(segment**2))
            mav = np.mean(np.abs(segment))
            var = np.var(segment)
            
            # Frequency-domain features
            fft = np.fft.fft(segment)
            freqs = np.fft.fftfreq(len(segment), 1/self.sampling_rate)
            
            # Power in different frequency bands
            low_power = np.sum(np.abs(fft[(freqs >= 20) & (freqs <= 80)])**2)
            mid_power = np.sum(np.abs(fft[(freqs >= 80) & (freqs <= 150)])**2)
            high_power = np.sum(np.abs(fft[(freqs >= 150) & (freqs <= 300)])**2)
            
            feature_vector = [rms, mav, var, low_power, mid_power, high_power]
            features.append(feature_vector)
        
        return np.array(features)
```

### 2. Cross-Subject Normalization

```python
def normalize_across_subjects(datasets):
    """Normalize EMG data across multiple subjects"""
    
    # Collect statistics across all subjects
    all_signals = []
    for subject_data in datasets:
        all_signals.extend(subject_data['emg_signals'])
    
    all_signals = np.concatenate(all_signals, axis=0)
    
    # Calculate global statistics
    global_mean = np.mean(all_signals, axis=0)
    global_std = np.std(all_signals, axis=0)
    
    # Normalize each subject's data
    normalized_datasets = []
    for subject_data in datasets:
        normalized_signals = []
        for signal in subject_data['emg_signals']:
            normalized = (signal - global_mean) / global_std
            normalized_signals.append(normalized)
        
        normalized_data = subject_data.copy()
        normalized_data['emg_signals'] = normalized_signals
        normalized_datasets.append(normalized_data)
    
    return normalized_datasets
```

## Data Collection Guidelines

### 1. Experimental Protocol

**Session Structure**:
```
Recommended EMG Data Collection Protocol:

1. Setup Phase (10 minutes):
   - Electrode placement and impedance check
   - System calibration
   - Participant briefing

2. Baseline Recording (5 minutes):
   - Rest condition (no muscle activity)
   - Breathing normally
   - Eyes open/closed conditions

3. Training Data Collection (30-45 minutes):
   - Phoneme repetitions (10x each)
   - Word repetitions (5x each)
   - Sentence reading (3x each)
   - Silent speech practice

4. Validation Data Collection (15 minutes):
   - Novel words/sentences
   - Different speaking rates
   - Fatigue assessment

5. Cleanup and Documentation (5 minutes):
   - Electrode removal
   - Data quality check
   - Session notes
```

**Quality Control Checklist**:
- [ ] Electrode impedance < 10 kΩ (wet) or < 100 kΩ (dry)
- [ ] Signal-to-noise ratio > 20 dB
- [ ] No saturation or clipping
- [ ] Consistent electrode placement
- [ ] Proper grounding and shielding
- [ ] Synchronized timing across channels

### 2. Annotation Standards

**Phoneme-Level Annotation**:
```python
class EMGAnnotation:
    def __init__(self):
        self.phoneme_set = [
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'B', 'CH', 'D', 'DH',
            'EH', 'ER', 'EY', 'F', 'G', 'HH', 'IH', 'IY', 'JH', 'K',
            'L', 'M', 'N', 'NG', 'OW', 'OY', 'P', 'R', 'S', 'SH',
            'T', 'TH', 'UH', 'UW', 'V', 'W', 'Y', 'Z', 'ZH'
        ]
        
    def create_annotation(self, text, start_time, end_time):
        """Create phoneme-level annotation"""
        # Convert text to phonemes (simplified)
        phonemes = self.text_to_phonemes(text)
        
        # Distribute timing across phonemes
        duration = end_time - start_time
        phoneme_duration = duration / len(phonemes)
        
        annotations = []
        for i, phoneme in enumerate(phonemes):
            annotation = {
                'phoneme': phoneme,
                'start_time': start_time + i * phoneme_duration,
                'end_time': start_time + (i + 1) * phoneme_duration,
                'confidence': 1.0
            }
            annotations.append(annotation)
        
        return annotations
    
    def text_to_phonemes(self, text):
        """Convert text to phoneme sequence (simplified)"""
        # This would typically use a phonetic dictionary
        # For demonstration, using a simple mapping
        phoneme_map = {
            'hello': ['HH', 'EH', 'L', 'OW'],
            'world': ['W', 'ER', 'L', 'D'],
            'speech': ['S', 'P', 'IY', 'CH'],
            'recognition': ['R', 'EH', 'K', 'AH', 'G', 'N', 'IH', 'SH', 'AH', 'N']
        }
        
        words = text.lower().split()
        phonemes = []
        for word in words:
            if word in phoneme_map:
                phonemes.extend(phoneme_map[word])
        
        return phonemes
```

## Dataset Evaluation Metrics

### 1. Data Quality Assessment

```python
def assess_dataset_quality(dataset):
    """Comprehensive dataset quality assessment"""
    
    quality_metrics = {}
    
    # Signal quality metrics
    signals = dataset['emg_signals']
    
    # Signal-to-noise ratio
    snr_values = []
    for signal in signals:
        signal_power = np.mean(signal**2)
        # Estimate noise from high-frequency content
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/1000)
        noise_mask = (freqs >= 400) & (freqs <= 500)
        noise_power = np.mean(np.abs(fft[noise_mask])**2)
        snr = 10 * np.log10(signal_power / noise_power)
        snr_values.append(snr)
    
    quality_metrics['mean_snr'] = np.mean(snr_values)
    quality_metrics['std_snr'] = np.std(snr_values)
    
    # Dynamic range
    dynamic_ranges = [np.max(signal) - np.min(signal) for signal in signals]
    quality_metrics['mean_dynamic_range'] = np.mean(dynamic_ranges)
    
    # Annotation completeness
    if 'annotations' in dataset:
        total_duration = sum([ann['end_time'] - ann['start_time'] 
                             for ann in dataset['annotations']])
        signal_duration = len(signals[0]) / 1000  # Assuming 1000 Hz
        quality_metrics['annotation_coverage'] = total_duration / signal_duration
    
    # Class balance
    if 'labels' in dataset:
        unique_labels, counts = np.unique(dataset['labels'], return_counts=True)
        quality_metrics['class_balance'] = np.std(counts) / np.mean(counts)
    
    return quality_metrics
```

### 2. Benchmark Performance

```python
class EMGBenchmark:
    def __init__(self):
        self.baseline_models = {
            'svm': SVC(kernel='rbf'),
            'random_forest': RandomForestClassifier(n_estimators=100),
            'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50))
        }
    
    def run_benchmark(self, dataset, test_size=0.2):
        """Run benchmark on dataset"""
        
        # Prepare data
        X = dataset['features']
        y = dataset['labels']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        results = {}
        
        # Test each baseline model
        for model_name, model in self.baseline_models.items():
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            
            results[model_name] = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1': f1_score(y_test, y_pred, average='weighted')
            }
        
        return results
```

## Data Sharing and Ethics

### 1. Privacy Considerations

**Data Anonymization**:
- Remove personal identifiers
- Aggregate demographic information
- Apply differential privacy techniques
- Secure data storage and transmission

**Consent Management**:
- Informed consent for data collection
- Clear usage permissions
- Right to data deletion
- Ongoing consent verification

### 2. Open Science Practices

**FAIR Data Principles**:
- **Findable**: Proper metadata and indexing
- **Accessible**: Open access with clear licensing
- **Interoperable**: Standard formats and protocols
- **Reusable**: Clear documentation and provenance

**Data Sharing Platforms**:
- IEEE DataPort
- Zenodo
- Figshare
- Institutional repositories

## Future Dataset Needs

### 1. Emerging Requirements

**Multi-Modal Integration**:
- EMG + EEG + fMRI
- EMG + Video (lip reading)
- EMG + Audio (parallel speech)
- EMG + Accelerometer (motion)

**Diverse Populations**:
- Age groups (children, elderly)
- Language diversity
- Neurological conditions
- Cultural variations

**Real-World Conditions**:
- Noisy environments
- Mobile/wearable scenarios
- Long-term recordings
- Emotional states

### 2. Technical Advances

**Higher Resolution**:
- High-density electrode arrays
- Improved spatial resolution
- Better temporal precision
- Multi-scale recordings

**Standardization**:
- Common data formats
- Unified annotation schemes
- Benchmark protocols
- Quality metrics

## Conclusion

The availability of high-quality EMG datasets is crucial for advancing silent speech recognition research. While several valuable datasets exist, there remains a need for larger, more diverse, and standardized datasets that reflect real-world usage conditions.

Key recommendations for dataset development:
- Standardize collection protocols and annotation schemes
- Ensure diverse participant populations
- Include multiple recording conditions
- Provide comprehensive quality metrics
- Follow open science and ethical guidelines

The field would benefit from collaborative efforts to create large-scale, multi-institutional datasets that can serve as common benchmarks for algorithm development and comparison.

## References

1. **Wand, M., & Schultz, T. (2011)**. Session-independent EMG-based speech recognition. Biosignals and Biorobotics Conference, 1-6.

2. **Gaddy, D., & Klein, D. (2020)**. Digital voicing of silent speech. Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing, 1692-1710.

3. **Meltzner, G. S., et al. (2018)**. Development of sEMG sensors and algorithms for silent speech recognition. Journal of Neural Engineering, 15(4), 046031.

4. **Kapur, A., Kapur, S., & Maes, P. (2018)**. AlterEgo: A personalized wearable silent speech interface. Proceedings of the 23rd International Conference on Intelligent User Interfaces, 43-53.

5. **Janke, M., & Diener, L. (2017)**. EMG-to-speech: Direct generation of speech from facial electromyographic signals. IEEE/ACM Transactions on Audio, Speech, and Language Processing, 25(12), 2375-2385.
