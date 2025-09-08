# Open-Altergo: Open Source Silent Speech Interface

An open-source implementation of a silent speech interface inspired by MIT's AlterEgo project. This project enables silent communication by detecting subtle muscle movements (EMG signals) during internal speech articulation (subvocalization).

## ⚠️ Important Disclaimer

**This is NOT mind-reading technology.** Open-Altergo detects intentional muscle movements associated with speech articulation, not thoughts. You must subtly move your mouth/jaw muscles (without making sound) for the system to work. This is similar to how the original AlterEgo works - it's based on electromyography (EMG) signal detection, not direct neural signal reading.

## Overview

Open-Altergo captures the spectrum of speech from mouthed words to the mere intent to speak, ensuring it only picks up what the user intends to communicate. The technology uses surface electromyography (sEMG) to detect muscle movements in the face, jaw, and neck during internal articulation.

### Key Features

- **Non-invasive EMG signal detection** using surface electrodes
- **Real-time signal processing** with filtering and feature extraction
- **Machine learning classification** for word/command recognition
- **Silent feedback** via bone conduction audio
- **Modular design** supporting Arduino and Raspberry Pi platforms
- **Open-source** with MIT license

## How It Works

### 1. Neural Signal Detection
- Surface electrodes placed on jaw, neck, and face muscles
- Captures neuromuscular signals during subvocalization
- Focuses on speech articulators (tongue, larynx, jaw muscles)
- Non-invasive detection of electrical impulses sent to speech muscles

### 2. Signal Processing
- **Filtering**: Band-pass (20-500Hz) and notch filters (50/60Hz noise removal)
- **Amplification**: Boost weak EMG signals for analysis
- **Feature Extraction**: RMS amplitude, frequency spectrum, temporal patterns
- **Noise Reduction**: Independent Component Analysis (ICA) for interference removal

### 3. Machine Learning Recognition
- **Training Data**: EMG signals paired with corresponding words/phrases
- **Neural Networks**: CNN/RNN models for pattern recognition
- **Real-time Processing**: <1s latency for practical interaction
- **Personalization**: Adaptive learning for individual users

### 4. Feedback System
- **Bone Conduction**: Silent audio feedback without blocking ambient sound
- **Visual Output**: Text display or computer interface control
- **API Integration**: Connect to AI systems, search engines, or applications

## Hardware Requirements

### Core Components ($50-200)

#### EMG Sensors
- **MyoWare Muscle Sensor** ($30-50) - Arduino-compatible EMG amplifier
- **Electrodes**: Dry electrodes ($10-20) or gel electrodes ($5-10)
- **Placement**: 4-8 channels on jaw (masseter), neck (sternocleidomastoid), face

#### Microcontroller Options
- **Arduino Uno/Nano** ($10-20) - Basic signal acquisition
- **Raspberry Pi 4** ($35-60) - Advanced processing and ML inference
- **OpenBCI Board** ($250-500) - Professional-grade EEG/EMG (optional)

#### Additional Components
- Breadboard, wires, battery pack ($10-15)
- Bone conduction transducer ($5-15) for audio feedback
- 3D-printed headset frame (optional, designs available)

### Advanced Setup ($200-500)
- Multiple EMG channels (8+)
- Hybrid EEG integration with OpenBCI
- Custom PCB design
- Professional electrode arrays

## Software Stack

### Core Libraries
- **Arduino IDE** - Firmware development
- **Python 3.8+** - Main processing language
- **SciPy/NumPy** - Signal processing and filtering
- **scikit-learn** - Machine learning and ICA
- **TensorFlow Lite** - Neural network inference
- **PySerial** - Arduino communication

### Signal Processing
```python
# Band-pass filter for EMG (20-500Hz)
from scipy import signal
b, a = signal.butter(4, [20/500, 500/500], btype='band', fs=1000)
filtered = signal.filtfilt(b, a, raw_signal)

# Notch filter for power line noise
notch_freq = 60  # or 50Hz depending on region
quality = 30
b_notch, a_notch = signal.iirnotch(notch_freq, quality, fs=1000)
clean_signal = signal.filtfilt(b_notch, a_notch, filtered)
```

### Machine Learning Pipeline
- **Feature Extraction**: RMS, spectral features, time-domain analysis
- **Classification**: SVM, Random Forest, or Neural Networks
- **Training**: Supervised learning on labeled EMG-word pairs
- **Evaluation**: Cross-validation and real-time accuracy testing

## Quick Start Guide

### 1. Hardware Setup (1-3 days)
1. **Assemble EMG Circuit**
   - Connect MyoWare sensor to Arduino (Signal → A0, Power → 5V/GND)
   - Follow electrode placement guide for optimal signal capture
   - Test raw signals using Arduino Serial Plotter

2. **Electrode Placement**
   - Jaw: Left/right masseter muscles
   - Neck: Under chin, sternocleidomastoid
   - Face: Cheek muscles (optional)
   - Ensure good skin contact and conductivity

### 2. Software Installation
```bash
# Clone repository
git clone https://github.com/ebowwa/Open-Altergo.git
cd Open-Altergo

# Install Python dependencies
pip install -r requirements.txt

# Upload Arduino firmware
# Open arduino/emg_acquisition/emg_acquisition.ino in Arduino IDE
# Select board and port, then upload
```

### 3. Data Collection (3-7 days)
```python
# Run data collection script
python scripts/collect_training_data.py

# Follow prompts to:
# 1. Silently mouth words/numbers (50-100 repetitions each)
# 2. Label each utterance
# 3. Build personal training dataset
```

### 4. Model Training (5-14 days)
```python
# Train classification model
python scripts/train_model.py --data data/training_set.csv

# Evaluate performance
python scripts/evaluate_model.py --model models/trained_classifier.pkl
```

### 5. Real-time Testing
```python
# Run real-time recognition
python scripts/realtime_recognition.py

# Test silent speech → text output
# Integrate with applications (typing, search, etc.)
```

## Project Structure

```
Open-Altergo/
├── README.md
├── LICENSE
├── requirements.txt
├── arduino/
│   ├── emg_acquisition/          # Arduino firmware
│   └── examples/                 # Basic EMG demos
├── python/
│   ├── signal_processing/        # DSP pipeline
│   ├── machine_learning/         # ML models and training
│   ├── realtime/                # Real-time recognition
│   └── utils/                   # Helper functions
├── data/
│   ├── datasets/                # Training datasets
│   └── models/                  # Trained models
├── docs/
│   ├── hardware_guide.md        # Detailed hardware setup
│   ├── electrode_placement.md   # Electrode positioning guide
│   └── api_reference.md         # Software API documentation
├── scripts/
│   ├── collect_training_data.py
│   ├── train_model.py
│   └── realtime_recognition.py
└── examples/
    ├── basic_emg_demo/          # Simple EMG reading
    ├── word_recognition/        # Basic word classifier
    └── integration_demos/       # App integrations
```

## Performance Expectations

### Accuracy Targets
- **Initial Setup**: 40-60% accuracy (similar to research baselines)
- **After Personalization**: 70-90% accuracy for trained words
- **Advanced Setup**: 90%+ accuracy (8+ channels, extensive training)

### Comparison to Research
- **MIT AlterEgo**: ~92% accuracy (8 EMG channels, controlled environment)
- **Meta Brain2Qwerty**: ~40% accuracy (64 EEG electrodes, character-level)
- **Open-Altergo Target**: 70-85% accuracy (4-8 EMG channels, word-level)

### Limitations
- Requires subtle mouth movements (not pure thought reading)
- Performance degrades in noisy environments
- Individual calibration needed for optimal accuracy
- Limited vocabulary without extensive training

## Applications

### Personal Use
- Silent typing and text input
- Voice assistant interaction without speaking
- Private communication in quiet environments
- Accessibility aid for speech impairments

### Development Platform
- Research tool for silent speech interfaces
- Educational platform for EMG signal processing
- Prototyping base for commercial applications
- Integration with AI systems and IoT devices

## Research Background

This project builds upon foundational research in silent speech interfaces:

- **MIT AlterEgo (2018)**: "AlterEgo: A Personalized Wearable Silent Speech Interface" by Kapur et al.
- **EMG-based Speech Recognition**: Multiple academic papers on surface EMG for speech detection
- **Brain-Computer Interfaces**: Broader BCI research for communication applications

### Key Differences from Original AlterEgo
- **Open Source**: Complete hardware and software specifications
- **Accessible Hardware**: Uses readily available components
- **Modular Design**: Supports various platforms and configurations
- **Community Driven**: Open development and contribution model

## Contributing

We welcome contributions from researchers, developers, and enthusiasts! Areas of focus:

### Hardware Development
- Improved electrode designs
- Custom PCB layouts
- Wearable form factors
- Wireless communication

### Software Enhancement
- Advanced signal processing algorithms
- Better machine learning models
- Real-time optimization
- User interface improvements

### Research Applications
- Accuracy improvements
- Noise robustness
- Vocabulary expansion
- Multi-language support

## Safety and Ethics

### Safety Considerations
- **Non-invasive Only**: Surface electrodes only, no implants
- **Skin Safety**: Avoid prolonged electrode contact, use hypoallergenic materials
- **Electrical Safety**: Low voltage operation, proper grounding
- **Medical Consultation**: Consult healthcare providers if you have medical conditions

### Privacy and Ethics
- **Intentional Communication**: Only captures deliberate speech attempts
- **Local Processing**: Data stays on device unless explicitly shared
- **User Control**: Complete control over what is transmitted
- **Transparency**: Open-source ensures no hidden functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- MIT Media Lab for the original AlterEgo research
- Open-source EMG and BCI communities
- Contributors to signal processing and machine learning libraries
- Hardware manufacturers supporting open-source development

## Support and Community

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for help and collaboration
- **Documentation**: Comprehensive guides in the `/docs` directory
- **Examples**: Working code examples in `/examples` directory

---

**Disclaimer**: This is an experimental project for research and educational purposes. Results may vary significantly between users and setups. This technology does not read thoughts and requires intentional muscle movements to function.
