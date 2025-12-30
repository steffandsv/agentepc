import os
# --- CONFIGURAÇÃO DE DISPLAY ---
os.environ["DISPLAY"] = ":0"

import re
import time
import base64
import pyautogui
import ollama
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image

# --- CONFIGURAÇÕES ---
load_dotenv()

# Cliente DeepSeek (Cérebro)
CLIENT_DS = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

MODELO_VISAO_LOCAL = "ui-tars"
SENHA_DO_PC = "sua_senha_aqui" # Opcional: Para desbloquear tela se necessário

# Configurações do PyAutoGUI
pyautogui.FAILSAFE = True 
pyautogui.PAUSE = 1.5 # Aumentei a pausa para dar tempo das janelas abrirem

def acordar_monitor():
    """Garante que a tela não está dormindo"""
    print("⏰ Acordando monitor...")
    pyautogui.press('esc')
    pyautogui.moveRel(10, 0)
    time.sleep(1)

def capturar_tela_pil():
    """Captura a tela retornando objeto PIL para análise"""
    return pyautogui.screenshot()

def ler_texto_da_tela(imagem):
    """OCR: Lê o texto visível na tela para dar contexto ao DeepSeek"""
    try:
        # Pega apenas textos relevantes (fatia superior e centro geralmente)
        texto = pytesseract.image_to_string(imagem)
        # Limpa quebras de linha excessivas
        texto_limpo = " ".join([linha.strip() for linha in texto.splitlines() if linha.strip()])
        return texto_limpo[:1000] # Limita a 1000 caracteres para não confundir o prompt
    except Exception as e:
        print(f"⚠️ Erro no OCR: {e}")
        return "Texto ilegível"

def converter_para_base64(imagem):
    buffered = BytesIO()
    imagem.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def cerebro_planejador(objetivo, historico, texto_tela):
    """DeepSeek: Agora enxerga o contexto textual!"""
    print("\n🧠 DeepSeek está analisando a situação...")
    
    prompt_sistema = f"""
    Você é um Operador de Computador Linux Experiente.
    Seu trabalho é cumprir o objetivo visualizando o estado atual da máquina.
    
    ESTADO ATUAL (O que está escrito na tela):
    "{texto_tela}"
    
    REGRAS DE SOBREVIVÊNCIA:
    1. Se ler "Password", "Unlock" ou hora/data gigante, a tela está BLOQUEADA. Mande digitar a senha.
    2. Se o objetivo é usar o terminal, mas você NÃO vê um prompt como 'user@host' ou '$', o terminal NÃO está aberto. Mande abrir de novo.
    3. Nunca digite comandos (sudo apt...) se o terminal não estiver confirmado visualmente.
    
    Retorne APENAS a próxima ação imediata. Seja atômico.
    """

    prompt_usuario = f"""
    Objetivo: {objetivo}
    Histórico Recente: {historico}
    
    Qual o próximo passo?
    """
    
    try:
        response = CLIENT_DS.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.5 # Menos criativo, mais preciso
        )
        plano = response.choices[0].message.content.strip()
        print(f"💡 Plano Baseado em Visão: {plano}")
        return plano
    except Exception as e:
        print(f"❌ Erro DeepSeek: {e}")
        return "Aguardar"

def executor_visual(instrucao_passo, imagem_pil):
    """UI-TARS: Encontra onde clicar"""
    print(f"👁️ UI-TARS buscando coordenadas para: '{instrucao_passo}'")
    
    img_b64 = converter_para_base64(imagem_pil)
    
    try:
        response = ollama.chat(
            model=MODELO_VISAO_LOCAL,
            messages=[{
                'role': 'user',
                'content': f"Instruction: {instrucao_passo}",
                'images': [img_b64]
            }]
        )
        acao = response['message']['content'].strip()
        print(f"🤖 UI-TARS sugere: {acao}")
        return acao
    except Exception as e:
        print(f"❌ Erro UI-TARS: {e}")
        return None

def realizar_acao_fisica(comando):
    """Executa a ação física com correção de escala"""
    largura_tela, altura_tela = pyautogui.size()
    
    try:
        # --- DESBLOQUEIO DE EMERGÊNCIA ---
        # Se o DeepSeek mandou desbloquear explicitamente
        if "desbloquear" in comando.lower() or "senha" in comando.lower():
            pyautogui.write(SENHA_DO_PC)
            pyautogui.press('enter')
            return True

        # --- CLIQUE ---
        if "click" in comando:
            # Regex ajustado para pegar (x, y)
            match = re.search(r"\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)", comando)
            if match:
                x_raw = float(match.group(1))
                y_raw = float(match.group(2))
                
                # CORREÇÃO DE ESCALA 1000 -> PIXEL
                # UI-TARS geralmente usa 0-1000.
                if x_raw > 1: x_raw = x_raw / 1000
                if y_raw > 1: y_raw = y_raw / 1000
                
                x_real = int(x_raw * largura_tela)
                y_real = int(y_raw * altura_tela)
                
                print(f"🎯 Clique: ({x_real}, {y_real})")
                pyautogui.moveTo(x_real, y_real, duration=0.8) # Movimento mais humano
                pyautogui.click()
                return True
            
        # --- DIGITAÇÃO ---
        elif "type" in comando:
            match_texto = re.search(r'type\((["\'])(.*?)\1\)', comando)
            if match_texto:
                texto = match_texto.group(2)
                print(f"⌨️ Digitando: {texto}")
                pyautogui.write(texto, interval=0.1) # Digitação mais lenta para o XFCE pegar
                pyautogui.press('enter')
                return True
                
        # --- TECLAS ---
        elif "key" in comando:
            match_key = re.search(r'key\((["\'])(.*?)\1\)', comando)
            if match_key:
                tecla = match_key.group(2)
                # Mapeamento de teclas comuns que IA erra
                if tecla == "return": tecla = "enter"
                if tecla == "super": tecla = "win" # Tecla Windows
                
                print(f"🎹 Pressionando: {tecla}")
                pyautogui.press(tecla)
                return True

        return False
    except Exception as e:
        print(f"❌ Erro motor: {e}")
        return False

def main():
    print("--- AGENTE V2 (COM VISÃO OCR) INICIADO ---")
    acordar_monitor()
    
    objetivo = input(">> Objetivo: ")
    historico = []
    
    while True:
        # 1. Captura Estado Real
        imagem_atual = capturar_tela_pil()
        
        # 2. Lê o que está escrito (OCR)
        texto_tela = ler_texto_da_tela(imagem_atual)
        # print(f"📜 Texto detectado: {texto_tela[:100]}...") # Debug
        
        # 3. Planeja com base na realidade
        proximo_passo = cerebro_planejador(objetivo, historico[-4:], texto_tela)
        
        # 4. Encontra onde clicar
        comando_acao = executor_visual(proximo_passo, imagem_atual)
        
        if comando_acao:
            # 5. Executa
            sucesso = realizar_acao_fisica(comando_acao)
            
            status = "Sucesso" if sucesso else "Falha"
            historico.append(f"Tela mostrava: '{texto_tela[:30]}...' -> Tentei: {proximo_passo} -> Resultado: {status}")
        
        time.sleep(3) # Pausa vital para a interface gráfica reagir

if __name__ == "__main__":
    main()