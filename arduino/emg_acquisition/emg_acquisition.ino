/*
 * Open-Altergo EMG Signal Acquisition
 * 
 * This Arduino sketch captures EMG signals from MyoWare sensors
 * and streams the data to a connected computer for processing.
 * 
 * Hardware Setup:
 * - MyoWare Muscle Sensor connected to analog pin A0
 * - Additional sensors can be connected to A1, A2, A3 for multi-channel
 * - Power: 5V and GND connections
 * 
 * Signal Processing:
 * - Samples at 1000Hz for EMG frequency range
 * - Basic filtering and amplification
 * - Serial output for Python processing
 */

const int EMG_PIN_1 = A0;  // Primary EMG sensor (jaw/masseter)
const int EMG_PIN_2 = A1;  // Secondary sensor (neck/sternocleidomastoid)
const int EMG_PIN_3 = A2;  // Optional third sensor (cheek)
const int EMG_PIN_4 = A3;  // Optional fourth sensor (under chin)

const int SAMPLE_RATE = 1000;  // 1kHz sampling rate for EMG
const int SAMPLE_DELAY = 1000 / SAMPLE_RATE;  // 1ms delay between samples

const int BUFFER_SIZE = 10;
int emg_buffer_1[BUFFER_SIZE];
int emg_buffer_2[BUFFER_SIZE];
int emg_buffer_3[BUFFER_SIZE];
int emg_buffer_4[BUFFER_SIZE];
int buffer_index = 0;

unsigned long last_sample_time = 0;
bool multi_channel = true;  // Set to false for single channel operation

void setup() {
  Serial.begin(115200);  // High baud rate for fast data transmission
  
  // Initialize analog pins
  pinMode(EMG_PIN_1, INPUT);
  pinMode(EMG_PIN_2, INPUT);
  pinMode(EMG_PIN_3, INPUT);
  pinMode(EMG_PIN_4, INPUT);
  
  // Initialize buffers
  for (int i = 0; i < BUFFER_SIZE; i++) {
    emg_buffer_1[i] = 0;
    emg_buffer_2[i] = 0;
    emg_buffer_3[i] = 0;
    emg_buffer_4[i] = 0;
  }
  
  Serial.println("Open-Altergo EMG Acquisition Started");
  Serial.println("Format: timestamp,emg1,emg2,emg3,emg4");
  
  delay(1000);  // Allow sensors to stabilize
}

void loop() {
  unsigned long current_time = millis();
  
  // Sample at consistent rate
  if (current_time - last_sample_time >= SAMPLE_DELAY) {
    // Read EMG values (0-1023 from 10-bit ADC)
    int emg1 = analogRead(EMG_PIN_1);
    int emg2 = multi_channel ? analogRead(EMG_PIN_2) : 0;
    int emg3 = multi_channel ? analogRead(EMG_PIN_3) : 0;
    int emg4 = multi_channel ? analogRead(EMG_PIN_4) : 0;
    
    // Apply basic smoothing filter
    emg_buffer_1[buffer_index] = emg1;
    emg_buffer_2[buffer_index] = emg2;
    emg_buffer_3[buffer_index] = emg3;
    emg_buffer_4[buffer_index] = emg4;
    
    buffer_index = (buffer_index + 1) % BUFFER_SIZE;
    
    // Calculate moving average for noise reduction
    int avg1 = calculateAverage(emg_buffer_1);
    int avg2 = calculateAverage(emg_buffer_2);
    int avg3 = calculateAverage(emg_buffer_3);
    int avg4 = calculateAverage(emg_buffer_4);
    
    // Output data in CSV format: timestamp,emg1,emg2,emg3,emg4
    Serial.print(current_time);
    Serial.print(",");
    Serial.print(avg1);
    Serial.print(",");
    Serial.print(avg2);
    Serial.print(",");
    Serial.print(avg3);
    Serial.print(",");
    Serial.println(avg4);
    
    last_sample_time = current_time;
  }
  
  // Handle serial commands for configuration
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "SINGLE") {
      multi_channel = false;
      Serial.println("Switched to single channel mode");
    } else if (command == "MULTI") {
      multi_channel = true;
      Serial.println("Switched to multi-channel mode");
    } else if (command == "STATUS") {
      Serial.print("Mode: ");
      Serial.println(multi_channel ? "Multi-channel" : "Single channel");
      Serial.print("Sample rate: ");
      Serial.print(SAMPLE_RATE);
      Serial.println(" Hz");
    }
  }
}

int calculateAverage(int buffer[]) {
  long sum = 0;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    sum += buffer[i];
  }
  return sum / BUFFER_SIZE;
}

// Calibration function - call this to establish baseline
void calibrateBaseline() {
  Serial.println("Calibrating baseline - stay relaxed for 5 seconds");
  delay(1000);
  
  long sum1 = 0, sum2 = 0, sum3 = 0, sum4 = 0;
  int samples = 0;
  
  unsigned long cal_start = millis();
  while (millis() - cal_start < 5000) {  // 5 second calibration
    if (millis() - last_sample_time >= SAMPLE_DELAY) {
      sum1 += analogRead(EMG_PIN_1);
      sum2 += analogRead(EMG_PIN_2);
      sum3 += analogRead(EMG_PIN_3);
      sum4 += analogRead(EMG_PIN_4);
      samples++;
      last_sample_time = millis();
    }
  }
  
  int baseline1 = sum1 / samples;
  int baseline2 = sum2 / samples;
  int baseline3 = sum3 / samples;
  int baseline4 = sum4 / samples;
  
  Serial.print("Baseline values: ");
  Serial.print(baseline1);
  Serial.print(",");
  Serial.print(baseline2);
  Serial.print(",");
  Serial.print(baseline3);
  Serial.print(",");
  Serial.println(baseline4);
}
