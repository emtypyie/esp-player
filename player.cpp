#include <U8g2lib.h>
#include <Wire.h>
#include "frames.h" 


U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// --- BUTTON PINS ---
#define BUTTON_PLAY_PAUSE 4  // Button 1: Toggles playback state
#define BUTTON_RESTART    5  // Button 2: Resets video back to frame 0

// --- PLAYBACK MANAGEMENT ---
bool isPaused = false;
int currentFrame = 0;
unsigned long lastDebounceTime1 = 0;
unsigned long lastDebounceTime2 = 0;
const unsigned long debounceDelay = 250; // ms debounce window

void setup() {
  Serial.begin(115200);
  

  pinMode(BUTTON_PLAY_PAUSE, INPUT_PULLUP);
  pinMode(BUTTON_RESTART, INPUT_PULLUP);

  // Initialize the standard I2C  pins (Pins 21 and 22)
  u8g2.begin();
  u8g2.setBusClock(400000); // Set to fast 400kHz I2C clock speed for smooth video frames
  
  // Boot screen display 
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB14_tr); // Set clean bold typography font
  u8g2.drawStr(28, 42, "EMTYPYIE");
  u8g2.sendBuffer();
  delay(2000); // Standby for 2 seconds before start
}

void loop() {
  // 1. Read low-active button states (Pressed = LOW)
  bool playPauseBtn = (digitalRead(BUTTON_PLAY_PAUSE) == LOW);
  bool restartBtn = (digitalRead(BUTTON_RESTART) == LOW);

  // 2. Button 1: Toggle Play/Pause state
  if (playPauseBtn && (millis() - lastDebounceTime1 > debounceDelay)) {
    isPaused = !isPaused;
    lastDebounceTime1 = millis();
    Serial.print(F("Play/Pause Toggled. State: "));
    Serial.println(isPaused ? F("PAUSED") : F("PLAYING"));
  }

  // 3. Button 2: Reset video to the beginning
  if (restartBtn && (millis() - lastDebounceTime2 > debounceDelay)) {
    currentFrame = 0;
    lastDebounceTime2 = millis();
    Serial.println(F("Video Restarted."));
  }

  // 4. Video Frame Streaming State Machine
  if (!isPaused) {
    u8g2.clearBuffer();
    
    // Draw the active video XBM frame out of Flash Memory
    u8g2.drawXBMP(0, 0, FRAME_WIDTH, FRAME_HEIGHT, video_frames[currentFrame]);
    
    u8g2.sendBuffer(); // Push frame to the display panel
    
    // Increment to the next frame array index loop
    currentFrame = (currentFrame + 1) % FRAME_COUNT;
    
    // Enforce target video speed (~30 FPS playback ceiling)
    delay(33); 
  } else {
    // Keep low-overhead standby delay during active pauses to catch inputs instantly
    delay(30); 
  }
}
