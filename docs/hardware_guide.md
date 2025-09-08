# Open-Altergo Hardware Setup Guide

This guide provides detailed instructions for setting up the hardware components needed for your Open-Altergo silent speech interface.

## Overview

Open-Altergo uses surface electromyography (sEMG) to detect muscle activity during silent speech. The system captures electrical signals from facial and neck muscles when you internally articulate words without making sound.

## Required Components

### Core Hardware ($50-200)

#### 1. EMG Sensor Module
**Recommended: MyoWare Muscle Sensor**
- **Price**: $30-50
- **Supplier**: SparkFun, Adafruit, or Amazon
- **Features**: 
  - Built-in amplification and filtering
  - Arduino-compatible 3.3V/5V operation
  - Integrated electrode connectors
  - Adjustable gain

**Alternative: DIY EMG Circuit**
- **Components**: AD8226 instrumentation amplifier, passive components
- **Price**: $5-15
- **Complexity**: Requires PCB design and assembly
- **Advantage**: Customizable gain and filtering

#### 2. Microcontroller Platform

**Option A: Arduino Uno/Nano (Beginner)**
- **Price**: $10-20
- **Pros**: Simple, well-documented, large community
- **Cons**: Limited processing power, no built-in WiFi
- **Use case**: Basic signal acquisition and serial transmission

**Option B: Raspberry Pi 4 (Advanced)**
- **Price**: $35-60
- **Pros**: Full Linux OS, powerful processing, WiFi/Bluetooth
- **Cons**: Higher power consumption, more complex setup
- **Use case**: Real-time processing, ML inference, standalone operation

**Option C: ESP32 (Wireless)**
- **Price**: $15-25
- **Pros**: WiFi/Bluetooth, dual-core, low power
- **Cons**: More complex programming
- **Use case**: Wireless EMG transmission, IoT integration

#### 3. Electrodes

**Dry Electrodes (Recommended for prototyping)**
- **Type**: Ag/AgCl or stainless steel
- **Price**: $10-20 for pack of 10
- **Pros**: Reusable, no gel required, comfortable
- **Cons**: Higher impedance, may need better skin contact

**Gel Electrodes (Medical grade)**
- **Type**: Disposable Ag/AgCl with conductive gel
- **Price**: $5-10 for pack of 50
- **Pros**: Low impedance, excellent signal quality
- **Cons**: Single-use, can cause skin irritation

**Electrode Specifications:**
- **Size**: 10-20mm diameter for facial placement
- **Material**: Silver/Silver Chloride (Ag/AgCl) preferred
- **Connector**: 3.5mm snap or wire leads
- **Quantity**: 8-12 electrodes (4 channels + references)

#### 4. Additional Components

**Wiring and Connections**
- Breadboard or PCB for prototyping ($5-10)
- Jumper wires and connectors ($5-10)
- Shielded cable for electrode connections ($10-15)

**Power Supply**
- 9V battery pack for portable operation ($5-10)
- USB power bank for Raspberry Pi ($15-25)
- LiPo battery for advanced builds ($10-20)

**Audio Feedback (Optional)**
- Bone conduction transducer ($5-15)
- Small speaker or piezo buzzer ($2-5)
- Audio amplifier module ($3-8)

### Advanced Hardware ($200-500)

#### Professional EMG Systems
**OpenBCI Cyton Board**
- **Price**: $250-350
- **Features**: 8-channel EEG/EMG, research-grade
- **Pros**: High precision, extensive software support
- **Use case**: Research applications, high-accuracy requirements

**Custom PCB Design**
- **Cost**: $50-150 for small batch production
- **Features**: Optimized layout, integrated components
- **Requirements**: PCB design skills, component sourcing

#### Wearable Form Factor
**3D Printed Enclosure**
- **Cost**: $10-30 in materials
- **Design**: Custom headset or jaw-mounted device
- **Files**: Available on Thingiverse and project repository

**Flexible PCB**
- **Cost**: $100-200 for prototypes
- **Advantage**: Comfortable wearable design
- **Complexity**: Requires specialized manufacturing

## Electrode Placement Guide

### Primary Placement (4-Channel Setup)

#### Channel 1: Masseter Muscle (Jaw)
- **Location**: Over the masseter muscle on the right side of the jaw
- **Position**: Place electrode 2-3cm above the jaw angle
- **Function**: Detects jaw movement during speech articulation
- **Reference**: Place reference electrode on the mastoid process (behind ear)

#### Channel 2: Masseter Muscle (Left Jaw)
- **Location**: Mirror position of Channel 1 on left side
- **Position**: Symmetric placement for bilateral detection
- **Function**: Captures left-right jaw movement differences
- **Reference**: Shared with Channel 1 or separate mastoid reference

#### Channel 3: Sternocleidomastoid (Neck)
- **Location**: On the sternocleidomastoid muscle in the neck
- **Position**: 2-3cm below the ear, on the neck muscle
- **Function**: Detects laryngeal and throat muscle activity
- **Reference**: Place on the clavicle (collarbone)

#### Channel 4: Submental (Under Chin)
- **Location**: Under the chin, above the hyoid bone
- **Position**: Center of the submental triangle
- **Function**: Captures tongue and floor-of-mouth muscle activity
- **Reference**: On the chin or shared with other channels

### Advanced Placement (8-Channel Setup)

Add the following channels for improved accuracy:

#### Channel 5-6: Facial Muscles
- **Location**: Zygomatic major (cheek muscles)
- **Function**: Lip and cheek movement detection

#### Channel 7-8: Additional Neck Muscles
- **Location**: Anterior neck muscles
- **Function**: Enhanced laryngeal activity detection

### Placement Tips

1. **Skin Preparation**
   - Clean skin with alcohol wipe
   - Gently abrade with fine sandpaper if using dry electrodes
   - Ensure good electrical contact

2. **Electrode Attachment**
   - Use medical tape or adhesive rings
   - Ensure secure but comfortable attachment
   - Avoid excessive pressure that could cause discomfort

3. **Reference Electrodes**
   - Place on electrically neutral locations (mastoid, clavicle)
   - Ensure good contact for noise reduction
   - Use common reference for multiple channels when possible

4. **Cable Management**
   - Secure cables to prevent movement artifacts
   - Use strain relief at electrode connections
   - Keep cables away from power sources to reduce interference

## Circuit Design

### Basic Arduino Circuit

```
MyoWare Sensor → Arduino Uno
├── VCC → 5V
├── GND → GND
├── SIG → A0 (Analog Input)
└── Optional: RAW → A1 (for raw signal monitoring)

Additional Channels:
├── Sensor 2 → A1
├── Sensor 3 → A2
└── Sensor 4 → A3
```

### Multi-Channel Amplifier Circuit

For DIY builders, here's a basic 4-channel EMG amplifier design:

**Per Channel:**
- Instrumentation amplifier (AD8226 or INA128)
- High-pass filter (0.5Hz, removes DC offset)
- Low-pass filter (500Hz, anti-aliasing)
- Notch filter (50/60Hz, power line rejection)
- Final amplification stage

**Shared Components:**
- Power supply regulation (+/-5V or single 5V)
- Reference electrode buffer
- Digital isolation (optional, for safety)

### Power Considerations

**Current Consumption:**
- Arduino Uno: ~50mA
- MyoWare sensors: ~10mA each
- Total system: ~100-150mA

**Battery Life:**
- 9V alkaline battery (500mAh): ~3-5 hours
- USB power bank (10,000mAh): ~60+ hours
- LiPo battery (2000mAh): ~12-15 hours

## Assembly Instructions

### Step 1: Prepare Components
1. Unpack all components and verify against parts list
2. Download and install Arduino IDE
3. Install required libraries (see software setup guide)

### Step 2: Basic Circuit Assembly
1. Connect MyoWare sensor to Arduino:
   - Red wire (VCC) to 5V pin
   - Black wire (GND) to GND pin
   - Blue wire (SIG) to analog pin A0

2. For multiple channels, repeat for A1, A2, A3

3. Connect electrodes to MyoWare sensor:
   - Center snap: Signal electrode
   - End snaps: Reference electrodes

### Step 3: Electrode Preparation
1. If using dry electrodes, ensure clean contact surfaces
2. For gel electrodes, remove backing and apply gel
3. Prepare electrode cables with appropriate connectors

### Step 4: Software Upload
1. Open Arduino IDE
2. Load the EMG acquisition sketch
3. Select correct board and port
4. Upload firmware to Arduino

### Step 5: Initial Testing
1. Connect electrodes to test subject
2. Open Arduino Serial Monitor
3. Verify signal acquisition
4. Test with jaw clenching and relaxation

## Troubleshooting

### Common Issues

**No Signal Detected**
- Check electrode connections
- Verify skin contact
- Test with multimeter for continuity
- Ensure proper power supply

**Noisy Signal**
- Improve electrode contact
- Check for loose connections
- Move away from electrical interference
- Verify proper grounding

**Inconsistent Readings**
- Stabilize electrode placement
- Check for movement artifacts
- Verify consistent skin preparation
- Consider electrode replacement

**Power Issues**
- Check battery voltage
- Verify power connections
- Monitor current consumption
- Consider power supply upgrade

### Signal Quality Optimization

1. **Electrode Contact**
   - Use conductive gel or paste
   - Ensure firm but comfortable pressure
   - Replace electrodes if signal degrades

2. **Noise Reduction**
   - Use shielded cables
   - Implement proper grounding
   - Filter power supply lines
   - Minimize cable movement

3. **Amplifier Settings**
   - Adjust gain for optimal signal range
   - Set appropriate filter cutoffs
   - Balance sensitivity vs. noise

## Safety Considerations

### Electrical Safety
- Use battery power for isolation from mains
- Implement current limiting resistors
- Consider medical-grade isolation amplifiers
- Never exceed 10µA of current through body

### Skin Safety
- Use hypoallergenic electrodes
- Limit continuous wear time
- Monitor for skin irritation
- Clean electrodes between uses

### User Comfort
- Ensure secure but not tight electrode placement
- Use soft, flexible cables
- Design ergonomic wearable form factor
- Provide easy on/off mechanism

## Maintenance

### Regular Maintenance
- Clean electrodes after each use
- Check cable integrity
- Verify connection tightness
- Monitor battery levels

### Electrode Care
- Store dry electrodes in clean, dry environment
- Replace gel electrodes after single use
- Clean reusable electrodes with alcohol
- Inspect for corrosion or damage

### System Calibration
- Perform baseline calibration before each session
- Record noise floor measurements
- Document electrode placement for consistency
- Maintain calibration logs

## Upgrades and Modifications

### Performance Improvements
- Add more EMG channels for better accuracy
- Implement wireless data transmission
- Integrate real-time signal processing
- Add visual feedback displays

### Form Factor Enhancements
- Design custom 3D-printed enclosures
- Implement flexible PCB designs
- Create comfortable headset mounting
- Add quick-connect electrode systems

### Advanced Features
- Integrate EEG channels for hybrid BCI
- Add accelerometer for motion detection
- Implement adaptive filtering algorithms
- Create smartphone app interface

This hardware guide provides the foundation for building your Open-Altergo system. Start with the basic setup and gradually add advanced features as you gain experience with the technology.
