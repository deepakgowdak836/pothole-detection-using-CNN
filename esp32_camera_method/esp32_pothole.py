import requests
import cv2
import numpy as np
import tensorflow as tf
import sys

# --- 1. CONFIGURATION ---
# IMPORTANT: Use the IP address printed by your ESP32-CAM
ESP32_STREAM = " http://192.xx.xxx.xx/stream" 
MODEL_PATH = "pothole_model.tflite" # Match the file name you verified

# Global variables for model details (Accessible by default from main body)
interpreter = None
input_details = None
output_details = None
INPUT_SHAPE = (128, 128)

# Variables for Frame Skipping and Display
frame_counter = 0
SKIP_FRAMES = 5  # Run AI inference on only 1 out of every 5 frames
display_label = "NORMAL"
display_conf = 0.0
display_color = (0, 255, 0) # Green (BGR format)
CONFIDENCE_THRESHOLD = 0.8 # Define outside the loop

# --- 2. TENSORFLOW LITE INITIALIZATION FUNCTION ---
def initialize_model():
    global interpreter, input_details, output_details, INPUT_SHAPE
    
    print(f"Loading model from: {MODEL_PATH}")
    
    try:
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        INPUT_SHAPE = input_details[0]['shape'][1:3]
        
        print(f" TFLite Model Loaded successfully. Input shape: {INPUT_SHAPE}")
        return True

    except FileNotFoundError:
        print(f" ERROR: Model file not found at '{MODEL_PATH}'.")
        return False
    except Exception as e:
        print(f" ERROR loading TFLite model: {e}")
        return False

# --- 3. MAIN EXECUTION ---

# Attempt to load model and exit if it fails
if not initialize_model():
    sys.exit(1)


print(f"Connecting to stream at {ESP32_STREAM}...")
try:
    stream = requests.get(ESP32_STREAM, stream=True)
    stream.raise_for_status() 
    print(" Successfully connected to the ESP32 stream.")
except requests.exceptions.RequestException as e:
    print(f" ERROR connecting to ESP32 stream: {e}")
    sys.exit(1)


bytes_buffer = b''

# --- 4. STREAM PROCESSING LOOP with Frame Skipping ---
try:
    for chunk in stream.iter_content(chunk_size=8192):
        bytes_buffer += chunk
        
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = bytes_buffer[a:b+2]
            
            if not jpg:
                bytes_buffer = bytes_buffer[b+2:] 
                continue 
            
            bytes_buffer = bytes_buffer[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            if frame is None:
                continue
            
            # --- Frame Skip Logic ---
            frame_counter += 1

            # Only run the expensive model inference every N frames
            if frame_counter % SKIP_FRAMES == 0:
                
                # Model Preprocessing
                resized = cv2.resize(frame, INPUT_SHAPE) 
                input_data = np.float32(resized) / 255.0
                input_data = np.expand_dims(input_data, axis=0)

                # Run Model
                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()
                out = interpreter.get_tensor(output_details[0]['index'])
                conf = float(out[0][0]) 

                # Update the display variables
                display_label = "POTHOLE" if conf > CONFIDENCE_THRESHOLD else "NORMAL"
                display_conf = conf
                display_color = (0, 0, 255) if conf > CONFIDENCE_THRESHOLD else (0, 255, 0) # Red or Green

            # --- Display Logic (Runs on EVERY frame using the latest result) ---
            cv2.putText(frame, f"{display_label} (Score: {display_conf:.2f})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, display_color, 2)
            
            cv2.imshow("ESP32 Pothole Detection", frame)

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except KeyboardInterrupt:
    print("\nApplication interrupted by user.")
except Exception as e:
    print(f"\nAn unexpected error occurred during streaming: {e}")

finally:
    # --- 5. CLEANUP ---
    cv2.destroyAllWindows()
    print("Stream closed and application terminated.")