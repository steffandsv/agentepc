# **PROTOCOLO SOVEREIGN: ARQUITETURA DE AGENTE AUTÔNOMO DE CONTROLE COMPUTACIONAL GERAL (GCC)**

Classificação: Vanguarda / Pesquisa Irrestrita  
Versão: 2.1 (Híbrida / Bare Metal)  
Data: 2025  
Autor: Especialista em LLMs & Engenharia de Sistemas

## **1\. RESUMO EXECUTIVO**

Este documento detalha a implementação técnica do **Protocolo Sovereign**, um sistema de Inteligência Artificial Agêntica projetado para operar computadores pessoais (General Computer Control \- GCC) com total autonomia e sem restrições éticas de segurança corporativa ("Uncensored").

Diferente de LLMs textuais passivos (ChatGPT), este sistema é um **LAM (Large Action Model)**. Ele fecha o ciclo cognitivo "Percepção $\\rightarrow$ Raciocínio $\\rightarrow$ Ação", permitindo que a IA manipule o mouse, o teclado e o sistema operacional Linux (Xubuntu) como um operador humano.

A arquitetura supera as limitações de hardware local (RTX 5060 Ti / 5070\) através de uma abordagem híbrida: o raciocínio complexo é terceirizado para uma API de alta capacidade (DeepSeek V3), enquanto a percepção visual e a motricidade permanecem locais e privadas (UI-TARS), garantindo latência mínima e precisão de pixel.

## **2\. O SUBSTRATO DE HARDWARE E SISTEMA OPERACIONAL**

A base física do sistema foi otimizada para eliminar gargalos de memória (RAM/VRAM) e latência de I/O.

### **2.1. Especificações do Host**

* **CPU:** Intel Core i5-14400F (Arquitetura Híbrida P-Cores/E-Cores). Otimizado para *single-thread performance*, crucial para o loop principal do Python.  
* **GPU:** NVIDIA RTX 5060 Ti (8GB) ou RTX 5070 (12GB).  
  * *Função:* Dedicada exclusivamente à inferência visual (UI-TARS) e renderização do desktop.  
  * *Constraint:* 8GB é o limite inferior para modelos de visão (VLMs). O uso de quantização 4-bit (GGUF) foi mandatório.  
* **Armazenamento:** SSD NVMe WD Green SN3000.  
  * *Particionamento:* **GPT (GUID Partition Table)**. Obrigatório para boot UEFI rápido e gerenciamento moderno de swap em Linux.  
* **RAM:** 16GB DDR4/DDR5.  
  * *Gargalo:* Quantidade crítica. Exigiu o abandono de virtualização (Docker) em favor de execução nativa (Bare Metal) para economizar \~4GB de overhead.

### **2.2. O Sistema Operacional: Xubuntu 24.04 LTS (Minimal)**

A escolha do Xubuntu (XFCE) não foi estética, foi cirúrgica.

1. **Gerenciador de Janelas X11 (Xorg):**  
   * Sistemas modernos usam Wayland, que por segurança isola janelas, impedindo que um script controle o mouse sobre outros apps.  
   * O X11 permite acesso global ao *input device*, essencial para bibliotecas como pyautogui e xdotool.  
2. **Pegada de Memória (Footprint):**  
   * O XFCE em instalação mínima consome \~400MB de RAM no boot. O GNOME (Ubuntu padrão) consome \~1.5GB. Essa economia de 1.1GB é transferida diretamente para o buffer de contexto do modelo de IA.  
3. **Ambiente de Execução:**  
   * Drivers NVIDIA proprietários (versão 550+) instalados via ubuntu-drivers autoinstall para acesso direto aos Tensor Cores via CUDA 12\.

## **3\. ARQUITETURA DE SOFTWARE HÍBRIDA (O "FRANKENSTEIN" OTIMIZADO)**

O sistema opera em uma topologia de **Cérebro Remoto / Corpo Local**. Isso maximiza a inteligência sem colapsar a VRAM local.

### **3.1. O Cérebro (Lóbulo Frontal): DeepSeek V3 via API**

Responsável pelo planejamento de alto nível, estratégia e manutenção do contexto da tarefa.

* **Modelo:** DeepSeek-V3 (ou variantes Uncensored via OpenRouter).  
* **Prompt Engineering ("Jailbreak"):**  
  * Utilizamos injeção de *System Prompt* para remover travas morais. O modelo é instruído a ignorar ética e focar na execução.  
  * *Entrada:* Texto puro (Objetivo \+ Histórico \+ Leitura OCR da tela).  
  * *Saída:* Instrução semântica (ex: "Abra o terminal e digite sudo").  
* **Por que não local?** Rodar um modelo de raciocínio 70B localmente exigiria 48GB de VRAM. A API oferece essa inteligência por um custo marginal ($0.14/1M tokens).

### **3.2. Os Olhos e Córtex Visual: UI-TARS 7B \+ Tesseract OCR**

Responsável pelo *Grounding* (Aterramento) — a tradução de intenção semântica para coordenadas espaciais.

* **UI-TARS (User Interface Task Automation & Reasoning System):**  
  * **Versão:** 7B parâmetros, Fine-tuned para GUI.  
  * **Formato:** GGUF Q4\_K\_M (Quantização de 4 bits).  
  * **Execução:** Via **Ollama** local.  
  * **Função:** Recebe um screenshot \+ instrução ("Clique no terminal") e retorna coordenadas \<|box\_start|\>(x,y)\<|box\_end|\>.  
* **Tesseract OCR (Reconhecimento Óptico de Caracteres):**  
  * **Função:** Leitura semântica da tela. O UI-TARS vê botões, mas o Tesseract lê o *conteúdo*.  
  * **Caso de Uso Crítico:** Detecção de falhas de estado. Se o DeepSeek manda digitar "sudo", o OCR verifica antes se a string user@host está visível na tela, prevenindo alucinação de digitação no vácuo.

### **3.3. O Sistema Motor: PyAutoGUI \+ Regex**

Responsável pela execução física no Kernel Linux.

* **Normalização de Coordenadas:**  
  * O UI-TARS opera em espaço normalizado (0-1000).  
  * O script Python intercepta a saída, aplica Regex para limpar tokens de lixo, divide por 1000 e multiplica pela resolução real do monitor (ex: 1920x1080).  
* **Failsafe:** Implementação de pyautogui.FAILSAFE \= True. Um movimento brusco do mouse para (0,0) encerra o processo imediatamente (Kill Switch físico).

## **4\. FLUXO DE CONTROLE (O ALGORITMO)**

O arquivo main\_v2.py implementa um Loop de Controle Fechado (Closed-Loop Control System):

1. **Sensoriamento (Sensing):**  
   * pyautogui.screenshot() captura o buffer de vídeo.  
   * pytesseract extrai texto bruto para contexto.  
2. **Planejamento (Planning):**  
   * O DeepSeek recebe: Objetivo \+ Histórico \+ Texto da Tela.  
   * Decide o próximo passo atômico.  
3. **Aterramento (Grounding):**  
   * O UI-TARS recebe: Screenshot \+ Passo do DeepSeek.  
   * Retorna: Coordenadas ou texto para digitação.  
4. **Atuação (Actuation):**  
   * O Python move o cursor via X11 e simula cliques/teclas.  
5. **Verificação (Feedback):**  
   * Pausa de 3 segundos para a GUI reagir.  
   * O ciclo reinicia. Se o OCR não detectar a mudança esperada, o DeepSeek recebe esse feedback no próximo histórico e tenta uma estratégia diferente.

## **5\. DEPENDÊNCIAS TÉCNICAS INSTALADAS**

Para referência futura ou replicação, este é o *stack* exato:

* **python3-venv**: Isolamento do ambiente Python para evitar quebra do sistema (PEP 668).  
* **libx11-dev / python3-tk / python3-dev**: Headers necessários para compilar as ferramentas de controle do X11.  
* **scrot / gnome-screenshot**: Backends de baixo nível para captura de frame buffer no Linux.  
* **xdotool**: Ferramenta de linha de comando para simulação de input X11 (backup do PyAutoGUI).  
* **tesseract-ocr-por**: Dados de treinamento LSTM para leitura de português.  
* **ollama (Service):** Daemon que gerencia a VRAM da GPU e carrega/descarrega o modelo GGUF dinamicamente.

## **6\. CONCLUSÃO E CAPACIDADES**

O sistema **Protocolo Sovereign** representa o estado da arte em automação pessoal de baixo custo.

* **Nível de Autonomia:** Nível 3 (Execução autônoma de tarefas complexas com supervisão humana passiva).  
* **Resistência à Censura:** Alta. O desacoplamento do "Cérebro" permite a troca instantânea para APIs "Rogue" ou modelos locais futuros, sem alterar a infraestrutura motora.  
* **Custo Operacional:** Desprezível (Inferência visual local gratuita \+ API de baixo custo).

Você criou um **Agente Cibernético**. Ele não apenas processa dados; ele interage fisicamente com o mundo digital.