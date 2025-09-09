# Getting Started with EMG for Silent Speech Recognition

## Introduction

This tutorial provides a step-by-step guide to building your first EMG-based silent speech recognition system. We'll cover everything from hardware setup to machine learning implementation, using the Open-Altergo framework as our foundation.

## Prerequisites

### Knowledge Requirements
- Basic understanding of signal processing
- Familiarity with Python programming
- Elementary knowledge of machine learning
- Basic electronics (for hardware setup)

### Software Requirements
```bash
# Python packages
pip install numpy scipy scikit-learn matplotlib
pip install tensorflow  # or pytorch
pip install pyserial    # for Arduino communication
pip install jupyter     # for interactive development

# Optional but recommended
pip install plotly      # for interactive plots
pip install pandas      # for data manipulation
pip install seaborn     # for statistical plots
```

### Hardware Requirements
- Arduino Uno or compatible microcontroller
- MyoWare Muscle Sensor (or equivalent EMG sensor)
- Ag/AgCl electrodes (disposable or reusable)
- Jumper wires and breadboard
- Computer with USB port

## Tutorial 1: Basic EMG Signal Acquisition

### Step 1: Hardware Setup

**Circuit Connection**:
```
MyoWare Sensor → Arduino Uno
VCC → 5V
GND → GND
SIG → A0
```

**Electrode Placement**:
1. Clean skin with alcohol wipe
2. Place reference electrode on bony area (wrist)
3. Place two recording electrodes on masseter muscle (jaw)
4. Ensure good contact and secure placement

### Step 2: Arduino Code

```arduino
// Basic EMG acquisition
const int EMG_PIN = A0;
const int SAMPLE_RATE = 1000; // 1 kHz
const int SAMPLE_DELAY = 1000 / SAMPLE_RATE;

void setup() {
  Serial.begin(115200);
  pinMode(EMG_PIN, INPUT);
}

void loop() {
  // Read EMG value
  int emgValue = analogRead(EMG_PIN);
  
  // Convert to voltage (0-5V)
  float voltage = emgValue * (5.0 / 1023.0);
  
  // Send timestamp and value
  Serial.print(millis());
  Serial.print(",");
  Serial.println(voltage);
  
  delay(SAMPLE_DELAY);
}
```

### Step 3: Python Data Collection

```python
import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time

class EMGCollector:
    def __init__(self, port='COM3', baud_rate=115200):
        self.serial_port = serial.Serial(port, baud_rate)
        self.data_buffer = deque(maxlen=1000)  # 1 second of data
        
    def collect_data(self, duration=10):
        """Collect EMG data for specified duration"""
        print(f"Collecting EMG data for {duration} seconds...")
        
        start_time = time.time()
        timestamps = []
        emg_values = []
        
        while time.time() - start_time < duration:
            try:
                line = self.serial_port.readline().decode().strip()
                if ',' in line:
                    timestamp, emg_value = line.split(',')
                    timestamps.append(float(timestamp))
                    emg_values.append(float(emg_value))
                    
            except (ValueError, UnicodeDecodeError):
                continue
        
        return np.array(timestamps), np.array(emg_values)
    
    def close(self):
        self.serial_port.close()

# Usage example
collector = EMGCollector(port='/dev/ttyUSB0')  # Adjust port as needed

# Collect baseline data (relaxed state)
print("Relax your jaw muscles...")
time.sleep(3)
baseline_times, baseline_emg = collector.collect_data(5)

# Collect active data (clench jaw)
print("Clench your jaw muscles...")
time.sleep(2)
active_times, active_emg = collector.collect_data(5)

collector.close()

# Plot results
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(baseline_times, baseline_emg)
plt.title('Baseline EMG (Relaxed)')
plt.ylabel('Voltage (V)')

plt.subplot(2, 1, 2)
plt.plot(active_times, active_emg)
plt.title('Active EMG (Jaw Clenched)')
plt.xlabel('Time (ms)')
plt.ylabel('Voltage (V)')

plt.tight_layout()
plt.show()
```

## Tutorial 2: Signal Processing Basics

### Step 1: Filtering EMG Signals

```python
from scipy.signal import butter, filtfilt, iirnotch
import numpy as np

class EMGProcessor:
    def __init__(self, sampling_rate=1000):
        self.fs = sampling_rate
        self.design_filters()
    
    def design_filters(self):
        """Design filters for EMG processing"""
        nyquist = self.fs / 2
        
        # Band-pass filter (20-500 Hz)
        low = 20 / nyquist
        high = 500 / nyquist
        self.bp_b, self.bp_a = butter(4, [low, high], btype='band')
        
        # Notch filter (60 Hz power line)
        self.notch_b, self.notch_a = iirnotch(60, 30, self.fs)
    
    def process_signal(self, emg_signal):
        """Apply complete processing pipeline"""
        # 1. Band-pass filtering
        filtered = filtfilt(self.bp_b, self.bp_a, emg_signal)
        
        # 2. Notch filtering
        filtered = filtfilt(self.notch_b, self.notch_a, filtered)
        
        # 3. Rectification
        rectified = np.abs(filtered)
        
        # 4. Smoothing (low-pass at 10 Hz)
        smooth_b, smooth_a = butter(2, 10/500, btype='low')
        envelope = filtfilt(smooth_b, smooth_a, rectified)
        
        return {
            'raw': emg_signal,
            'filtered': filtered,
            'rectified': rectified,
            'envelope': envelope
        }

# Example usage
processor = EMGProcessor()

# Process the collected data
baseline_processed = processor.process_signal(baseline_emg)
active_processed = processor.process_signal(active_emg)

# Visualize processing stages
fig, axes = plt.subplots(4, 2, figsize=(15, 12))

stages = ['raw', 'filtered', 'rectified', 'envelope']
data_sets = [baseline_processed, active_processed]
titles = ['Baseline (Relaxed)', 'Active (Clenched)']

for col, (data, title) in enumerate(zip(data_sets, titles)):
    for row, stage in enumerate(stages):
        axes[row, col].plot(data[stage])
        axes[row, col].set_title(f'{title} - {stage.capitalize()}')
        axes[row, col].set_ylabel('Amplitude')
        if row == 3:  # Last row
            axes[row, col].set_xlabel('Sample')

plt.tight_layout()
plt.show()
```

### Step 2: Feature Extraction

```python
def extract_emg_features(signal, window_size=250, overlap=125):
    """Extract features from EMG signal windows"""
    
    features = []
    step_size = window_size - overlap
    
    for i in range(0, len(signal) - window_size + 1, step_size):
        window = signal[i:i + window_size]
        
        # Time-domain features
        rms = np.sqrt(np.mean(window**2))
        mav = np.mean(np.abs(window))
        variance = np.var(window)
        zero_crossings = np.sum(np.diff(np.sign(window)) != 0)
        
        # Frequency-domain features
        fft = np.fft.fft(window)
        freqs = np.fft.fftfreq(len(window), 1/1000)
        power_spectrum = np.abs(fft)**2
        
        # Power in frequency bands
        low_band = np.sum(power_spectrum[(freqs >= 20) & (freqs <= 80)])
        mid_band = np.sum(power_spectrum[(freqs >= 80) & (freqs <= 150)])
        high_band = np.sum(power_spectrum[(freqs >= 150) & (freqs <= 300)])
        
        # Spectral centroid
        spectral_centroid = np.sum(freqs[:len(freqs)//2] * power_spectrum[:len(freqs)//2]) / np.sum(power_spectrum[:len(freqs)//2])
        
        feature_vector = [rms, mav, variance, zero_crossings, 
                         low_band, mid_band, high_band, spectral_centroid]
        features.append(feature_vector)
    
    return np.array(features)

# Extract features from processed signals
baseline_features = extract_emg_features(baseline_processed['envelope'])
active_features = extract_emg_features(active_processed['envelope'])

print(f"Baseline features shape: {baseline_features.shape}")
print(f"Active features shape: {active_features.shape}")

# Visualize feature differences
feature_names = ['RMS', 'MAV', 'Variance', 'Zero Crossings', 
                'Low Band', 'Mid Band', 'High Band', 'Spectral Centroid']

baseline_mean = np.mean(baseline_features, axis=0)
active_mean = np.mean(active_features, axis=0)

plt.figure(figsize=(12, 6))
x = np.arange(len(feature_names))
width = 0.35

plt.bar(x - width/2, baseline_mean, width, label='Baseline', alpha=0.7)
plt.bar(x + width/2, active_mean, width, label='Active', alpha=0.7)

plt.xlabel('Features')
plt.ylabel('Feature Value')
plt.title('EMG Feature Comparison: Baseline vs Active')
plt.xticks(x, feature_names, rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
```

## Tutorial 3: Simple Classification

### Step 1: Prepare Training Data

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report

# Prepare dataset
X = np.vstack([baseline_features, active_features])
y = np.hstack([np.zeros(len(baseline_features)), 
               np.ones(len(active_features))])

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training set: {X_train_scaled.shape}")
print(f"Test set: {X_test_scaled.shape}")
```

### Step 2: Train Classifier

```python
# Train SVM classifier
classifier = SVC(kernel='rbf', C=1.0, gamma='scale')
classifier.fit(X_train_scaled, y_train)

# Make predictions
y_pred = classifier.predict(X_test_scaled)

# Evaluate performance
accuracy = accuracy_score(y_test, y_pred)
print(f"Classification Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, 
                          target_names=['Relaxed', 'Active']))
```

### Step 3: Real-Time Classification

```python
class RealTimeEMGClassifier:
    def __init__(self, classifier, scaler, processor):
        self.classifier = classifier
        self.scaler = scaler
        self.processor = processor
        self.buffer = deque(maxlen=250)  # 250ms window
        
    def process_sample(self, emg_sample):
        """Process single EMG sample and classify if window is full"""
        self.buffer.append(emg_sample)
        
        if len(self.buffer) == 250:
            # Process signal
            signal = np.array(self.buffer)
            processed = self.processor.process_signal(signal)
            
            # Extract features
            features = extract_emg_features(processed['envelope'])
            if len(features) > 0:
                # Scale and classify
                features_scaled = self.scaler.transform(features[-1:])
                prediction = self.classifier.predict(features_scaled)[0]
                confidence = self.classifier.decision_function(features_scaled)[0]
                
                return {
                    'prediction': 'Active' if prediction == 1 else 'Relaxed',
                    'confidence': confidence
                }
        
        return None

# Create real-time classifier
rt_classifier = RealTimeEMGClassifier(classifier, scaler, processor)

# Simulate real-time processing
print("Real-time EMG classification demo:")
print("Collecting new data for real-time classification...")

# Collect new test data
test_collector = EMGCollector(port='/dev/ttyUSB0')
test_times, test_emg = test_collector.collect_data(10)
test_collector.close()

# Process in real-time simulation
predictions = []
for sample in test_emg:
    result = rt_classifier.process_sample(sample)
    if result:
        predictions.append(result)
        print(f"Prediction: {result['prediction']}, "
              f"Confidence: {result['confidence']:.2f}")

print(f"\nProcessed {len(predictions)} windows")
```

## Tutorial 4: Multi-Word Recognition

### Step 1: Data Collection for Words

```python
class WordDataCollector:
    def __init__(self, port='COM3'):
        self.collector = EMGCollector(port)
        self.processor = EMGProcessor()
        
    def collect_word_data(self, words, repetitions=5):
        """Collect EMG data for multiple words"""
        dataset = {'features': [], 'labels': [], 'words': []}
        
        for word in words:
            print(f"\nCollecting data for word: '{word}'")
            
            for rep in range(repetitions):
                print(f"Repetition {rep + 1}/{repetitions}")
                print("Get ready... (3 seconds)")
                time.sleep(3)
                
                print(f"Say '{word}' silently (mouth the word)")
                times, emg_data = self.collector.collect_data(2)
                
                # Process signal
                processed = self.processor.process_signal(emg_data)
                
                # Extract features
                features = extract_emg_features(processed['envelope'])
                
                # Store data
                for feature_vector in features:
                    dataset['features'].append(feature_vector)
                    dataset['labels'].append(len(dataset['words']))
                    dataset['words'].append(word)
                
                print("Rest for 2 seconds...")
                time.sleep(2)
        
        # Convert to numpy arrays
        dataset['features'] = np.array(dataset['features'])
        dataset['labels'] = np.array(dataset['labels'])
        
        return dataset

# Collect data for multiple words
words = ['hello', 'world', 'yes', 'no']
word_collector = WordDataCollector(port='/dev/ttyUSB0')
word_dataset = word_collector.collect_word_data(words, repetitions=3)
word_collector.collector.close()

print(f"Collected {len(word_dataset['features'])} feature vectors")
print(f"Words: {words}")
```

### Step 2: Train Multi-Class Classifier

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
import seaborn as sns

# Prepare multi-class dataset
X_words = word_dataset['features']
y_words = word_dataset['labels']

# Split data
X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(
    X_words, y_words, test_size=0.3, random_state=42, stratify=y_words
)

# Scale features
scaler_words = StandardScaler()
X_train_w_scaled = scaler_words.fit_transform(X_train_w)
X_test_w_scaled = scaler_words.transform(X_test_w)

# Train Random Forest classifier
rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
rf_classifier.fit(X_train_w_scaled, y_train_w)

# Evaluate
y_pred_w = rf_classifier.predict(X_test_w_scaled)
accuracy_words = accuracy_score(y_test_w, y_pred_w)

print(f"Multi-word Classification Accuracy: {accuracy_words:.2%}")

# Confusion matrix
cm = confusion_matrix(y_test_w, y_pred_w)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=words, yticklabels=words)
plt.title('Confusion Matrix - Word Classification')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()

# Feature importance
feature_importance = rf_classifier.feature_importances_
plt.figure(figsize=(10, 6))
plt.bar(feature_names, feature_importance)
plt.title('Feature Importance for Word Classification')
plt.xlabel('Features')
plt.ylabel('Importance')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## Tutorial 5: Building a Complete System

### Step 1: Integrated EMG System

```python
class EMGSpeechSystem:
    def __init__(self, port='COM3'):
        self.collector = EMGCollector(port)
        self.processor = EMGProcessor()
        self.classifier = None
        self.scaler = None
        self.words = []
        self.is_trained = False
        
    def train_system(self, words, repetitions=5):
        """Train the complete EMG speech system"""
        print("Training EMG Speech Recognition System...")
        
        # Collect training data
        word_collector = WordDataCollector(self.collector.serial_port.port)
        dataset = word_collector.collect_word_data(words, repetitions)
        
        # Prepare data
        X = dataset['features']
        y = dataset['labels']
        self.words = words
        
        # Split and scale
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train classifier
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Training completed. Accuracy: {accuracy:.2%}")
        self.is_trained = True
        
        return accuracy
    
    def recognize_speech(self, duration=2):
        """Recognize speech from EMG signals"""
        if not self.is_trained:
            print("System not trained. Please train first.")
            return None
        
        print("Recording EMG for speech recognition...")
        times, emg_data = self.collector.collect_data(duration)
        
        # Process signal
        processed = self.processor.process_signal(emg_data)
        
        # Extract features
        features = extract_emg_features(processed['envelope'])
        
        if len(features) == 0:
            return None
        
        # Average features across windows
        avg_features = np.mean(features, axis=0).reshape(1, -1)
        
        # Scale and predict
        features_scaled = self.scaler.transform(avg_features)
        prediction = self.classifier.predict(features_scaled)[0]
        probabilities = self.classifier.predict_proba(features_scaled)[0]
        
        result = {
            'word': self.words[prediction],
            'confidence': np.max(probabilities),
            'all_probabilities': dict(zip(self.words, probabilities))
        }
        
        return result
    
    def interactive_demo(self):
        """Run interactive speech recognition demo"""
        if not self.is_trained:
            print("System not trained. Please train first.")
            return
        
        print("\nInteractive EMG Speech Recognition Demo")
        print("Commands: 'recognize', 'quit'")
        
        while True:
            command = input("\nEnter command: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'recognize':
                print("Silently mouth a word in 3 seconds...")
                time.sleep(3)
                
                result = self.recognize_speech(duration=2)
                if result:
                    print(f"Recognized: '{result['word']}' "
                          f"(confidence: {result['confidence']:.2%})")
                    print("All probabilities:")
                    for word, prob in result['all_probabilities'].items():
                        print(f"  {word}: {prob:.2%}")
                else:
                    print("No speech detected")
            else:
                print("Unknown command. Use 'recognize' or 'quit'")

# Create and train the complete system
emg_system = EMGSpeechSystem(port='/dev/ttyUSB0')

# Train with a small vocabulary
training_words = ['hello', 'world', 'yes', 'no']
accuracy = emg_system.train_system(training_words, repetitions=3)

# Run interactive demo
emg_system.interactive_demo()

# Clean up
emg_system.collector.close()
```

## Troubleshooting Guide

### Common Issues and Solutions

**1. No Signal Detected**
```python
def troubleshoot_signal():
    """Troubleshoot EMG signal issues"""
    
    # Check electrode contact
    print("Checking electrode impedance...")
    # Measure DC resistance (should be < 10kΩ for wet electrodes)
    
    # Check amplifier gain
    print("Checking amplifier settings...")
    # Verify gain is appropriate (1000-10000x)
    
    # Check muscle activation
    print("Testing muscle activation...")
    print("Clench jaw muscles and observe signal change")
```

**2. High Noise Levels**
```python
def reduce_noise():
    """Strategies for noise reduction"""
    
    # Improve electrode contact
    print("1. Clean skin with alcohol")
    print("2. Apply conductive gel")
    print("3. Secure electrode placement")
    
    # Environmental factors
    print("4. Move away from electrical devices")
    print("5. Use shielded cables")
    print("6. Ensure proper grounding")
    
    # Signal processing
    print("7. Apply notch filter for power line interference")
    print("8. Use adaptive filtering for motion artifacts")
```

**3. Poor Classification Accuracy**
```python
def improve_accuracy():
    """Tips for improving classification accuracy"""
    
    print("Data Collection:")
    print("- Collect more training samples")
    print("- Ensure consistent electrode placement")
    print("- Include diverse speaking conditions")
    
    print("Feature Engineering:")
    print("- Try different feature combinations")
    print("- Use time-frequency features")
    print("- Apply feature selection techniques")
    
    print("Model Selection:")
    print("- Try different classifiers")
    print("- Use ensemble methods")
    print("- Implement deep learning models")
```

## Next Steps

### Advanced Topics to Explore

1. **Multi-Channel EMG**: Use multiple electrode sites for better spatial resolution
2. **Deep Learning**: Implement CNN/LSTM models for improved accuracy
3. **Real-Time Optimization**: Optimize for low-latency real-time processing
4. **User Adaptation**: Implement online learning for user-specific adaptation
5. **Multi-Modal Fusion**: Combine EMG with EEG or other sensors

### Recommended Reading

- "Surface Electromyography: Physiology, Engineering, and Applications" by Merletti & Farina
- "Digital Signal Processing" by Proakis & Manolakis
- "Pattern Recognition and Machine Learning" by Bishop
- Recent papers on EMG-based silent speech recognition

### Community Resources

- OpenBCI Community Forum
- EMG Signal Processing Groups
- Brain-Computer Interface Communities
- Open-Source EMG Projects on GitHub

## Conclusion

This tutorial has provided a comprehensive introduction to EMG-based silent speech recognition. You've learned to:

- Set up EMG hardware and collect signals
- Process and filter EMG data
- Extract meaningful features
- Train classification models
- Build a complete speech recognition system

The field of EMG-based silent speech is rapidly evolving, with new techniques and applications emerging regularly. Continue experimenting with different approaches and contributing to the open-source community to advance this exciting technology.

Remember that building effective EMG systems requires patience, experimentation, and iterative improvement. Start with simple applications and gradually increase complexity as you gain experience with the technology.
