# Simple DDoS Detector Module

## Overview

The `simple_ddos_detector` module provides heuristic-based DDoS (Distributed Denial of Service) attack detection using traffic pattern analysis. It serves as a fallback detection mechanism when ML models are unavailable and complements the ML-based detection system.

## Features

- **Heuristic-based Detection**: Uses traffic rate thresholds and pattern analysis
- **Multiple Attack Types**: Detects DDoS, volume, and flood attacks
- **Configurable Thresholds**: Adjustable detection parameters
- **Attack History**: Tracks detected attacks for analysis
- **Statistics**: Provides detection statistics and metrics

## Installation

The module is included in the project and requires no additional dependencies beyond Python standard library.

## Usage

### Basic Usage

```python
from simple_ddos_detector import SimpleDDoSDetector

# Initialize detector
detector = SimpleDDoSDetector()

# Detect attack from packet information
packet = {
    'size': 1500,        # Packet size in bytes
    'protocol': 6,       # Protocol (6=TCP, 17=UDP)
    'rate': 100000.0,   # Traffic rate
    'pps': 2000.0,      # Packets per second
    'duration': 15.0    # Attack duration in seconds
}

result = detector.detect(packet=packet)

if result['is_attack']:
    print(f"Attack detected: {result['attack_type']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Severity: {result['severity']}")
    print(f"Reason: {result['reason']}")
```

### Detection Result Format

```python
{
    'is_attack': bool,           # True if attack detected
    'attack_type': str,          # 'ddos', 'volume', 'flood', or None
    'confidence': float,         # 0.0-1.0 confidence score
    'reason': str,               # Human-readable reason
    'severity': str,             # 'low', 'medium', or 'high'
    'packet_info': dict          # Original packet information
}
```

## Detection Thresholds

Default thresholds (configurable):

- **Packet Rate Threshold**: 1000 packets/second
- **Byte Rate Threshold**: 10 MB/s (10,000,000 bytes/second)
- **Duration Threshold**: 10 seconds
- **PPS Threshold**: 1000 packets/second

### Attack Detection Levels

1. **Extreme (10x threshold)**: High confidence (0.90-0.95), High severity
2. **Very High (5x threshold)**: High confidence (0.80-0.85), High severity
3. **High (above threshold)**: Medium confidence (0.65-0.70), Medium severity

## Attack Types

### DDoS Attack
- Detected by high packet rate (PPS)
- Multiple severity levels based on rate multiplier

### Volume Attack
- Detected by high byte rate
- Targets bandwidth saturation

### Flood Attack
- Detected by many small packets at high rate
- Pattern: small size (< 100 bytes) + high PPS (> 2x threshold)

## API Reference

### `SimpleDDoSDetector()`

Initialize the DDoS detector with default thresholds.

### `detect(packet=None, **kwargs) -> Dict`

Detect DDoS attack from packet information.

**Parameters:**
- `packet` (dict, optional): Packet information dictionary
- `**kwargs`: Additional packet attributes

**Returns:** Detection result dictionary

### `analyze(packet: Dict) -> Dict`

Alias for `detect()` method for compatibility.

### `get_statistics() -> Dict`

Get detector statistics including:
- Total packets processed
- Detected attacks count
- Detection rate percentage
- Recent attacks count
- Current thresholds

### `get_recent_attacks(limit: int = 10) -> list`

Get list of recent attack detections.

**Parameters:**
- `limit`: Maximum number of attacks to return

**Returns:** List of attack dictionaries

### `reset_statistics()`

Reset all detector statistics and history.

### `update_thresholds(**kwargs)`

Update detection thresholds.

**Parameters:**
- `packet_rate_threshold`: Packets per second threshold
- `byte_rate_threshold`: Bytes per second threshold
- `duration_threshold`: Duration threshold in seconds
- `pps_threshold`: Packets per second threshold

## Integration with ML Security Engine

The Simple DDoS Detector is automatically used by the ML Security Engine:

```python
from ml_security_engine import MLSecurityEngine

engine = MLSecurityEngine()
# engine.ddos_detector is a SimpleDDoSDetector instance
```

The detector provides:
1. **Fallback Detection**: When ML models are unavailable
2. **Fast Detection**: Heuristic-based detection is faster than ML inference
3. **Complementary Detection**: Works alongside ML-based detection

## Example Scenarios

### Normal Traffic
```python
result = detector.detect({
    'size': 100,
    'protocol': 6,
    'pps': 10.0,
    'rate': 1000.0
})
# result['is_attack'] = False
```

### DDoS Attack
```python
result = detector.detect({
    'size': 1500,
    'protocol': 6,
    'pps': 5000.0,  # 5x threshold
    'rate': 50000.0
})
# result['is_attack'] = True
# result['attack_type'] = 'ddos'
# result['confidence'] = 0.85
```

### Volume Attack
```python
result = detector.detect({
    'size': 1500,
    'protocol': 6,
    'pps': 100.0,
    'rate': 200000000.0  # 20x byte rate threshold
})
# result['is_attack'] = True
# result['attack_type'] = 'volume'
# result['confidence'] = 0.90
```

## Configuration

Thresholds can be adjusted based on network characteristics:

```python
detector = SimpleDDoSDetector()
detector.update_thresholds(
    pps_threshold=2000.0,        # Higher threshold for high-traffic networks
    byte_rate_threshold=50000000.0  # 50 MB/s for high-bandwidth networks
)
```

## Performance

- **Low Overhead**: Minimal CPU and memory usage
- **Fast Detection**: Real-time detection with < 1ms latency
- **Scalable**: Handles high packet rates efficiently
- **Memory Efficient**: Uses deque with maxlen for bounded memory

## Limitations

1. **Heuristic-based**: May have false positives/negatives compared to ML models
2. **Threshold-dependent**: Requires tuning for different network environments
3. **Pattern-based**: May miss sophisticated attacks that don't match patterns

## Future Enhancements

- Machine learning integration for threshold optimization
- Adaptive thresholds based on network baseline
- Attack pattern learning and correlation
- Integration with threat intelligence feeds

## License

Part of the IoT Zero Trust Security System.

---

**Last Updated**: 2025-01-27

