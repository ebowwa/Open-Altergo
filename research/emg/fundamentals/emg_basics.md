# EMG Fundamentals

## What is Electromyography (EMG)?

Electromyography (EMG) is a technique for evaluating and recording the electrical activity produced by skeletal muscles. EMG signals are bioelectric signals that reflect the anatomical and physiological properties of muscles.

## Physiological Basis

### Motor Unit Activation
- **Motor Unit**: The basic functional unit consisting of a motor neuron and all muscle fibers it innervates
- **Action Potential**: Electrical signal that travels along the motor neuron to muscle fibers
- **Muscle Contraction**: Result of synchronized activation of multiple motor units

### Signal Generation Process
1. **Neural Command**: Brain sends signal through spinal cord to motor neurons
2. **Neuromuscular Junction**: Motor neuron releases acetylcholine at muscle fiber
3. **Muscle Fiber Depolarization**: Electrical activity spreads across muscle membrane
4. **EMG Signal**: Summation of electrical activity from multiple muscle fibers

## EMG Signal Characteristics

### Amplitude
- **Range**: 0-10 mV (surface EMG), 0-30 mV (intramuscular EMG)
- **Typical**: 50-5000 μV for surface EMG during voluntary contractions
- **Factors**: Muscle force, electrode placement, muscle depth, tissue impedance

### Frequency Content
- **Bandwidth**: 10-500 Hz (usable content)
- **Peak Power**: 50-150 Hz
- **Low Frequency**: 10-50 Hz (muscle fiber conduction velocity)
- **High Frequency**: 150-500 Hz (motor unit firing rates)

### Temporal Characteristics
- **Onset**: 50-100 ms after neural command
- **Duration**: Varies with contraction type and duration
- **Fatigue Effects**: Frequency shift toward lower frequencies over time

## Types of EMG

### Surface EMG (sEMG)
**Advantages**:
- Non-invasive
- Easy to apply
- Suitable for dynamic movements
- Good for global muscle activity

**Disadvantages**:
- Lower spatial resolution
- Crosstalk from adjacent muscles
- Affected by subcutaneous tissue
- Limited to superficial muscles

**Applications**:
- Gait analysis
- Sports biomechanics
- Rehabilitation
- Silent speech interfaces

### Intramuscular EMG
**Advantages**:
- High spatial resolution
- Specific motor unit recording
- Less crosstalk
- Access to deep muscles

**Disadvantages**:
- Invasive procedure
- Risk of infection
- Limited movement
- Requires medical expertise

**Applications**:
- Clinical diagnosis
- Motor unit studies
- Research applications

## EMG in Silent Speech

### Relevant Muscles for Speech

**Facial Muscles**:
- **Masseter**: Jaw closing, chewing
- **Temporalis**: Jaw elevation
- **Buccinator**: Cheek compression
- **Orbicularis Oris**: Lip movement

**Neck Muscles**:
- **Sternocleidomastoid**: Head/neck movement
- **Platysma**: Lower face/neck expression
- **Digastric**: Jaw opening, swallowing

**Throat Muscles**:
- **Mylohyoid**: Floor of mouth, swallowing
- **Geniohyoid**: Hyoid bone movement
- **Thyrohyoid**: Larynx positioning

### Subvocalization Process

1. **Neural Planning**: Brain formulates speech intent
2. **Motor Preparation**: Motor cortex prepares muscle commands
3. **Muscle Activation**: Subtle contractions in speech muscles
4. **EMG Detection**: Surface electrodes capture electrical activity
5. **Signal Processing**: Extract features related to speech intent
6. **Classification**: Machine learning maps patterns to words/phonemes

### Signal Characteristics in Silent Speech

**Amplitude**: 10-100 μV (much lower than overt speech)
**Frequency**: 20-300 Hz (focused on speech-relevant frequencies)
**Spatial Patterns**: Different muscles activate for different phonemes
**Temporal Patterns**: Timing reflects speech rhythm and prosody

## Challenges in EMG Signal Processing

### Noise Sources

**Electrical Noise**:
- Power line interference (50/60 Hz)
- Electronic equipment interference
- Electrode impedance variations

**Physiological Noise**:
- Cardiac activity (ECG artifacts)
- Eye movement (EOG artifacts)
- Breathing artifacts
- Motion artifacts

**Environmental Factors**:
- Temperature variations
- Humidity effects
- Electrode-skin interface changes
- Cable movement artifacts

### Signal Processing Solutions

**Filtering**:
- High-pass filter (>10 Hz) to remove motion artifacts
- Low-pass filter (<500 Hz) to remove high-frequency noise
- Notch filter (50/60 Hz) to remove power line interference
- Adaptive filtering for dynamic noise removal

**Amplification**:
- Differential amplification to reduce common-mode noise
- High input impedance to minimize loading effects
- Low noise amplifiers for weak signals
- Programmable gain for different signal levels

**Digitization**:
- Sampling rate: >1000 Hz (Nyquist criterion)
- Resolution: 12-16 bits minimum
- Anti-aliasing filters before ADC
- Proper grounding and shielding

## EMG Feature Extraction

### Time Domain Features

**Root Mean Square (RMS)**:
```
RMS = sqrt(1/N * Σ(x[i]²))
```
- Represents signal power
- Correlates with muscle force
- Robust to noise

**Mean Absolute Value (MAV)**:
```
MAV = 1/N * Σ|x[i]|
```
- Simple amplitude measure
- Less sensitive to outliers
- Computationally efficient

**Zero Crossings (ZC)**:
```
ZC = Σ[sgn(x[i] * x[i+1]) < 0]
```
- Frequency domain information
- Indicates signal complexity
- Useful for muscle fatigue detection

**Waveform Length (WL)**:
```
WL = Σ|x[i+1] - x[i]|
```
- Measures signal complexity
- Sensitive to frequency content
- Good for pattern recognition

### Frequency Domain Features

**Mean Frequency (MNF)**:
```
MNF = Σ(f[i] * P[i]) / Σ(P[i])
```
- Spectral centroid
- Shifts with muscle fatigue
- Indicates motor unit recruitment

**Median Frequency (MDF)**:
- Frequency dividing spectrum into equal power halves
- Robust to noise
- Clinical fatigue indicator

**Power Spectral Density (PSD)**:
- Frequency distribution of signal power
- Reveals dominant frequency components
- Useful for muscle characterization

### Time-Frequency Features

**Short-Time Fourier Transform (STFT)**:
- Time-localized frequency analysis
- Good for non-stationary signals
- Balances time and frequency resolution

**Wavelet Transform**:
- Multi-resolution analysis
- Good for transient events
- Adaptive time-frequency resolution

**Empirical Mode Decomposition (EMD)**:
- Data-driven decomposition
- Handles non-linear signals
- No basis function assumptions

## Clinical and Research Applications

### Medical Diagnosis
- Neuromuscular disorders
- Motor neuron diseases
- Muscle fatigue assessment
- Rehabilitation monitoring

### Biomechanics Research
- Movement analysis
- Sports performance
- Ergonomic assessment
- Prosthetic control

### Brain-Computer Interfaces
- Silent speech recognition
- Gesture recognition
- Assistive technology
- Human-machine interaction

## Future Directions

### Advanced Signal Processing
- Machine learning feature extraction
- Deep learning classification
- Real-time adaptive filtering
- Multi-modal sensor fusion

### Hardware Innovations
- Wireless EMG systems
- Flexible electrode arrays
- Low-power acquisition
- Miniaturized amplifiers

### Applications
- Augmented reality control
- Virtual reality interaction
- Smart home automation
- Wearable health monitoring

## References

1. Merletti, R., & Parker, P. (2004). Electromyography: physiology, engineering, and non-invasive applications. John Wiley & Sons.

2. De Luca, C. J. (2002). Surface electromyography: detection and recording. DelSys Incorporated.

3. Reaz, M. B. I., Hussain, M. S., & Mohd-Yasin, F. (2006). Techniques of EMG signal analysis: detection, processing, classification and applications. Biological procedures online, 8(1), 11-35.

4. Phinyomark, A., Phukpattaranont, P., & Limsakul, C. (2012). Feature reduction and selection for EMG signal classification. Expert systems with applications, 39(8), 7420-7431.

5. Kapur, A., Kapur, S., & Maes, P. (2018). AlterEgo: A personalized wearable silent speech interface. In 23rd International Conference on Intelligent User Interfaces (pp. 43-53).
