# **PROTOCOLO SOVEREIGN: ARQUITETURA DE AGENTE AUTÔNOMO DE CONTROLE COMPUTACIONAL GERAL (GCC)**

Classificação: Vanguarda / Pesquisa Irrestrita  
Versão: 3.0 (Modular / Híbrida / Robustecida)
Data: 2025  
Autor: Especialista em LLMs & Engenharia de Sistemas (Refatorado por Jules)

## **1\. RESUMO EXECUTIVO**

Este documento detalha a implementação técnica do **Protocolo Sovereign V3**, um sistema de Inteligência Artificial Agêntica projetado para operar computadores pessoais (General Computer Control - GCC) com total autonomia.

A arquitetura mantém a abordagem híbrida (Cérebro Remoto + Corpo Local) mas foi completamente refatorada para modularidade, robustez e capacidade de teste.

## **2\. ARQUITETURA DE SOFTWARE (V3)**

O sistema foi dividido em módulos independentes dentro do pacote `core/`:

### **2.1. Cérebro (`core/brain`)**
*   **Planner:** Utiliza DeepSeek V3 (via API OpenAI-compatible) com um prompt de sistema estruturado para pensamento "Chain of Thought".
*   **Memory:** Implementa uma memória de curto prazo (deque) para manter contexto das últimas ações e observações, permitindo recuperação de falhas.

### **2.2. Visão (`core/vision`)**
*   **VisionClient:** Integração com **UI-TARS 7B** via Ollama.
*   **ActionParser:** Um parser robusto capaz de interpretar o formato nativo do UI-TARS (`click(point='<point>x y</point>')`), além de lidar com normalização de coordenadas (0-1000 -> Pixels).
*   **OCRProcessor:** Wrapper robusto do Tesseract com pré-processamento de imagem para leitura de estado do sistema (texto).

### **2.3. Ação (`core/action`)**
*   **Motor:** Wrapper seguro para `pyautogui` com verificação de falhas e suporte a teclas especiais.
*   **Segurança:** Mantém o `FAILSAFE=True` (movimento brusco do mouse para o canto da tela aborta o agente).

## **3\. COMO EXECUTAR**

### **3.1. Pré-requisitos**
1.  **Python 3.10+**
2.  **Ollama** rodando localmente com o modelo UI-TARS (`ollama run ui-tars`).
3.  **Tesseract OCR** instalado no sistema (`sudo apt install tesseract-ocr`).
4.  **Chave de API DeepSeek**.

### **3.2. Instalação**

```bash
pip install -r requirements.txt
```

### **3.3. Configuração**

Crie um arquivo `.env` ou exporte as variáveis:

```bash
export DEEPSEEK_API_KEY="sk-..."
export MODEL_VISION="ui-tars" # Nome do modelo no Ollama
```

### **3.4. Execução**

```bash
python3 main.py
```

## **4\. CAPACIDADES**

*   **Planejamento Estratégico:** O agente analisa a tela via OCR antes de agir.
*   **Interação Visual:** Usa UI-TARS para clicar em elementos que não têm texto selecionável.
*   **Loop de Feedback:** O agente verifica o resultado de suas ações (via OCR e Memória) e ajusta o plano se falhar.

---
*Aviso: Este software concede controle total do seu mouse e teclado a uma IA. Use com cautela e monitore a execução.*
