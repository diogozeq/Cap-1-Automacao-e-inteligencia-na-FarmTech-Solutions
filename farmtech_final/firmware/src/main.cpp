#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- Otimização de Pinos e Constantes (OPT-1) ---
// Mapeamento de pinos
const int SENSOR_PIN = 34;    // Pino ANALÓGICO para o sensor de umidade
const int RELAY_PIN = 23;     // Pino DIGITAL para controlar o relé da bomba

// --- Otimização de Lógica (OPT-2) ---
// Limites de umidade para controle da irrigação
const int UMIDADE_SECO = 45;  // Abaixo deste valor, ligar a bomba (valor em %)
const int UMIDADE_UMIDO = 65; // Acima deste valor, desligar a bomba (valor em %)

// --- Otimização de Hardware (OPT-3) ---
// Configuração do Display LCD I2C
const int LCD_COLS = 16;
const int LCD_ROWS = 2;
LiquidCrystal_I2C lcd(0x27, LCD_COLS, LCD_ROWS);

// --- Otimização de Memória (OPT-4) ---
// Buffers de char para evitar uso da classe String
char lcdLine1[LCD_COLS + 1];
char lcdLine2[LCD_COLS + 1];

void setup() {
    // Inicializa a comunicação serial para debug
    Serial.begin(115200);
    
    // Configura o pino do relé como saída
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, HIGH); // Inicia com o relé DESLIGADO (HIGH para esse módulo)

    // Inicializa o display LCD
    lcd.init();
    lcd.backlight();
    lcd.setCursor(0, 0);
    // --- Otimização de Memória (OPT-5) ---
    // Uso da macro F() para armazenar strings na memória Flash
    lcd.print(F("FarmTech ESP32"));
    Serial.println(F("FarmTech ESP32 - Sistema de Irrigacao Iniciado."));
    delay(2000);
    lcd.clear();
}

void loop() {
    // Leitura do sensor de umidade
    // O sensor analógico fornece valores de ~0 (úmido) a ~4095 (seco)
    int valorSensor = analogRead(SENSOR_PIN);
    
    // Mapeia o valor lido para uma porcentagem (0-100%)
    // Invertemos a lógica, pois 4095 é seco e 0 é úmido.
    int umidadePercent = map(valorSensor, 4095, 0, 0, 100);

    // Lógica de controle da bomba
    if (umidadePercent < UMIDADE_SECO) {
        digitalWrite(RELAY_PIN, LOW); // Liga a bomba (relé ATIVADO em LOW)
    } else if (umidadePercent > UMIDADE_UMIDO) {
        digitalWrite(RELAY_PIN, HIGH); // Desliga a bomba
    }

    bool bombaLigada = (digitalRead(RELAY_PIN) == LOW);

    // --- Otimização de Display e Serial (OPT-6) ---
    // Preparação das strings para o display e monitor serial
    // Uso de snprintf para evitar a classe String e controlar o tamanho do buffer
    snprintf(lcdLine1, sizeof(lcdLine1), "Umidade: %d%%", umidadePercent);
    snprintf(lcdLine2, sizeof(lcdLine2), "Bomba: %s", bombaLigada ? "LIGADA" : "DESLIGADA");

    // Atualiza o display LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(lcdLine1);
    lcd.setCursor(0, 1);
    lcd.print(lcdLine2);

    // Envia status para o Serial Monitor usando macro F()
    Serial.print(F("Umidade: "));
    Serial.print(umidadePercent);
    Serial.print(F("%, Bomba: "));
    Serial.println(bombaLigada ? "LIGADA" : "DESLIGADA");

    // Aguarda antes da próxima leitura para estabilidade
    delay(5000); // 5 segundos
} 