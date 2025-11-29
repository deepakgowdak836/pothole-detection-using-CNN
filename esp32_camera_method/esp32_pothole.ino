#include "esp_camera.h"
#include <WiFi.h>

// ====== ENTER YOUR WIFI DETAILS HERE ======
const char* WIFI_SSID = "*******";
const char* WIFI_PASS = "*******";
// ==========================================

// ESP32-CAM (AI Thinker) Pin Definitions
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5

#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

#include "esp_http_server.h"
httpd_handle_t stream_httpd = NULL;

static esp_err_t stream_handler(httpd_req_t *req){
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    size_t jpg_len = 0;
    uint8_t *jpg_buf = NULL;

    char buffer[64];
    res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
    if(res != ESP_OK){
        return res;
    }

    while(true){
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed!");
            continue;
        }

        jpg_buf = fb->buf;
        jpg_len = fb->len;

        int hlen = snprintf(buffer, 64,
            "\r\n--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
            jpg_len);

        if (httpd_resp_send_chunk(req, buffer, hlen) != ESP_OK) break;
        if (httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_len) != ESP_OK) break;

        esp_camera_fb_return(fb);
        vTaskDelay(30 / portTICK_PERIOD_MS);
    }

    return ESP_OK;
}

void startStreamServer(){
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.stack_size = 8192; // Increase stack size for stability

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_uri_t stream_uri = {
            .uri = "/stream",
            .method = HTTP_GET,
            .handler = stream_handler,
            .user_ctx = NULL
        };
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        Serial.println("HTTP Stream Server Started.");
    } else {
        Serial.println("Error starting HTTP Stream Server!");
    }
}

void setup(){
    Serial.begin(115200);
    delay(1000);

    // Camera configuration
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;

    if(esp_camera_init(&config) != ESP_OK){
        Serial.println(" Camera init failed!");
        return;
    }
    Serial.println(" Camera initialized.");

    // --- Connect to WiFi with Timeout ---
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("Connecting to WiFi");

    // Timeout for 20 loops (20 * 500ms = 10 seconds)
    int connection_attempts = 0; 

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        connection_attempts++;

        if (connection_attempts >= 20) {
            Serial.println("\n\n WiFi Connection Failed! Check SSID/Password and Power Supply.");
            Serial.println("The ESP32 will now restart to try again...");
            delay(3000);
            ESP.restart(); // Restart the board to retry connection
        }
    }

    Serial.println("\n WiFi connected!");
    Serial.print("STREAM URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/stream");

    // Start streaming
    startStreamServer();
}

void loop(){
    delay(1);
}