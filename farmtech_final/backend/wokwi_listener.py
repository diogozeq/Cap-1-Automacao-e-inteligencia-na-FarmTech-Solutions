#!/usr/bin/env python3
"""
wokwi_listener.py
Listener para capturar dados da simulação Wokwi em tempo real
Integração com o dashboard para visualização em tempo real

Este módulo simula a captura de dados do simulador Wokwi
e os persiste no banco de dados para visualização no dashboard.
"""

import json
import time
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import signal
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WokwiListener")

# Imports do sistema FarmTech
try:
    from . import services, db_manager
    from .config_manager import get_config
except ImportError:
    # Para execução direta
    import services
    import db_manager
    from config_manager import get_config

class WokwiListener:
    """
    Listener para capturar dados simulados do Wokwi
    e persistir no banco de dados do FarmTech
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or get_config()
        self.running = False
        self.simulation_active = False
        
        # Inicializar banco de dados
        try:
            db_manager.init_db()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
        
        # Configurar handler para interrupção
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Parâmetros da simulação
        self.params = self.config.get('logica_esp32', {
            'UMIDADE_CRITICA_BAIXA': 15.0,
            'UMIDADE_MINIMA_PARA_IRRIGAR': 20.0,
            'UMIDADE_ALTA_PARAR_IRRIGACAO': 60.0,
            'PH_IDEAL_MINIMO': 5.5,
            'PH_IDEAL_MAXIMO': 6.5,
            'PH_CRITICO_MINIMO': 4.5,
            'PH_CRITICO_MAXIMO': 7.5,
        })
        
        logger.info("WokwiListener inicializado")
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de interrupção"""
        logger.info(f"Recebido sinal {signum}, parando listener...")
        self.stop()
        sys.exit(0)
    
    def simulate_wokwi_data(self) -> Dict[str, Any]:
        """
        Simula dados que seriam recebidos do Wokwi
        Em uma implementação real, isso seria substituído
        pela leitura da porta serial ou WebSocket
        """
        # Simula variação realística dos sensores
        base_humidity = 30.0
        base_ph = 6.5
        base_temp = 25.0
        
        # Adiciona variação aleatória mas realística
        humidity = max(0, min(100, base_humidity + random.uniform(-10, 15)))
        ph = max(0, min(14, base_ph + random.uniform(-1, 1)))
        temperature = max(0, min(50, base_temp + random.uniform(-5, 10)))
        
        # Simula presença de nutrientes (ocasionalmente False)
        phosphorus = random.random() > 0.1  # 90% chance de estar presente
        potassium = random.random() > 0.1   # 90% chance de estar presente
        
        # Simula lógica de decisão da bomba
        pump_on, decision_reason = self._simulate_irrigation_logic(
            humidity, ph, phosphorus, potassium, temperature
        )
        
        # Detecta emergência
        emergency = (
            humidity < self.params['UMIDADE_CRITICA_BAIXA'] or
            ph < self.params['PH_CRITICO_MINIMO'] or
            ph > self.params['PH_CRITICO_MAXIMO']
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "umidade": round(humidity, 1),
            "ph_estimado": round(ph, 1),
            "fosforo_presente": phosphorus,
            "potassio_presente": potassium,
            "temperatura": round(temperature, 1),
            "bomba_ligada": pump_on,
            "decisao_logica_esp32": decision_reason,
            "emergencia": emergency
        }
    
    def _simulate_irrigation_logic(self, humidity: float, ph: float, 
                                  phosphorus: bool, potassium: bool, 
                                  temperature: float) -> tuple[bool, str]:
        """
        Simula a lógica de irrigação do ESP32
        Retorna (deve_ligar_bomba, motivo)
        """
        params = self.params
        
        # Lógica de emergência
        if humidity < params['UMIDADE_CRITICA_BAIXA']:
            return True, f"EMERGÊNCIA: Umidade crítica ({humidity:.1f}%)"
        
        # Lógica de pH crítico
        if ph < params['PH_CRITICO_MINIMO'] or ph > params['PH_CRITICO_MAXIMO']:
            return False, f"pH crítico ({ph:.1f}) - Irrigação bloqueada"
        
        # Lógica normal de irrigação
        if humidity < params['UMIDADE_MINIMA_PARA_IRRIGAR']:
            if params['PH_IDEAL_MINIMO'] <= ph <= params['PH_IDEAL_MAXIMO']:
                if phosphorus and potassium:
                    return True, f"Umidade baixa ({humidity:.1f}%), pH ideal, nutrientes OK"
                elif phosphorus or potassium:
                    return True, f"Umidade baixa ({humidity:.1f}%), pH ideal, nutrientes parciais"
                else:
                    return True, f"Umidade baixa ({humidity:.1f}%), pH ideal, sem nutrientes"
            else:
                return False, f"Umidade baixa ({humidity:.1f}%), mas pH não ideal ({ph:.1f})"
        
        # Umidade alta - parar irrigação
        if humidity > params['UMIDADE_ALTA_PARAR_IRRIGACAO']:
            return False, f"Umidade alta ({humidity:.1f}%) - Irrigação desnecessária"
        
        # Condições normais
        return False, f"Condições normais - Bomba desligada (Umidade: {humidity:.1f}%)"
    
    def persist_data(self, data: Dict[str, Any]) -> bool:
        """
        Persiste os dados no banco de dados
        """
        try:
            # Converte timestamp string para datetime se necessário
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            # Usa o serviço para adicionar a leitura
            leitura_id = services.add_leitura(**data)
            
            logger.info(f"Dados persistidos com sucesso - ID: {leitura_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao persistir dados: {e}")
            return False
    
    def start(self):
        """Inicia o listener"""
        if self.running:
            logger.warning("Listener já está em execução")
            return
        
        self.running = True
        self.simulation_active = True
        
        logger.info("Iniciando WokwiListener...")
        logger.info("Pressione Ctrl+C para parar")
        
        try:
            while self.running:
                if self.simulation_active:
                    # Simula dados do Wokwi
                    data = self.simulate_wokwi_data()
                    
                    # Log dos dados
                    logger.info(f"Dados simulados: Umidade={data['umidade']}%, "
                              f"pH={data['ph_estimado']}, "
                              f"Bomba={'ON' if data['bomba_ligada'] else 'OFF'}")
                    
                    # Persiste no banco
                    success = self.persist_data(data)
                    
                    if success:
                        logger.debug("Dados persistidos com sucesso")
                    else:
                        logger.error("Falha ao persistir dados")
                
                # Aguarda intervalo de leitura (padrão: 5 segundos para simulação rápida)
                reading_interval = self.config.get('forecast_settings', {}).get('intervalo_leitura_minutos', 0.1) * 60
                if reading_interval < 5:  # Mínimo de 5 segundos para simulação
                    reading_interval = 5
                time.sleep(reading_interval)
                
        except KeyboardInterrupt:
            logger.info("Interrupção manual recebida")
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Para o listener"""
        if not self.running:
            return
        
        logger.info("Parando WokwiListener...")
        self.running = False
        self.simulation_active = False
        logger.info("WokwiListener parado")
    
    def pause_simulation(self):
        """Pausa a simulação sem parar o listener"""
        logger.info("Pausando simulação...")
        self.simulation_active = False
    
    def resume_simulation(self):
        """Resume a simulação"""
        logger.info("Retomando simulação...")
        self.simulation_active = True
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do listener"""
        return {
            "running": self.running,
            "simulation_active": self.simulation_active,
            "last_update": datetime.now().isoformat()
        }

class WokwiListenerManager:
    """
    Gerenciador para controlar múltiplas instâncias do listener
    ou para controle remoto via API
    """
    
    def __init__(self):
        self.listeners = {}
        logger.info("WokwiListenerManager inicializado")
    
    def create_listener(self, name: str = "default") -> WokwiListener:
        """Cria um novo listener"""
        if name in self.listeners:
            logger.warning(f"Listener '{name}' já existe")
            return self.listeners[name]
        
        listener = WokwiListener()
        self.listeners[name] = listener
        logger.info(f"Listener '{name}' criado")
        return listener
    
    def start_listener(self, name: str = "default") -> bool:
        """Inicia um listener específico"""
        if name not in self.listeners:
            self.create_listener(name)
        
        try:
            self.listeners[name].start()
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar listener '{name}': {e}")
            return False
    
    def stop_listener(self, name: str = "default") -> bool:
        """Para um listener específico"""
        if name not in self.listeners:
            logger.warning(f"Listener '{name}' não encontrado")
            return False
        
        try:
            self.listeners[name].stop()
            return True
        except Exception as e:
            logger.error(f"Erro ao parar listener '{name}': {e}")
            return False
    
    def get_listener_status(self, name: str = "default") -> Optional[Dict[str, Any]]:
        """Obtém status de um listener"""
        if name not in self.listeners:
            return None
        
        return self.listeners[name].get_status()
    
    def list_listeners(self) -> list[str]:
        """Lista todos os listeners"""
        return list(self.listeners.keys())

def main():
    """Função principal para execução direta"""
    print("=== FarmTech Wokwi Listener ===")
    print("Simulador de dados para integração com dashboard")
    print()
    
    try:
        # Cria e inicia o listener
        listener = WokwiListener()
        listener.start()
        
    except KeyboardInterrupt:
        print("\nEncerrando...")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()