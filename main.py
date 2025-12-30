import os
import time
import sys

# 1. Configuração CRÍTICA de Display antes de qualquer import gráfico
# Isso garante que o PyAutoGUI saiba onde rodar
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

try:
    import pyautogui
except ImportError:
    print("ERRO: PyAutoGUI não instalado ou dependências de sistema faltando.")
    print("Execute: sudo apt install python3-tk python3-dev scrot xclip")
    sys.exit(1)

from datetime import datetime
from core.brain.planner import Planner
from core.brain.memory import ShortTermMemory
from core.vision.client import VisionClient
from core.vision.parser import ActionParser
from core.vision.ocr import OCRProcessor
from core.action.motor import Motor

# Configurações de segurança do PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.5  # Aumentado para 1.5s igual ao script antigo (dá tempo da UI responder)

def wake_up_screen():
    """
    Função vital: Garante que a tela não está em modo de economia de energia (tela preta).
    Sem isso, o OCR lê 'nada' e o agente falha.
    """
    try:
        pyautogui.press('esc')
        pyautogui.moveRel(10, 0)
        time.sleep(0.5)
        pyautogui.moveRel(-10, 0)
    except Exception as e:
        print(f"Aviso: Não foi possível acordar o monitor: {e}")

def main():
    print("--- SOVEREIGN AGENT V3 (CORRIGIDO) ---")
    
    # Inicializa Componentes
    memory = ShortTermMemory()
    planner = Planner()
    vision = VisionClient()
    ocr = OCRProcessor()
    motor = Motor()
    
    # Detecção Robusta de Tela
    try:
        w, h = pyautogui.size()
        print(f"DEBUG: Resolução detectada: {w}x{h}")
    except Exception as e:
        print(f"ALERTA: Falha ao detectar tela ({e}). Assumindo 1024x768 (Safe Mode).")
        w, h = 1024, 768

    parser = ActionParser(w, h)
    
    objective = input(">> ENTER OBJECTIVE: ")
    
    while True:
        print("\n--- NEW CYCLE ---")
        cycle_id = datetime.now().strftime("%H%M%S")

        # 1. ACORDAR (Passo que faltava!)
        wake_up_screen()
        time.sleep(1) # Espera a tela acender

        # 2. PERCEPÇÃO
        try:
            screenshot = pyautogui.screenshot()
        except Exception as e:
            print(f"CRÍTICO: Falha ao tirar screenshot. Instale o 'scrot' (sudo apt install scrot). Erro: {e}")
            time.sleep(5)
            continue

        # Debug visual (Salva o que o robô está vendo)
        screenshot.save(f"debug_monitor_latest.png")
        
        screen_text = ocr.extract_text(screenshot)
        
        # Verificação de Cegueira
        if not screen_text.strip():
            print("(!) AVISO: Tela parece vazia ou bloqueada. Tentando desbloqueio cego...")
            # Se não vê nada, tenta dar Enter para tirar screensaver
            pyautogui.press('enter')
            time.sleep(2)
            continue
            
        print(f"PERCEPTION (OCR): {screen_text[:100]}...")
        
        # 3. PLANEJAMENTO (Cérebro)
        high_level_plan = planner.plan_next_step(objective, memory, screen_text)
        print(f"🧠 PLANO: {high_level_plan}")

        # 4. GROUNDING (Visão)
        raw_action = vision.get_action(high_level_plan, screenshot)
        action_data = parser.parse(raw_action)

        # 5. AÇÃO (Motor)
        success = False
        if action_data:
            print(f"⚡ EXECUÇÃO: {action_data}")
            success = motor.execute(action_data)
            status = "SUCCESS" if success else "FAILED"
        else:
            print(f"FALHA: Não foi possível traduzir a ação: {raw_action}")
            status = "FAILED PARSING"

        # 6. MEMÓRIA
        memory.add_event(f"Plano: {high_level_plan} -> Ação: {raw_action} -> Resultado: {status}")
        
        time.sleep(2)

if __name__ == "__main__":
    main()