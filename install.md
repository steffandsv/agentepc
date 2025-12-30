# Guia de Instalação e Configuração

Este guia detalha as dependências necessárias para rodar o Agente Sovereign em um ambiente Linux (Ubuntu/Debian) e como configurar o ambiente para evitar problemas comuns de captura de tela.

## 1. Dependências do Sistema

O `pyautogui` e o `pytesseract` dependem de ferramentas do sistema operacional para controlar o mouse/teclado e processar imagens.

Execute o seguinte comando no terminal:

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-tk \
    python3-dev \
    scrot \
    tesseract-ocr \
    tesseract-ocr-por \
    xclip \
    xsel \
    libgirepository1.0-dev \
    libcairo2-dev
```

*   **scrot**: Essencial para o `pyautogui` tirar prints da tela no Linux.
*   **tesseract-ocr**: Engine de OCR para ler o texto da tela.
*   **xclip/xsel**: Gerenciamento de área de transferência.

## 2. Configuração de Auto-Login (Bypass de Tela de Bloqueio)

Scripts de automação de usuário (como este) **não conseguem** interagir com a tela de login (GDM/LightDM) ou a tela de bloqueio do Linux por restrições de segurança do X11/Wayland. Se o agente "vê" uma tela preta ou OCR com 0 caracteres, é provável que a tela esteja bloqueada.

### Solução:
Habilite o **Login Automático** nas configurações do seu sistema:

1.  Vá em **Configurações** -> **Usuários**.
2.  Desbloqueie o painel.
3.  Ative a opção **Login Automático**.

Isso garante que, ao ligar o PC ou reiniciar, o ambiente gráfico do usuário seja carregado imediatamente, permitindo que o agente comece a operar.

## 3. Notas sobre Resolução (Headless)

Se você está rodando em um servidor sem monitor (headless), a resolução padrão pode ser **1024x768**. O agente foi ajustado para funcionar nesta resolução nativa.

Se desejar aumentar a resolução para melhorar a precisão do modelo de visão (recomendado 1920x1080), você pode usar um "Dummy Plug" HDMI ou configurar o Xorg para forçar uma resolução maior.
