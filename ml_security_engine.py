"""
ML Security Engine for IoT DDoS Attack Detection
Real-time network traffic analysis using pre-trained ML models
"""

import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from collections import deque
import threading
import logging
import os
# Try to import simple DDoS detector, but make it optional
try:
    from simple_ddos_detector import SimpleDDoSDetector
    SIMPLE_DDOS_DETECTOR_AVAILABLE = True
except ImportError:
    SIMPLE_DDOS_DETECTOR_AVAILABLE = False
    SimpleDDoSDetector = None
    logger = logging.getLogger(__name__)
    logger.warning("Simple DDoS detector not available. Install or create simple_ddos_detector module.")

# Try to import TensorFlow, but make it optional
try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None
    logger = logging.getLogger(__name__)
    logger.warning("TensorFlow not available. ML model features will be limited.")

# Module-level constants for health checks
HEALTH_CHECK_INTERVAL = 60  # seconds
MAX_RELOAD_ATTEMPTS = 3
INIT_TIMEOUT = 30  # seconds

# Global ML engine instance placeholder (set by controller)
ml_engine = None

class MLSecurityEngine:
    def __init__(self, model_path="data/models/ddos_model_retrained"):
        """
        Initialize ML Security Engine with DDoS detection system
        
        Args:
            model_path: Path to model directory (containing config.json and model.weights.h5)
                       or path to .keras file for backward compatibility
        """
        self.model = None
        self.model_path = model_path
        self.is_loaded = False
        self.initialization_time = time.time()
        self.last_health_check = time.time()
        self.reload_attempts = 0
        self.health_check_thread = None
        self.is_running = True
        self.attack_detections = deque(maxlen=1000)  # Store last 1000 detections
        self.blocked_ips = {}  # Dictionary to track blocked IPs and their block duration
        
        # Initialize logging first (before using self.logger)
        self.logger = logging.getLogger(__name__)
        
        # Initialize the simple DDoS detector
        if SIMPLE_DDOS_DETECTOR_AVAILABLE and SimpleDDoSDetector:
            self.ddos_detector = SimpleDDoSDetector()
        else:
            self.ddos_detector = None
            self.logger.warning("Simple DDoS detector not available")
        
        # Statistics tracking
        self.detection_window = deque(maxlen=1000)  # Store recent detections for statistics
        self.last_processing_times = deque(maxlen=100)  # Store last 100 processing times
        self.false_positives = deque(maxlen=1000)  # Store known false positives
        
        self.network_stats = {
            'total_packets': 0,
            'attack_packets': 0,
            'normal_packets': 0,
            'attack_rate': 0.0,
            'detection_rate': 0.0,
            'false_positive_rate': 0.0,
            'model_confidence': 0.0,
            'processing_rate': 0.0,
            'uptime': 0,
            'last_health_check': None,
            'model_status': 'initializing'
        }
        self.real_time_features = deque(maxlen=100)  # Store last 100 feature vectors
        self.attack_types = {
            0: 'Normal',
            1: 'DDoS Attack',
            2: 'Botnet Attack',
            3: 'Flood Attack'
        }
        
        # Load the model
        if not self.load_model():
            self.logger.error("❌ Initial model load failed")
            return
            
        # Start health check thread
        self.start_health_checks()

    def start_health_checks(self):
        """Start periodic health checks"""
        def health_check_loop():
            while self.is_running:
                try:
                    self.check_health()
                    time.sleep(HEALTH_CHECK_INTERVAL)
                except Exception as e:
                    self.logger.error(f"Health check error: {e}")
                    time.sleep(5)  # Wait before retry
        
        self.health_check_thread = threading.Thread(
            target=health_check_loop,
            name="ML_HealthCheck",
            daemon=True
        )
        self.health_check_thread.start()

    def update_detection_stats(self, prediction_time):
        """
        Update detection statistics based on recent detections
        """
        try:
            current_time = time.time()
            window_start = current_time - 300  # 5 minutes window

            # Filter detections within the time window
            recent_detections = [d for d in self.detection_window 
                               if d['timestamp'] > window_start]

            if recent_detections:
                # Calculate detection rate
                total_detections = len(recent_detections)
                attack_detections = sum(1 for d in recent_detections 
                                     if d['type'] != 'Normal')
                
                self.network_stats['detection_rate'] = round(
                    (attack_detections / total_detections) * 100, 2)

                # Calculate false positive rate (if ground truth is available)
                false_positives = sum(1 for d in self.false_positives 
                                    if d > window_start)
                if attack_detections > 0:
                    self.network_stats['false_positive_rate'] = round(
                        (false_positives / attack_detections) * 100, 2)
                else:
                    self.network_stats['false_positive_rate'] = 0.0

                # Calculate average model confidence
                avg_confidence = np.mean([d['confidence'] for d in recent_detections])
                self.network_stats['model_confidence'] = round(avg_confidence, 2)

            # Update processing rate
            if self.last_processing_times:
                avg_processing_time = np.mean(self.last_processing_times)
                self.network_stats['processing_rate'] = round(
                    1.0 / avg_processing_time if avg_processing_time > 0 else 0, 2)
            
            # Update packet statistics
            self.network_stats['total_packets'] += 1
            if prediction_time is not None:
                self.last_processing_times.append(prediction_time)

        except Exception as e:
            self.logger.error(f"Error updating detection stats: {e}")

    def get_detection_stats(self):
        """Get current detection statistics"""
        return {
            'detection_rate': self.network_stats['detection_rate'],
            'false_positive_rate': self.network_stats['false_positive_rate'],
            'model_confidence': self.network_stats['model_confidence'],
            'processing_rate': self.network_stats['processing_rate'],
            'total_packets': self.network_stats['total_packets'],
            'attack_packets': self.network_stats['attack_packets'],
            'normal_packets': self.network_stats['normal_packets']
        }

    def check_health(self) -> bool:
        """
        Check ML engine health and reload if necessary
        Returns True if healthy, False otherwise
        """
        try:
            self.last_health_check = time.time()
            self.network_stats['last_health_check'] = datetime.now().isoformat()
            
            # Update uptime
            self.network_stats['uptime'] = time.time() - self.initialization_time
            
            # Check if model is loaded
            if not self.is_loaded or self.model is None:
                self.logger.warning("❗ Model not loaded during health check")
                if self.reload_attempts < MAX_RELOAD_ATTEMPTS:
                    self.reload_attempts += 1
                    self.logger.info(f"Attempting model reload ({self.reload_attempts}/{MAX_RELOAD_ATTEMPTS})")
                    return self.load_model()
                return False
            
            # Test model with dummy data
            test_input = np.random.rand(1, 77)  # Match model input shape
            try:
                _ = self.model.predict(test_input, verbose=0)
                self.network_stats['model_status'] = 'healthy'
                self.reload_attempts = 0  # Reset counter on successful predict
                return True
            except Exception as e:
                self.logger.error(f"Model prediction failed during health check: {e}")
                self.network_stats['model_status'] = 'error'
                return False
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.network_stats['model_status'] = 'error'
            return False
    
    def load_model(self):
        """
        Load the DDoS Detection Model from file
        Supports both directory format (config.json + model.weights.h5) and .keras format
        Returns True if successful, False otherwise
        """
        try:
            # Ensure logger is set (don't reset it)
            if not hasattr(self, 'logger') or self.logger is None:
                self.logger = logging.getLogger(__name__)
            
            self.logger.info("🤖 Loading DDoS Detection Model...")
            
            # Check if TensorFlow is available
            if not TENSORFLOW_AVAILABLE:
                self.logger.warning("TensorFlow not available, using simple detector only")
                self.is_loaded = True  # Mark as loaded but without ML model
                self.network_stats['model_status'] = 'simple_detector_only'
                return True
            
            import os
            model_path = self.model_path
            
            # Check if path is a directory (new format) or file (old format)
            if os.path.isdir(model_path):
                # New format: directory with config.json and model.weights.h5
                config_path = os.path.join(model_path, 'config.json')
                weights_path = os.path.join(model_path, 'model.weights.h5')
                
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Model config not found: {config_path}")
                if not os.path.exists(weights_path):
                    raise FileNotFoundError(f"Model weights not found: {weights_path}")
                
                # Load model from config and weights
                with open(config_path, 'r') as f:
                    model_config = json.load(f)
                
                # Reconstruct model from config
                if 'module' in model_config and model_config['module'] == 'keras':
                    try:
                        # Method 1: Try building model manually from config (most reliable)
                        from keras.models import Sequential
                        from keras.layers import Dense, Dropout
                        from keras.optimizers import Adam
                        
                        # Build model from config
                        model_config_obj = model_config.get('config', {})
                        layers_config = model_config_obj.get('layers', [])
                        
                        self.model = Sequential()
                        for layer_config in layers_config:
                            layer_class = layer_config.get('class_name', '')
                            layer_cfg = layer_config.get('config', {})
                            
                            if layer_class == 'InputLayer':
                                # Input layer is handled automatically by Sequential
                                continue
                            elif layer_class == 'Dense':
                                units = layer_cfg.get('units')
                                activation = layer_cfg.get('activation', 'linear')
                                self.model.add(Dense(units, activation=activation))
                            elif layer_class == 'Dropout':
                                rate = layer_cfg.get('rate', 0.0)
                                self.model.add(Dropout(rate))
                        
                        # Load weights
                        self.model.load_weights(weights_path)
                        
                        # Compile model
                        compile_config = model_config.get('compile_config', {})
                        if compile_config:
                            optimizer_config = compile_config.get('optimizer', {})
                            loss = compile_config.get('loss', 'binary_crossentropy')
                            metrics = compile_config.get('metrics', ['accuracy'])
                            
                            # Reconstruct optimizer
                            opt_config = optimizer_config.get('config', {})
                            lr = opt_config.get('learning_rate', 0.001)
                            optimizer = Adam(learning_rate=lr)
                            
                            self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
                        else:
                            # Default compilation
                            self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
                        
                        self.logger.info(f"✅ Model loaded from directory: {model_path}")
                    except Exception as e1:
                        # Fallback: Try using model_from_json
                        self.logger.warning(f"Manual model building failed: {e1}, trying model_from_json...")
                        try:
                            from keras.models import model_from_json
                            # Convert full config to JSON string
                            config_json_str = json.dumps(model_config)
                            self.model = model_from_json(config_json_str)
                            self.model.load_weights(weights_path)
                            
                            # Compile if needed
                            compile_config = model_config.get('compile_config', {})
                            if compile_config:
                                from keras.optimizers import Adam
                                opt_config = compile_config.get('optimizer', {}).get('config', {})
                                lr = opt_config.get('learning_rate', 0.001)
                                self.model.compile(
                                    optimizer=Adam(learning_rate=lr),
                                    loss=compile_config.get('loss', 'binary_crossentropy'),
                                    metrics=compile_config.get('metrics', ['accuracy'])
                                )
                            
                            self.logger.info(f"✅ Model loaded using model_from_json: {model_path}")
                        except Exception as e2:
                            raise Exception(f"Both loading methods failed. Manual: {e1}, JSON: {e2}")
                else:
                    raise ValueError(f"Unsupported model config format: {model_config.get('module')}")
                    
            elif os.path.isfile(model_path) and model_path.endswith('.keras'):
                # Old format: single .keras file
                self.model = keras.models.load_model(model_path)
                self.logger.info(f"✅ Model loaded from file: {model_path}")
            else:
                # Try to find model in default location
                default_path = "data/models/ddos_model_retrained"
                if os.path.isdir(default_path):
                    self.model_path = default_path
                    return self.load_model()  # Retry with default path
                else:
                    raise FileNotFoundError(f"Model not found: {model_path}")
            
            # Verify model is loaded
            if self.model is None:
                raise ValueError("Model loaded but is None")
            
            # Test model with dummy input
            test_input = np.random.rand(1, 77)
            _ = self.model.predict(test_input, verbose=0)
            
            # Initialize attack types
            self.attack_types = {
                0: 'Normal',
                1: 'DDoS Attack',
                2: 'Volume Attack',
                3: 'Rate Attack',
                4: 'Protocol Attack'
            }
            
            # Mark as loaded
            self.is_loaded = True
            self.network_stats['model_status'] = 'healthy'
            
            self.logger.info("✅ DDoS Detection Model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load DDoS Detection Model: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            self.is_loaded = False
            self.network_stats['model_status'] = 'error'
            # Fallback to simple detector
            if self.ddos_detector:
                self.logger.info("Falling back to simple DDoS detector")
                self.is_loaded = True
                self.network_stats['model_status'] = 'simple_detector_only'
                return True
            return False
    
    def extract_features(self, packet_data):
        """
        Extract features from network packet data for ML model
        This function simulates feature extraction from real network traffic
        """
        try:
            # Generate 77 features to match the model's expected input
            # This simulates comprehensive network traffic analysis
            features = {}
            
            # Basic packet features (15 features) - Use actual packet data
            features['packet_size'] = packet_data.get('size', 64)
            features['protocol'] = packet_data.get('protocol', 6)
            features['src_port'] = packet_data.get('src_port', 0)
            features['dst_port'] = packet_data.get('dst_port', 80)
            features['packet_rate'] = packet_data.get('rate', 1.0)
            features['connection_duration'] = packet_data.get('duration', 1.0)
            features['bytes_per_second'] = packet_data.get('bps', 1000)
            features['packets_per_second'] = packet_data.get('pps', 1.0)
            features['tcp_flags'] = packet_data.get('tcp_flags', 16)
            features['window_size'] = packet_data.get('window_size', 8192)
            features['ttl'] = packet_data.get('ttl', 64)
            features['fragment_offset'] = packet_data.get('fragment_offset', 0)
            features['ip_length'] = packet_data.get('ip_length', packet_data.get('size', 64))
            features['tcp_length'] = packet_data.get('tcp_length', 20)
            features['udp_length'] = packet_data.get('udp_length', 0)
            
            # Generate additional 62 features to reach 77 total
            # These represent various network traffic characteristics based on actual data
            additional_features = []
            
            # Statistical features (20 features) - Based on packet characteristics
            packet_size = features['packet_size']
            packet_rate = features['packet_rate']
            bps = features['bytes_per_second']
            pps = features['packets_per_second']
            
            # Size-based features
            additional_features.extend([
                packet_size / 1500,  # Normalized packet size
                packet_size * packet_rate,  # Size-rate product
                packet_size / max(bps, 1),  # Size per byte
                packet_size / max(pps, 1),  # Size per packet
                min(packet_size / 64, 10),  # Size ratio to minimum
            ])
            
            # Rate-based features
            additional_features.extend([
                packet_rate / 100,  # Normalized rate
                pps / 1000,  # Normalized PPS
                bps / 1000000,  # Normalized BPS
                packet_rate * pps,  # Rate product
                bps / max(pps, 1),  # Bytes per packet
            ])
            
            # Protocol-based features
            protocol = features['protocol']
            additional_features.extend([
                protocol / 6,  # Normalized protocol
                features['tcp_flags'] / 255,  # Normalized flags
                features['window_size'] / 65535,  # Normalized window
                features['ttl'] / 255,  # Normalized TTL
                features['fragment_offset'] / 8191,  # Normalized fragment
            ])
            
            # Port-based features
            src_port = features['src_port']
            dst_port = features['dst_port']
            additional_features.extend([
                src_port / 65535,  # Normalized src port
                dst_port / 65535,  # Normalized dst port
                abs(src_port - dst_port) / 65535,  # Port difference
                (src_port + dst_port) / 131070,  # Port sum
                min(src_port, dst_port) / 65535,  # Min port
            ])
            
            # Duration and timing features
            duration = features['connection_duration']
            additional_features.extend([
                duration,  # Raw duration
                duration * packet_rate,  # Duration-rate product
                duration / max(pps, 1),  # Duration per packet
                min(duration, 1),  # Capped duration
                duration * bps,  # Duration-bandwidth product
            ])
            
            # Attack pattern indicators
            additional_features.extend([
                1 if packet_size > 1000 else 0,  # Large packet indicator
                1 if packet_rate > 100 else 0,  # High rate indicator
                1 if pps > 1000 else 0,  # High PPS indicator
                1 if bps > 1000000 else 0,  # High BPS indicator
                1 if features['tcp_flags'] == 2 else 0,  # SYN flag indicator
            ])
            
            # Fill remaining features with derived values
            remaining_features = 77 - len(additional_features) - 15
            for i in range(remaining_features):
                # Create meaningful derived features
                base_value = (packet_size + packet_rate + bps + pps) / 4
                additional_features.append(base_value * (i + 1) / remaining_features)
            
            # Combine all features into a 77-dimensional vector
            all_features = [
                features['packet_size'],
                features['protocol'],
                features['src_port'],
                features['dst_port'],
                features['packet_rate'],
                features['connection_duration'],
                features['bytes_per_second'],
                features['packets_per_second'],
                features['tcp_flags'],
                features['window_size'],
                features['ttl'],
                features['fragment_offset'],
                features['ip_length'],
                features['tcp_length'],
                features['udp_length']
            ] + additional_features
            
            # Ensure we have exactly 77 features
            if len(all_features) < 77:
                all_features.extend([0.0] * (77 - len(all_features)))
            elif len(all_features) > 77:
                all_features = all_features[:77]
            
            feature_vector = np.array(all_features).reshape(1, -1)
            
            return feature_vector, features
            
        except Exception as e:
            self.logger.error(f"❌ Feature extraction failed: {e}")
            return None, None
    
    def predict_attack(self, packet_data):
        """
        Predict if the packet represents a DDoS attack using ML model and/or simple detector
        """
        if not self.is_loaded:
            return {'prediction': 'Model not loaded', 'confidence': 0.0, 'attack_type': 'Unknown'}
        
        try:
            ml_prediction = None
            ml_confidence = 0.0
            is_attack = False
            
            # Try ML model prediction first if available
            if self.model is not None and TENSORFLOW_AVAILABLE:
                try:
                    # Extract features
                    feature_vector, features = self.extract_features(packet_data)
                    if feature_vector is not None:
                        # Get ML prediction
                        start_time = time.time()
                        ml_prediction_raw = self.model.predict(feature_vector, verbose=0)
                        prediction_time = time.time() - start_time
                        
                        # Model outputs probability (0-1) for binary classification
                        ml_confidence = float(ml_prediction_raw[0][0])
                        is_attack = ml_confidence > 0.5  # Threshold for attack detection
                        
                        # Update processing time
                        self.last_processing_times.append(prediction_time)
                        self.update_detection_stats(prediction_time)
                        
                        # Determine attack type based on confidence and packet characteristics
                        if is_attack:
                            if ml_confidence > 0.9:
                                attack_type = 'DDoS Attack'
                            elif ml_confidence > 0.7:
                                attack_type = 'Volume Attack'
                            else:
                                attack_type = 'Rate Attack'
                        else:
                            attack_type = 'Normal'
                        
                        ml_prediction = {
                            'is_attack': is_attack,
                            'attack_type': attack_type,
                            'confidence': ml_confidence,
                            'method': 'ml_model'
                        }
                except Exception as e:
                    self.logger.warning(f"ML model prediction failed: {e}, falling back to simple detector")
                    ml_prediction = None
            
            # Use simple DDoS detector as primary or fallback
            if self.ddos_detector:
                simple_result = self.ddos_detector.detect(packet=packet_data)
                
                # Combine ML and simple detector results if both available
                if ml_prediction:
                    # Weighted combination: 70% ML, 30% simple detector
                    ml_weight = 0.7
                    simple_weight = 0.3
                    
                    combined_confidence = (ml_weight * ml_confidence + 
                                         simple_weight * simple_result.get('confidence', 0.0))
                    combined_is_attack = is_attack or simple_result.get('is_attack', False)
                    
                    # Use ML attack type if ML detected attack, otherwise use simple detector
                    if is_attack:
                        final_attack_type = ml_prediction['attack_type']
                    elif simple_result.get('is_attack'):
                        final_attack_type = simple_result.get('attack_type', 'DDoS Attack')
                    else:
                        final_attack_type = 'Normal'
                    
                    result = {
                        'is_attack': combined_is_attack,
                        'attack_type': final_attack_type,
                        'confidence': combined_confidence,
                        'reason': f"ML: {ml_confidence:.2f}, Simple: {simple_result.get('confidence', 0.0):.2f}",
                        'severity': 'high' if combined_confidence > 0.8 else ('medium' if combined_confidence > 0.5 else 'low'),
                        'ml_confidence': ml_confidence,
                        'simple_confidence': simple_result.get('confidence', 0.0)
                    }
                else:
                    # Use only simple detector
                    result = simple_result
            else:
                # Use only ML model or fallback
                if ml_prediction:
                    result = {
                        'is_attack': is_attack,
                        'attack_type': ml_prediction['attack_type'],
                        'confidence': ml_confidence,
                        'reason': f"ML model prediction: {ml_confidence:.2f}",
                        'severity': 'high' if ml_confidence > 0.8 else ('medium' if ml_confidence > 0.5 else 'low')
                    }
                else:
                    # No detectors available
                    result = {
                        'is_attack': False,
                        'attack_type': None,
                        'confidence': 0.0,
                        'reason': 'No detection methods available',
                        'severity': 'low'
                    }
            
            # Calculate attack score (0-100)
            attack_score = result.get('confidence', 0.0) * 100
            
            # Build indicators list
            indicators = []
            if result.get('reason'):
                indicators.append(result['reason'])
            if ml_prediction and ml_prediction.get('method') == 'ml_model':
                indicators.append(f"ML Model: {ml_confidence:.2%} confidence")
            
            # Store detection in our history
            detection = {
                'timestamp': datetime.now().isoformat(),
                'device_id': packet_data.get('device_id', 'unknown'),
                'is_attack': result.get('is_attack', False),
                'attack_type': result.get('attack_type'),
                'confidence': result.get('confidence', 0.0),
                'attack_score': attack_score,
                'indicators': indicators,
                'severity': result.get('severity', 'low')
            }
            
            self.attack_detections.append(detection)
            
            # Update statistics
            self.update_statistics(result.get('is_attack', False))
            
            return {
                'prediction': result.get('attack_type', 'Unknown'),
                'confidence': result.get('confidence', 0.0),
                'attack_type': result.get('attack_type'),
                'is_attack': result.get('is_attack', False),
                'attack_score': attack_score,
                'indicators': indicators,
                'detection': detection
            }
            
        except Exception as e:
            self.logger.error(f"❌ Attack prediction failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {'prediction': 'Error', 'confidence': 0.0, 'attack_type': 'Unknown'}
    
    def update_statistics(self, is_attack):
        """Update network statistics based on detection results"""
        self.network_stats['total_packets'] += 1
        
        if is_attack:
            self.network_stats['attack_packets'] += 1
        else:
            self.network_stats['normal_packets'] += 1
        
        # Calculate attack rate
        if self.network_stats['total_packets'] > 0:
            self.network_stats['attack_rate'] = (
                self.network_stats['attack_packets'] / self.network_stats['total_packets']
            ) * 100
        
        # Calculate detection accuracy (simplified)
        if len(self.attack_detections) > 10:
            recent_detections = list(self.attack_detections)[-10:]
            avg_confidence = np.mean([d['confidence'] for d in recent_detections])
            self.network_stats['detection_accuracy'] = avg_confidence * 100
    
    def get_attack_statistics(self):
        """Get comprehensive attack statistics"""
        if not self.attack_detections:
            return self.network_stats
        
        # Calculate additional statistics
        recent_attacks = [d for d in self.attack_detections if d['is_attack']]
        attack_types_count = {}
        
        for detection in recent_attacks:
            attack_type = detection['attack_type']
            attack_types_count[attack_type] = attack_types_count.get(attack_type, 0) + 1
        
        # Time-based analysis
        now = datetime.now()
        last_hour_attacks = [
            d for d in recent_attacks 
            if (now - datetime.fromisoformat(d['timestamp'])).seconds < 3600
        ]
        
        # Convert numpy types to Python types for JSON serialization
        stats = {
            **self.network_stats,
            'recent_attacks': int(len(recent_attacks)),
            'last_hour_attacks': int(len(last_hour_attacks)),
            'attack_types_distribution': attack_types_count,
            'avg_confidence': float(np.mean([d['confidence'] for d in recent_attacks])) if recent_attacks else 0.0,
            'max_confidence': float(np.max([d['confidence'] for d in recent_attacks])) if recent_attacks else 0.0,
            'min_confidence': float(np.min([d['confidence'] for d in recent_attacks])) if recent_attacks else 0.0
        }
        
        # Convert any remaining numpy types
        for key, value in stats.items():
            if hasattr(value, 'item'):  # numpy scalar
                stats[key] = value.item()
            elif isinstance(value, np.ndarray):
                stats[key] = value.tolist()
                
        return stats
    
    def get_recent_detections(self, limit=10):
        """Get recent attack detections"""
        try:
            detections = list(self.attack_detections)[-limit:]
            # Ensure all detections have proper format and convert numpy types to Python types
            for detection in detections:
                if not isinstance(detection, dict):
                    continue
                # Ensure required fields exist and convert numpy types
                if 'timestamp' not in detection:
                    detection['timestamp'] = datetime.now().isoformat()
                    
                if 'confidence' not in detection:
                    detection['confidence'] = 0.0
                else:
                    detection['confidence'] = float(detection['confidence'])
                    
                if 'attack_type' not in detection:
                    detection['attack_type'] = 'Unknown'
                else:
                    detection['attack_type'] = str(detection['attack_type'])
                    
                if 'is_attack' not in detection:
                    detection['is_attack'] = False
                else:
                    detection['is_attack'] = bool(detection['is_attack'])
                    
                # Convert any remaining numpy types to Python types
                for key, value in detection.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        detection[key] = value.item()
                    elif isinstance(value, np.ndarray):
                        detection[key] = value.tolist()
            return detections
        except Exception as e:
            self.logger.error(f"Error getting recent detections: {e}")
            return []
    
    def simulate_network_traffic(self):
        """Simulate network traffic for testing purposes"""
        while True:
            # Simulate different types of network traffic
            traffic_types = ['normal', 'ddos', 'botnet', 'flood']
            traffic_type = np.random.choice(traffic_types, p=[0.7, 0.1, 0.1, 0.1])
            
            # Generate packet data based on traffic type
            if traffic_type == 'normal':
                packet_data = {
                    'size': np.random.randint(64, 1500),
                    'protocol': np.random.choice([1, 6, 17]),  # ICMP, TCP, UDP
                    'src_port': np.random.randint(1024, 65535),
                    'dst_port': np.random.randint(80, 443),
                    'rate': np.random.uniform(0.1, 10.0),
                    'duration': np.random.uniform(1.0, 3600.0),
                    'bps': np.random.uniform(1000, 100000),
                    'pps': np.random.uniform(0.1, 100.0)
                }
            else:  # Attack traffic
                packet_data = {
                    'size': np.random.randint(64, 1500),
                    'protocol': np.random.choice([1, 6, 17]),
                    'src_port': np.random.randint(1, 65535),
                    'dst_port': np.random.randint(80, 443),
                    'rate': np.random.uniform(50.0, 1000.0),  # Higher rate for attacks
                    'duration': np.random.uniform(0.1, 100.0),
                    'bps': np.random.uniform(100000, 10000000),  # Higher bandwidth
                    'pps': np.random.uniform(100.0, 10000.0)  # Higher packet rate
                }
            
            # Analyze the packet
            result = self.predict_attack(packet_data)
            
            # Log significant detections
            if result.get('is_attack', False) and result.get('confidence', 0) > 0.8:
                self.logger.warning(f"🚨 ATTACK DETECTED: {result['attack_type']} (Confidence: {result['confidence']:.2f})")
            
            time.sleep(0.1)  # Simulate real-time processing
    
    def start_monitoring(self):
        """Start real-time network monitoring"""
        if not self.is_loaded:
            self.logger.error("❌ Cannot start monitoring: Model not loaded")
            return
        
        self.logger.info("🔍 Starting real-time network monitoring...")
        monitor_thread = threading.Thread(target=self.simulate_network_traffic, daemon=True)
        monitor_thread.start()
        self.logger.info("✅ Network monitoring started")

# Global ML Security Engine instance
ml_engine = None

def initialize_ml_engine():
    """Initialize the global ML security engine"""
    global ml_engine
    if ml_engine is None:
        ml_engine = MLSecurityEngine()
    return ml_engine

def get_ml_engine():
    """Get the global ML security engine instance"""
    return ml_engine

if __name__ == "__main__":
    # Test the ML Security Engine
    print("🧪 Testing ML Security Engine...")
    
    engine = MLSecurityEngine()
    
    if engine.is_loaded:
        print("✅ ML Engine initialized successfully")
        
        # Test with sample data
        test_packet = {
            'size': 1024,
            'protocol': 6,  # TCP
            'src_port': 12345,
            'dst_port': 80,
            'rate': 5.0,
            'duration': 10.0,
            'bps': 50000,
            'pps': 5.0
        }
        
        result = engine.predict_attack(test_packet)
        print(f"Test prediction: {result}")
        
        # Start monitoring
        engine.start_monitoring()
        
        # Run for a few seconds to see detections
        time.sleep(5)
        
        stats = engine.get_attack_statistics()
        print(f"Network statistics: {stats}")
        
    else:
        print("❌ Failed to initialize ML Engine")
