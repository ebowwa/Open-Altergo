#!/usr/bin/env python3
"""
Open-Altergo Training Data Collection Script

This script helps users collect labeled EMG training data for their personal
silent speech recognition model. It guides through the data collection process
and saves the data in a format suitable for machine learning training.

Usage:
    python collect_training_data.py --port /dev/ttyUSB0 --words "hello,world,yes,no"
"""

import argparse
import os
import sys
import time
import json
import csv
from datetime import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.signal_processing.emg_processor import EMGProcessor


class TrainingDataCollector:
    def __init__(self, port='/dev/ttyUSB0', output_dir='data/datasets'):
        """
        Initialize training data collector
        
        Args:
            port: Serial port for Arduino connection
            output_dir: Directory to save training data
        """
        self.processor = EMGProcessor(port=port)
        self.output_dir = output_dir
        self.session_data = []
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metadata = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'port': port,
            'sample_rate': self.processor.sample_rate,
            'channels': self.processor.channels
        }
        
    def collect_word_samples(self, word, num_samples=50, rest_time=2):
        """
        Collect EMG samples for a specific word
        
        Args:
            word: Word to collect samples for
            num_samples: Number of samples to collect
            rest_time: Rest time between samples (seconds)
        """
        print(f"\n=== Collecting samples for word: '{word}' ===")
        print(f"Target: {num_samples} samples")
        print("Instructions:")
        print("- When prompted, silently mouth the word (no sound)")
        print("- Move your jaw and mouth muscles as if speaking")
        print("- Keep the movement consistent each time")
        print("- Press Enter when ready for each sample")
        print("- Type 'skip' to skip a sample")
        print("- Type 'done' to finish early")
        
        input("\nPress Enter to start collecting samples...")
        
        word_samples = []
        
        for i in range(num_samples):
            print(f"\nSample {i+1}/{num_samples} for '{word}'")
            
            user_input = input("Press Enter to record (or 'skip'/'done'): ").strip().lower()
            
            if user_input == 'done':
                print("Finishing early as requested")
                break
            elif user_input == 'skip':
                print("Skipping this sample")
                continue
                
            print("Get ready...")
            for countdown in range(3, 0, -1):
                print(f"{countdown}...")
                time.sleep(1)
                
            print(f"NOW: Silently mouth '{word}'")
            
            sample_data = self._record_sample(duration=1.0)
            
            if sample_data:
                sample_entry = {
                    'word': word,
                    'sample_id': f"{word}_{i+1}",
                    'timestamp': time.time(),
                    'features': sample_data['features'],
                    'raw_data': sample_data['raw_data'],
                    'filtered_data': sample_data['filtered_data']
                }
                
                word_samples.append(sample_entry)
                self.session_data.append(sample_entry)
                
                print(f"✓ Sample recorded successfully")
            else:
                print("✗ Failed to record sample")
                
            if i < num_samples - 1:  # Don't rest after last sample
                print(f"Rest for {rest_time} seconds...")
                time.sleep(rest_time)
                
        print(f"\nCompleted collection for '{word}': {len(word_samples)} samples")
        return word_samples
        
    def _record_sample(self, duration=1.0):
        """Record a single EMG sample"""
        self.processor.data_queue.queue.clear()
        
        start_time = time.time()
        collected_features = []
        
        while time.time() - start_time < duration:
            features = self.processor.get_latest_features()
            if features:
                collected_features.append(features)
            time.sleep(0.01)  # Small delay to prevent busy waiting
            
        if collected_features:
            avg_features = self._average_features(collected_features)
            return avg_features
        else:
            return None
            
    def _average_features(self, feature_list):
        """Average features over multiple time windows"""
        if not feature_list:
            return None
            
        avg_raw = [[] for _ in range(self.processor.channels)]
        avg_filtered = [[] for _ in range(self.processor.channels)]
        avg_features = [{} for _ in range(self.processor.channels)]
        
        for sample in feature_list:
            for ch in range(self.processor.channels):
                if ch < len(sample['raw_data']):
                    avg_raw[ch].extend(sample['raw_data'][ch])
                if ch < len(sample['filtered_data']):
                    avg_filtered[ch].extend(sample['filtered_data'][ch])
                    
        feature_keys = feature_list[0]['features'][0].keys()
        for ch in range(self.processor.channels):
            for key in feature_keys:
                values = [sample['features'][ch][key] for sample in feature_list 
                         if ch < len(sample['features'])]
                avg_features[ch][key] = np.mean(values) if values else 0.0
                
        return {
            'raw_data': avg_raw,
            'filtered_data': avg_filtered,
            'features': avg_features
        }
        
    def collect_rest_samples(self, num_samples=20):
        """Collect baseline/rest samples (no speech)"""
        print("\n=== Collecting baseline/rest samples ===")
        print("Instructions:")
        print("- Stay completely relaxed")
        print("- Don't move your jaw or mouth")
        print("- Breathe normally")
        
        input("Press Enter to start collecting rest samples...")
        
        rest_samples = []
        
        for i in range(num_samples):
            print(f"Rest sample {i+1}/{num_samples}")
            print("Stay relaxed...")
            
            time.sleep(1)  # Give time to relax
            
            sample_data = self._record_sample(duration=1.0)
            
            if sample_data:
                sample_entry = {
                    'word': 'rest',
                    'sample_id': f"rest_{i+1}",
                    'timestamp': time.time(),
                    'features': sample_data['features'],
                    'raw_data': sample_data['raw_data'],
                    'filtered_data': sample_data['filtered_data']
                }
                
                rest_samples.append(sample_entry)
                self.session_data.append(sample_entry)
                
            time.sleep(0.5)  # Brief pause between samples
            
        print(f"Completed rest sample collection: {len(rest_samples)} samples")
        return rest_samples
        
    def save_session_data(self):
        """Save collected data to files"""
        if not self.session_data:
            print("No data to save")
            return
            
        session_dir = os.path.join(self.output_dir, f"session_{self.session_id}")
        os.makedirs(session_dir, exist_ok=True)
        
        metadata_file = os.path.join(session_dir, "metadata.json")
        self.metadata['num_samples'] = len(self.session_data)
        self.metadata['words'] = list(set(sample['word'] for sample in self.session_data))
        
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
        raw_data_file = os.path.join(session_dir, "raw_data.json")
        with open(raw_data_file, 'w') as f:
            json.dump(self.session_data, f, indent=2, default=str)
            
        features_file = os.path.join(session_dir, "features.csv")
        self._save_features_csv(features_file)
        
        print(f"\nSession data saved to: {session_dir}")
        print(f"Files created:")
        print(f"  - metadata.json: Session information")
        print(f"  - raw_data.json: Complete raw data")
        print(f"  - features.csv: Features for ML training")
        
        return session_dir
        
    def _save_features_csv(self, filepath):
        """Save features in CSV format for machine learning"""
        if not self.session_data:
            return
            
        feature_names = []
        for ch in range(self.processor.channels):
            for key in self.session_data[0]['features'][ch].keys():
                feature_names.append(f"ch{ch}_{key}")
                
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            header = ['word', 'sample_id', 'timestamp'] + feature_names
            writer.writerow(header)
            
            for sample in self.session_data:
                row = [sample['word'], sample['sample_id'], sample['timestamp']]
                
                for ch in range(self.processor.channels):
                    for key in self.session_data[0]['features'][ch].keys():
                        if ch < len(sample['features']):
                            row.append(sample['features'][ch][key])
                        else:
                            row.append(0.0)
                            
                writer.writerow(row)
                
    def run_collection_session(self, words, samples_per_word=50):
        """Run complete data collection session"""
        print("=== Open-Altergo Training Data Collection ===")
        print(f"Session ID: {self.session_id}")
        print(f"Words to collect: {words}")
        print(f"Samples per word: {samples_per_word}")
        
        if not self.processor.start_recording():
            print("Failed to connect to Arduino. Check connection and port.")
            return False
            
        try:
            self.collect_rest_samples(num_samples=20)
            
            for word in words:
                self.collect_word_samples(word, num_samples=samples_per_word)
                
                if word != words[-1]:  # Not the last word
                    print(f"\nTake a break before next word...")
                    input("Press Enter when ready to continue...")
                    
            session_dir = self.save_session_data()
            
            print(f"\n=== Collection Complete ===")
            print(f"Total samples collected: {len(self.session_data)}")
            print(f"Data saved to: {session_dir}")
            print("\nNext steps:")
            print("1. Review the collected data")
            print("2. Run training script: python scripts/train_model.py")
            print("3. Test your model: python scripts/realtime_recognition.py")
            
            return True
            
        except KeyboardInterrupt:
            print("\nCollection interrupted by user")
            if self.session_data:
                print("Saving partial data...")
                self.save_session_data()
            return False
            
        finally:
            self.processor.stop_recording()


def main():
    parser = argparse.ArgumentParser(description="Collect EMG training data for Open-Altergo")
    parser.add_argument('--port', default='/dev/ttyUSB0', 
                       help='Serial port for Arduino (default: /dev/ttyUSB0)')
    parser.add_argument('--words', required=True,
                       help='Comma-separated list of words to collect (e.g., "hello,world,yes,no")')
    parser.add_argument('--samples', type=int, default=50,
                       help='Number of samples per word (default: 50)')
    parser.add_argument('--output', default='data/datasets',
                       help='Output directory for training data (default: data/datasets)')
    
    args = parser.parse_args()
    
    words = [word.strip().lower() for word in args.words.split(',')]
    
    print(f"Collecting data for words: {words}")
    print(f"Arduino port: {args.port}")
    print(f"Samples per word: {args.samples}")
    print(f"Output directory: {args.output}")
    
    collector = TrainingDataCollector(port=args.port, output_dir=args.output)
    
    success = collector.run_collection_session(words, samples_per_word=args.samples)
    
    if success:
        print("Data collection completed successfully!")
        return 0
    else:
        print("Data collection failed or was interrupted")
        return 1


if __name__ == "__main__":
    exit(main())
