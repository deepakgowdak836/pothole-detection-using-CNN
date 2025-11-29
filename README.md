# Pothole Detection Using CNN

This project detects potholes in real-time using **Convolutional Neural Networks (CNN)**.  
It supports **two methods**:

1. **Mobile Camera Method (IP Webcam)**
2. **ESP32-CAM Method (TFLite)**

Both software and hardware approaches are included for demonstration.

---

##  1. Mobile Camera Method (Easy + Smooth)

This method uses a **mobile phone camera** as the video source using the **IP Webcam** app.

###  Requirements
- IP Webcam app (Play Store or Apple App Store)
- Python 3.10
- OpenCV
- TensorFlow / Keras
- Numpy

###  How to Run This Method
1. Install **IP Webcam**
2. Open the app → Start server  
3. Note your phone's camera IP  
   Example: `http://192.xxx.xx:8080/video`
4. Open the Python file:
   ```python
   url = "http://<your-ip-address>/video"
