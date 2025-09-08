"""
Open-Altergo EMG Signal Processing Module

This module handles real-time EMG signal processing including:
- Serial communication with Arduino
- Digital signal processing (filtering, amplification)
- Feature extraction for machine learning
- Real-time visualization

Based on research from MIT AlterEgo project and EMG signal processing literature.
"""

import numpy as np
import serial
import time
from scipy import signal
from scipy.signal import butter, filtfilt, iirnotch
from sklearn.decomposition import FastICA
import matplotlib.pyplot as plt
from collections import deque
import threading
import queue


class EMGProcessor:
    def __init__(self, port='/dev/ttyUSB0', baud_rate=115200, sample_rate=1000):
        """
        Initialize EMG processor with Arduino connection
        
        Args:
            port: Serial port for Arduino connection
            baud_rate: Serial communication speed
            sample_rate: Expected sampling rate from Arduino (Hz)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.sample_rate = sample_rate
        self.serial_connection = None
        
        self.buffer_size = 1000  # 1 second of data
        self.channels = 4  # Number of EMG channels
        
        self.raw_buffers = [deque(maxlen=self.buffer_size) for _ in range(self.channels)]
        self.filtered_buffers = [deque(maxlen=self.buffer_size) for _ in range(self.channels)]
        
        self.lowcut = 20.0
        self.highcut = 500.0
        self.notch_freq = 60.0  # Power line frequency (50Hz in Europe)
        self.quality_factor = 30
        
        self._design_filters()
        
        self.window_size = 250  # 250ms windows for feature extraction
        self.overlap = 125      # 50% overlap
        
        self.data_queue = queue.Queue()
        self.is_recording = False
        
    def _design_filters(self):
        """Design digital filters for EMG signal processing"""
        nyquist = 0.5 * self.sample_rate
        
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        self.bp_b, self.bp_a = butter(4, [low, high], btype='band')
        
        self.notch_b, self.notch_a = iirnotch(self.notch_freq, self.quality_factor, self.sample_rate)
        
    def connect_arduino(self):
        """Establish serial connection with Arduino"""
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset
            print(f"Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
            
    def disconnect_arduino(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Disconnected from Arduino")
            
    def read_serial_data(self):
        """Read and parse data from Arduino"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
            
        try:
            line = self.serial_connection.readline().decode('utf-8').strip()
            if line and ',' in line:
                parts = line.split(',')
                if len(parts) == 5:  # timestamp + 4 EMG channels
                    timestamp = int(parts[0])
                    emg_values = [int(parts[i]) for i in range(1, 5)]
                    return timestamp, emg_values
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error parsing serial data: {e}")
        return None
        
    def apply_filters(self, signal_data):
        """Apply band-pass and notch filters to EMG signal"""
        signal_array = np.array(signal_data)
        
        filtered = filtfilt(self.bp_b, self.bp_a, signal_array)
        
        filtered = filtfilt(self.notch_b, self.notch_a, filtered)
        
        return filtered
        
    def extract_features(self, signal_window):
        """
        Extract features from EMG signal window for machine learning
        
        Args:
            signal_window: Array of EMG samples
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        features['rms'] = np.sqrt(np.mean(signal_window**2))
        features['mean_absolute'] = np.mean(np.abs(signal_window))
        features['variance'] = np.var(signal_window)
        features['zero_crossings'] = np.sum(np.diff(np.sign(signal_window)) != 0)
        
        fft = np.fft.fft(signal_window)
        freqs = np.fft.fftfreq(len(signal_window), 1/self.sample_rate)
        power_spectrum = np.abs(fft)**2
        
        features['spectral_centroid'] = np.sum(freqs[:len(freqs)//2] * power_spectrum[:len(freqs)//2]) / np.sum(power_spectrum[:len(freqs)//2])
        features['spectral_bandwidth'] = np.sqrt(np.sum(((freqs[:len(freqs)//2] - features['spectral_centroid'])**2) * power_spectrum[:len(freqs)//2]) / np.sum(power_spectrum[:len(freqs)//2]))
        
        features['low_freq_power'] = np.sum(power_spectrum[(freqs >= 20) & (freqs <= 100)])
        features['mid_freq_power'] = np.sum(power_spectrum[(freqs >= 100) & (freqs <= 300)])
        features['high_freq_power'] = np.sum(power_spectrum[(freqs >= 300) & (freqs <= 500)])
        
        return features
        
    def apply_ica(self, multi_channel_data):
        """
        Apply Independent Component Analysis to separate signal sources
        
        Args:
            multi_channel_data: Array of shape (n_channels, n_samples)
            
        Returns:
            Separated signal components
        """
        if multi_channel_data.shape[0] < 2:
            return multi_channel_data
            
        ica = FastICA(n_components=multi_channel_data.shape[0], random_state=42)
        separated_signals = ica.fit_transform(multi_channel_data.T).T
        
        return separated_signals
        
    def start_recording(self):
        """Start real-time data recording and processing"""
        if not self.connect_arduino():
            return False
            
        self.is_recording = True
        
        collection_thread = threading.Thread(target=self._data_collection_loop)
        collection_thread.daemon = True
        collection_thread.start()
        
        print("Started EMG recording")
        return True
        
    def stop_recording(self):
        """Stop data recording"""
        self.is_recording = False
        self.disconnect_arduino()
        print("Stopped EMG recording")
        
    def _data_collection_loop(self):
        """Main data collection loop running in separate thread"""
        while self.is_recording:
            data = self.read_serial_data()
            if data:
                timestamp, emg_values = data
                
                for i, value in enumerate(emg_values):
                    self.raw_buffers[i].append(value)
                
                if len(self.raw_buffers[0]) >= self.window_size:
                    self._process_window()
                    
    def _process_window(self):
        """Process current window of EMG data"""
        windows = []
        for i in range(self.channels):
            if len(self.raw_buffers[i]) >= self.window_size:
                window = list(self.raw_buffers[i])[-self.window_size:]
                windows.append(window)
        
        if len(windows) == self.channels:
            filtered_windows = []
            for window in windows:
                filtered = self.apply_filters(window)
                filtered_windows.append(filtered)
            
            multi_channel_array = np.array(filtered_windows)
            separated = self.apply_ica(multi_channel_array)
            
            features_list = []
            for component in separated:
                features = self.extract_features(component)
                features_list.append(features)
            
            self.data_queue.put({
                'timestamp': time.time(),
                'raw_data': windows,
                'filtered_data': filtered_windows,
                'separated_data': separated,
                'features': features_list
            })
            
    def get_latest_features(self):
        """Get the most recent feature vector for classification"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
            
    def visualize_signals(self, duration=5):
        """
        Real-time visualization of EMG signals
        
        Args:
            duration: Duration to display (seconds)
        """
        plt.ion()
        fig, axes = plt.subplots(self.channels, 1, figsize=(12, 8))
        if self.channels == 1:
            axes = [axes]
            
        lines_raw = []
        lines_filtered = []
        
        for i in range(self.channels):
            line_raw, = axes[i].plot([], [], 'b-', label='Raw', alpha=0.7)
            line_filtered, = axes[i].plot([], [], 'r-', label='Filtered', linewidth=2)
            lines_raw.append(line_raw)
            lines_filtered.append(line_filtered)
            
            axes[i].set_ylabel(f'EMG {i+1}')
            axes[i].legend()
            axes[i].grid(True)
            
        axes[-1].set_xlabel('Time (s)')
        plt.tight_layout()
        
        start_time = time.time()
        while time.time() - start_time < duration and self.is_recording:
            current_time = time.time() - start_time
            
            for i in range(self.channels):
                if len(self.raw_buffers[i]) > 0:
                    time_axis = np.linspace(current_time - len(self.raw_buffers[i])/self.sample_rate, 
                                          current_time, len(self.raw_buffers[i]))
                    
                    lines_raw[i].set_data(time_axis, list(self.raw_buffers[i]))
                    
                    if len(self.filtered_buffers[i]) > 0:
                        lines_filtered[i].set_data(time_axis[-len(self.filtered_buffers[i]):], 
                                                 list(self.filtered_buffers[i]))
                    
                    axes[i].relim()
                    axes[i].autoscale_view()
            
            plt.pause(0.01)
            
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    processor = EMGProcessor(port='/dev/ttyUSB0')  # Adjust port as needed
    
    try:
        if processor.start_recording():
            print("Recording EMG signals. Press Ctrl+C to stop.")
            
            processor.visualize_signals(duration=10)
            
            for _ in range(100):
                features = processor.get_latest_features()
                if features:
                    print(f"Features extracted at {features['timestamp']}")
                    for i, feature_dict in enumerate(features['features']):
                        print(f"  Channel {i}: RMS={feature_dict['rms']:.3f}")
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        processor.stop_recording()
