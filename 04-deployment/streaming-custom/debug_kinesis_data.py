#!/usr/bin/env python3

import json
import base64

# Test the data format you're sending
test_data = {
    "ride": {
        "PULocationID": 130,
        "DOLocationID": 205,
        "trip_distance": 3.66
    }, 
    "ride_id": 156
}

# Convert to JSON string (this is what you send to Kinesis)
json_string = json.dumps(test_data)
print("Original JSON string:")
print(json_string)
print(f"Length: {len(json_string)}")
print()

# Simulate what Kinesis does - encode as UTF-8 bytes then base64
utf8_bytes = json_string.encode('utf-8')
print("UTF-8 encoded bytes:")
print(utf8_bytes)
print(f"Length: {len(utf8_bytes)}")
print()

# Base64 encode (what Kinesis stores)
b64_encoded = base64.b64encode(utf8_bytes).decode('ascii')
print("Base64 encoded (what Kinesis stores):")
print(b64_encoded)
print()

# Now simulate what your Lambda should do
print("=== Lambda Processing ===")

# Decode from base64 (this gives you the UTF-8 bytes back)
decoded_bytes = base64.b64decode(b64_encoded)
print("Decoded bytes from base64:")
print(decoded_bytes)
print()

# Decode from UTF-8 (this gives you the JSON string back)
try:
    decoded_string = decoded_bytes.decode('utf-8')
    print("Decoded string from UTF-8:")
    print(decoded_string)
    print()
    
    # Parse JSON
    parsed_data = json.loads(decoded_string)
    print("Parsed JSON:")
    print(parsed_data)
    
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError: {e}")
    print("This suggests the data contains invalid UTF-8 sequences")
    
    # Show the problematic bytes
    print("Raw bytes:")
    for i, byte in enumerate(decoded_bytes):
        print(f"  Position {i}: 0x{byte:02x} ({byte})") 