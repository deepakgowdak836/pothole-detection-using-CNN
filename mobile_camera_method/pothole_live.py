import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter

# Load the TFLite model
interpreter = Interpreter(model_path="pothole_model.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

#  Replace this with your phone IP Webcam URL
url = "http://192.xxx.xx.xx:8080/video"

# Open camera stream
cap = cv2.VideoCapture(url)

# Set your threshold
threshold = 0.8  # you can adjust this (0.4 → more sensitive, 0.9 → more strict)

while True:
    ret, frame = cap.read()
    if not ret:
        print(" Failed to grab frame. Check IP address or connection.")
        break

    # Preprocess
    frame_resized = cv2.resize(frame, (128, 128))
    frame_normalized = frame_resized.astype(np.float32) / 255.0
    input_data = np.expand_dims(frame_normalized, axis=0)

    # Run model
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    confidence = float(output_data[0][0])  # assuming single output (0 = normal, 1 = pothole)

    # Apply threshold
    if confidence > threshold:
        label = f"POTHOLE ({confidence:.2f})"
        color = (0, 0, 255)  # red
    else:
        label = f"NORMAL ROAD ({confidence:.2f})"
        color = (0, 255, 0)  # green

    # Display result
    cv2.putText(frame, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Pothole Detection - IP Webcam", frame)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()