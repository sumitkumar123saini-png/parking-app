/*
 * Smart parking — single slot (matches project report)
 * Arduino Uno + HC-SR04 + red/green LEDs
 * USB serial lines: STATUS:OCCUPIED | STATUS:EMPTY (read by scripts/serial_bridge.py)
 */
#define TRIG_PIN   9
#define ECHO_PIN   10
#define RED_LED    7
#define GREEN_LED  6

#define THRESHOLD_CM  15.0f
#define LOOP_MS       500

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  Serial.begin(9600);
  Serial.println(F("# smart_parking_slot ready"));
}

static float measureCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration <= 0) return -1.0f;
  return duration * 0.0343f / 2.0f;
}

void loop() {
  float d = measureCm();
  bool occupied = (d > 0.0f && d < THRESHOLD_CM);

  if (occupied) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    Serial.println(F("STATUS:OCCUPIED"));
  } else {
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
    Serial.println(F("STATUS:EMPTY"));
  }

  delay(LOOP_MS);
}
