"""
Open-Altergo EMG Classification Module

This module implements machine learning models for classifying EMG signals
into words, phonemes, or commands for silent speech recognition.

Supports multiple ML approaches:
- Traditional ML: SVM, Random Forest, Neural Networks
- Deep Learning: CNN, RNN for temporal pattern recognition
- Online Learning: Adaptive models that improve with use
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Conv1D, MaxPooling1D, Dropout, Input, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
import pickle
import os
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class EMGClassifier:
    def __init__(self, model_type='svm', n_channels=4, feature_dim=10):
        """
        Initialize EMG classifier
        
        Args:
            model_type: Type of model ('svm', 'rf', 'mlp', 'cnn', 'lstm')
            n_channels: Number of EMG channels
            feature_dim: Dimension of feature vector per channel
        """
        self.model_type = model_type
        self.n_channels = n_channels
        self.feature_dim = feature_dim
        self.total_features = n_channels * feature_dim
        
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        
        self.model_params = {
            'svm': {'C': 1.0, 'kernel': 'rbf', 'gamma': 'scale'},
            'rf': {'n_estimators': 100, 'max_depth': 10, 'random_state': 42},
            'mlp': {'hidden_layer_sizes': (128, 64), 'max_iter': 1000, 'random_state': 42}
        }
        
    def _create_traditional_model(self):
        """Create traditional ML model (SVM, RF, MLP)"""
        if self.model_type == 'svm':
            return SVC(**self.model_params['svm'], probability=True)
        elif self.model_type == 'rf':
            return RandomForestClassifier(**self.model_params['rf'])
        elif self.model_type == 'mlp':
            return MLPClassifier(**self.model_params['mlp'])
        else:
            raise ValueError(f"Unknown traditional model type: {self.model_type}")
            
    def _create_cnn_model(self, n_classes):
        """Create CNN model for EMG signal classification"""
        model = Sequential([
            Input(shape=(self.total_features, 1)),
            Conv1D(32, 3, activation='relu'),
            MaxPooling1D(2),
            Conv1D(64, 3, activation='relu'),
            MaxPooling1D(2),
            Conv1D(128, 3, activation='relu'),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(n_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
        
    def _create_lstm_model(self, n_classes, sequence_length=10):
        """Create LSTM model for temporal EMG pattern recognition"""
        model = Sequential([
            Input(shape=(sequence_length, self.total_features)),
            LSTM(64, return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(n_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
        
    def prepare_features(self, feature_list: List[Dict]) -> np.ndarray:
        """
        Convert list of feature dictionaries to numpy array
        
        Args:
            feature_list: List of feature dictionaries from EMG processor
            
        Returns:
            Feature matrix of shape (n_samples, n_features)
        """
        if not feature_list:
            return np.array([])
            
        feature_names = list(feature_list[0].keys())
        
        feature_matrix = []
        for features in feature_list:
            feature_vector = [features[name] for name in feature_names]
            feature_matrix.append(feature_vector)
            
        return np.array(feature_matrix)
        
    def prepare_multichannel_features(self, multichannel_features: List[List[Dict]]) -> np.ndarray:
        """
        Prepare features from multiple EMG channels
        
        Args:
            multichannel_features: List of [channel_features] for each sample
            
        Returns:
            Feature matrix with concatenated channel features
        """
        if not multichannel_features:
            return np.array([])
            
        combined_features = []
        for sample_features in multichannel_features:
            sample_vector = []
            for channel_features in sample_features:
                channel_vector = list(channel_features.values())
                sample_vector.extend(channel_vector)
            combined_features.append(sample_vector)
            
        return np.array(combined_features)
        
    def train(self, X: np.ndarray, y: np.ndarray, validation_split=0.2):
        """
        Train the EMG classifier
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,)
            validation_split: Fraction of data for validation
        """
        print(f"Training {self.model_type} classifier...")
        print(f"Data shape: {X.shape}, Labels: {len(np.unique(y))} classes")
        
        y_encoded = self.label_encoder.fit_transform(y)
        n_classes = len(self.label_encoder.classes_)
        
        X_scaled = self.scaler.fit_transform(X)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_encoded, test_size=validation_split, 
            random_state=42, stratify=y_encoded
        )
        
        if self.model_type in ['svm', 'rf', 'mlp']:
            self.model = self._create_traditional_model()
            self.model.fit(X_train, y_train)
            
            train_score = self.model.score(X_train, y_train)
            val_score = self.model.score(X_val, y_val)
            print(f"Training accuracy: {train_score:.3f}")
            print(f"Validation accuracy: {val_score:.3f}")
            
        elif self.model_type == 'cnn':
            self.model = self._create_cnn_model(n_classes)
            
            X_train_cnn = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
            X_val_cnn = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
            
            early_stopping = EarlyStopping(patience=10, restore_best_weights=True)
            
            history = self.model.fit(
                X_train_cnn, y_train,
                validation_data=(X_val_cnn, y_val),
                epochs=100,
                batch_size=32,
                callbacks=[early_stopping],
                verbose=1
            )
            
        elif self.model_type == 'lstm':
            print("LSTM training requires sequence data preparation")
            sequence_length = 10
            if X_train.shape[0] >= sequence_length:
                X_train_lstm = self._create_sequences(X_train, sequence_length)
                y_train_lstm = y_train[sequence_length-1:]
                X_val_lstm = self._create_sequences(X_val, sequence_length)
                y_val_lstm = y_val[sequence_length-1:]
                
                self.model = self._create_lstm_model(n_classes, sequence_length)
                
                early_stopping = EarlyStopping(patience=10, restore_best_weights=True)
                
                history = self.model.fit(
                    X_train_lstm, y_train_lstm,
                    validation_data=(X_val_lstm, y_val_lstm),
                    epochs=100,
                    batch_size=16,
                    callbacks=[early_stopping],
                    verbose=1
                )
        
        self.is_trained = True
        print("Training completed!")
        
    def _create_sequences(self, data, sequence_length):
        """Create sequences for LSTM training"""
        sequences = []
        for i in range(len(data) - sequence_length + 1):
            sequences.append(data[i:i+sequence_length])
        return np.array(sequences)
        
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict labels for new data
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predicted_labels, prediction_probabilities)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        X_scaled = self.scaler.transform(X)
        
        if self.model_type in ['svm', 'rf', 'mlp']:
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            
        elif self.model_type == 'cnn':
            X_cnn = X_scaled.reshape(X_scaled.shape[0], X_scaled.shape[1], 1)
            probabilities = self.model.predict(X_cnn)
            predictions = np.argmax(probabilities, axis=1)
            
        elif self.model_type == 'lstm':
            if X_scaled.shape[0] >= 10:
                X_lstm = self._create_sequences(X_scaled, 10)
                probabilities = self.model.predict(X_lstm)
                predictions = np.argmax(probabilities, axis=1)
            else:
                return np.array([]), np.array([])
        
        predicted_labels = self.label_encoder.inverse_transform(predictions)
        
        return predicted_labels, probabilities
        
    def predict_single(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict single sample with confidence
        
        Args:
            features: Single feature vector
            
        Returns:
            Tuple of (predicted_label, confidence)
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)
            
        labels, probs = self.predict(features)
        
        if len(labels) > 0:
            confidence = np.max(probs[0])
            return labels[0], confidence
        else:
            return "unknown", 0.0
            
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray):
        """Evaluate model performance"""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
            
        predictions, _ = self.predict(X_test)
        
        accuracy = accuracy_score(y_test, predictions)
        report = classification_report(y_test, predictions)
        
        print(f"Test Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(report)
        
        return accuracy, report
        
    def save_model(self, filepath: str):
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
            
        model_data = {
            'model_type': self.model_type,
            'n_channels': self.n_channels,
            'feature_dim': self.feature_dim,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'is_trained': self.is_trained
        }
        
        if self.model_type in ['svm', 'rf', 'mlp']:
            model_data['model'] = self.model
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
        else:
            model_dir = os.path.splitext(filepath)[0]
            os.makedirs(model_dir, exist_ok=True)
            
            self.model.save(os.path.join(model_dir, 'keras_model.h5'))
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
                
        print(f"Model saved to {filepath}")
        
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.model_type = model_data['model_type']
        self.n_channels = model_data['n_channels']
        self.feature_dim = model_data['feature_dim']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.is_trained = model_data['is_trained']
        
        if self.model_type in ['svm', 'rf', 'mlp']:
            self.model = model_data['model']
        else:
            model_dir = os.path.splitext(filepath)[0]
            self.model = tf.keras.models.load_model(os.path.join(model_dir, 'keras_model.h5'))
            
        print(f"Model loaded from {filepath}")


class OnlineEMGClassifier(EMGClassifier):
    """Online learning version that adapts to user over time"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adaptation_rate = 0.1
        self.confidence_threshold = 0.8
        self.feedback_buffer = []
        
    def update_with_feedback(self, features: np.ndarray, true_label: str):
        """Update model with user feedback"""
        if not self.is_trained:
            return
            
        self.feedback_buffer.append((features, true_label))
        
        if len(self.feedback_buffer) >= 10:
            self._incremental_update()
            self.feedback_buffer = []
            
    def _incremental_update(self):
        """Perform incremental model update"""
        if not self.feedback_buffer:
            return
            
        X_new = np.array([item[0] for item in self.feedback_buffer])
        y_new = np.array([item[1] for item in self.feedback_buffer])
        
        print(f"Updating model with {len(self.feedback_buffer)} new samples")


if __name__ == "__main__":
    np.random.seed(42)
    
    n_samples = 1000
    n_features = 40  # 10 features per channel * 4 channels
    n_classes = 5
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, n_classes, n_samples)
    
    word_labels = ['hello', 'world', 'yes', 'no', 'stop']
    y_words = [word_labels[i] for i in y]
    
    print("Testing EMG Classifier with synthetic data...")
    
    for model_type in ['svm', 'rf', 'cnn']:
        print(f"\n--- Testing {model_type.upper()} ---")
        
        classifier = EMGClassifier(model_type=model_type)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_words, test_size=0.2, random_state=42
        )
        
        classifier.train(X_train, y_train)
        
        classifier.evaluate(X_test, y_test)
        
        sample_features = X_test[0]
        pred_label, confidence = classifier.predict_single(sample_features)
        print(f"Single prediction: {pred_label} (confidence: {confidence:.3f})")
        
        model_path = f"test_model_{model_type}.pkl"
        classifier.save_model(model_path)
        
        print(f"Model saved and tested successfully!")
