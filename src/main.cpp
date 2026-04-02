/*
  Wandering Patient Alert System
  --------------------------------
  Hardware:
    - ESP32
    - MH-Sensor-Series IR Obstacle Avoidance Sensor

  Wiring:
    - IR VCC  → ESP32 3.3V
    - IR GND  → ESP32 GND
    - IR OUT  → ESP32 GPIO 13

  The IR sensor outputs LOW when it detects an object (patient in bed)
  and HIGH when no object is detected (patient has left).

  Data is sent over Serial (USB) as JSON every 500ms.
  Format: {"status":"IN_BED","absent_ms":0,"alert":false}
*/

#include <Arduino.h>

const int IR_PIN = 13;
const unsigned long ALERT_THRESHOLD_MS = 1000; // 2 seconds for demo

unsigned long absenceStart = 0;
bool patientAbsent = false;
bool alertFired = false;

void setup() {
  Serial.begin(115200);
  pinMode(IR_PIN, INPUT);
  delay(1000);
  Serial.println("{\"event\":\"SYSTEM_START\"}");
}

void loop() {
  // MH sensor: LOW = object detected (patient in bed), HIGH = no object (patient gone)
  bool sensorTriggered = (digitalRead(IR_PIN) == LOW);

  if (sensorTriggered) {
    // Patient is in bed
    if (patientAbsent) {
      // Patient just returned
      patientAbsent = false;
      alertFired = false;
      absenceStart = 0;
      Serial.println("{\"event\":\"PATIENT_RETURNED\"}");
    }

    Serial.print("{\"status\":\"IN_BED\",\"absent_ms\":0,\"alert\":false}");
    Serial.println();

  } else {
    // Patient is absent
    if (!patientAbsent) {
      // Just left — record time
      patientAbsent = true;
      absenceStart = millis();
      Serial.println("{\"event\":\"PATIENT_LEFT\"}");
    }

    unsigned long absentDuration = millis() - absenceStart;
    bool alert = absentDuration >= ALERT_THRESHOLD_MS;

    if (alert && !alertFired) {
      alertFired = true;
      Serial.println("{\"event\":\"ALERT_TRIGGERED\"}");
    }

    Serial.print("{\"status\":\"ABSENT\",\"absent_ms\":");
    Serial.print(absentDuration);
    Serial.print(",\"alert\":");
    Serial.print(alert ? "true" : "false");
    Serial.println("}");
  }

  delay(500);
}
