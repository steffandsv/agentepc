#Infraestrutura Bare-Metal do Agente Autônomo (Qwen GGUF + llama.cpp + API local + Navegador Automatizado)

> **Objetivo**: registrar, com precisão técnica, a infraestrutura **bare-metal** montada para executar um modelo **Qwen** localmente (formato **GGUF**, quantizado), servi-lo via **llama.cpp** como API HTTP estilo OpenAI (`/v1/*`) e acoplá-lo a um agente de automação de navegador em Python.
>
> **Princípio**: um agente que trabalha “por horas” não é um demo. Ele exige **previsibilidade** (infra estável), **disciplinas de recursos** (VRAM/RAM/IO), **interfaces padronizadas** (HTTP) e **instalação reprodutível** (toolchain versionada).

---

## 1) Visão arquitetural (o que foi efetivamente construído)

A solução foi estabelecida como **dois processos nativos** comunicando-se via loopback (localhost), sem contêineres:

1. **Servidor LLM local (inferência)**  
   - Runtime: **llama.cpp** (binário `llama-server`) compilado nativamente em modo release  
   - Modelo: **Qwen** em **GGUF** (quantizado)  
   - Aceleração: **CUDA** (GPU NVIDIA) com build direcionado à arquitetura da placa  
   - Interface: **HTTP** em `127.0.0.1:8080` expondo endpoints compatíveis com “OpenAI-like”:  
     - `GET /v1/models`  
     - `POST /v1/chat/completions` (e afins, conforme build)

2. **Agente de Navegador (orquestração e execução web)**  
   - Runtime: Python  
   - Navegação/ação: Playwright/Chromium (ou equivalente)  
   - Consumo do LLM: HTTP local (base_url apontando para `http://127.0.0.1:8080/v1`)  
   - Regra operacional: o browser deve **evitar disputar VRAM** com o LLM (GPU do navegador desabilitada quando necessário)

Topologia lógica:

```
[ Agente Python (browser automation) ]  --->  HTTP localhost  --->  [ llama-server (Qwen GGUF + CUDA) ] ---> GPU
             |
             +--> Chromium/Playwright (CPU/RAM)   (GPU opcionalmente desabilitada para preservar VRAM do LLM)
```

**Motivo estrutural dessa separação:**  
- desacopla o “cérebro” (LLM) do “corpo” (browser)  
- permite reiniciar e versionar cada peça independentemente  
- reduz superfície de falha (o LLM não depende da pilha do browser)  
- torna o LLM um **serviço de infraestrutura**, e não “um comando no terminal”

---

## 2) Inventário técnico do servidor (componentes que determinaram decisões)

### 2.1 Plataforma (SO e toolchain)
- Sistema operacional: **Pop!_OS** (base Ubuntu 24.04)  
- Gerenciador de serviços: **systemd**  
- CMake: **3.28** (módulos de teste CUDA observados em `/usr/share/cmake-3.28/...`)  
- Python do sistema: **3.12.3** (observado durante instalação via pipx)  
- Política Python: **PEP 668** (“externally managed environment”)

**Implicação direta:** o host proíbe instalação “pip global” de pacotes não empacotados pela distro sem exceção explícita. Essa política evita quebrar o Python do sistema — e foi respeitada.

### 2.2 GPU / VRAM (o gargalo real)
- GPU: **NVIDIA GeForce RTX 5060 Ti**  
- VRAM: **8 GB**  
- Arquitetura CUDA alvo utilizada na compilação: **compute_120 / sm_120** (compatível com a série/geração detectada no processo)

**Por que isso muda tudo:**  
- O tamanho do modelo, o contexto (`n_ctx`) e o KV-cache competem por VRAM.  
- O navegador (Chromium) pode consumir VRAM de forma imprevisível (compositor, aceleração, texturas).  
- Em agentes long-running, o problema não é “rodar uma vez”; é **não degradar** com horas de uso, picos de carga e flutuações de memória.

### 2.3 Memória RAM (limite operacional)
- RAM do host: **16 GB**

Impacto:
- Compilar CUDA com paralelismo alto pode explodir RAM e encerrar processos (“Killed” por OOM).  
- Rodar browser + LLM + buffers exige disciplina de contexto e parâmetros de servidor.

### 2.4 Itens de hardware **não registrados neste ato**
Este documento registra apenas os itens explicitamente observados no processo. Informações como **modelo de CPU**, **armazenamento (NVMe/SATA)**, **swap**, **driver exato** e **topologia PCIe** não foram capturadas no diálogo de montagem.  
> **Regra de governança:** não inventar especificação. Se esses itens forem críticos para auditoria/performance, devem ser anexados como adendo com evidências (`lscpu`, `lsblk`, `nvidia-smi`, etc.).

---

## 3) Hardening “servidor-grade”: por que antes do modelo vem estabilidade

O primeiro conjunto de falhas não foi “IA”. Foi infraestrutura clássica:

- downloads grandes interrompidos (arquivo parcial tratado como completo)
- “checksum/digest mismatch” (assinatura inválida)
- timeouts e intermitência de resolução (DNS)
- risco de suspensão/hibernação interrompendo transferências longas

### 3.1 Controle de suspensão (energia/uptime)
Em desktop convertido em servidor, suspensão automática destrói confiabilidade. A política aplicada foi:

- bloquear suspensão por idle (nível de sessão/desktop)
- bloquear targets de suspensão/hibernação no systemd

**Efeito prático:** elimina a classe de bugs “download começou, travou, arquivo ficou vazio/0 bytes” e “serviço caiu sem log útil”.

### 3.2 DNS e consistência de resolução (systemd-resolved)
Em Ubuntu/Pop, a resolução passa por `systemd-resolved`. Se `/etc/resolv.conf` não aponta para o stub correto (ou se caches ficam inconsistentes), aparece:

- falha de resolução intermitente
- conexões TCP que iniciam e travam
- downloads que falham “aleatoriamente”

A correção foi alinhar `resolv.conf` ao stub do resolved e reiniciar/resincronizar caches, estabilizando rede e downloads.

---

## 4) Por que Qwen (e por que exatamente Qwen 8B)

A escolha do modelo foi uma decisão de engenharia guiada por **restrições de hardware + perfil de tarefa**.

### 4.1 Critérios que governaram a escolha
1) **Rodar localmente** no servidor atual (sem serviços externos).  
2) **Qualidade suficiente** para planejamento, instruções e coordenação de ações web.  
3) **Capacidade multilíngue**, com foco em português (entrada/saída naturais).  
4) **Tamanho compatível** com VRAM e com execução paralela ao browser.  
5) **Ecossistema disponível** em GGUF para execução via llama.cpp.

### 4.2 Por que “8B” (trade-off real)
- Modelos menores tendem a perder robustez em cadeias de decisão longas (agente web).  
- Modelos maiores frequentemente inviabilizam operação estável com VRAM de 8 GB, especialmente com contexto alto e KV-cache grande.  

**8B** é o ponto em que:
- ainda é capaz de raciocínio/orquestração,
- e ainda pode ser viabilizado com quantização e parâmetros conservadores de contexto.

### 4.3 Metadados do modelo carregado (evidência operacional)
Ao consultar `GET /v1/models`, o servidor reportou (como fatos observados):
- `n_params`: **8.190.735.360** (≈ 8,19B)  
- `size`: **5.021.827.072 bytes** (≈ 5,02 GB)  
- `n_ctx_train`: **32.768** (contexto de treino do modelo)  
- `n_vocab`: **151.936**  

Esses números são relevantes porque definem:
- pressão de VRAM e RAM,
- limites de contexto teóricos,
- e expectativas realistas de desempenho.

---

## 5) Por que GGUF e por que Q4_K_M (quantização como condição de viabilidade)

### 5.1 GGUF como “artefato operacional”
GGUF (no ecossistema ggml/llama.cpp) é escolhido por:
- portabilidade e rapidez de load
- viabilidade sem runtime pesado (sem PyTorch)
- compatibilidade direta com `llama-server`
- distribuição de pesos quantizados em múltiplas variantes

### 5.2 Por que quantização não é opcional aqui
Sem quantização, um 8B em FP16 exige VRAM muito maior. Em VRAM de 8 GB:
- o modelo em precisão alta + KV-cache + overhead do runtime = instabilidade ou impossibilidade.
- quantização reduz footprint mantendo utilidade para planejamento/execução.

### 5.3 Por que Q4_K_M (o compromisso correto)
`Q4_K_M` é uma quantização 4-bit “K-quant” otimizada para boa relação qualidade/memória:
- reduz footprint para caber com folga na VRAM disponível
- preserva qualidade suficiente para tarefas de agente (coordenação + instruções)
- evita o comportamento “capenga” de quantizações agressivas demais (pior aderência a instruções)

---

## 6) Por que o download teve que ser daquele jeito (HF CLI via pipx) — e não “pip global” ou wget

### 6.1 O bloqueio PEP 668 e a decisão correta
O host retornou `externally-managed-environment` ao tentar instalar pacotes via pip no Python do sistema.  
Isso é proposital: impede quebrar o stack Python da distro.

**Decisão adotada:** usar **pipx** (CLI isolada em ambiente virtual gerenciado), em vez de:
- `--break-system-packages` (alto risco de corromper o Python do host)
- depender de ferramentas “ad hoc” que não lidam bem com retomada/validação

### 6.2 Por que `hf` (e não `huggingface-cli`)
A instalação via pipx expôs executáveis como:
- `hf` (cliente principal)
- outros utilitários

O comando esperado “`huggingface-cli`” não existiu no PATH porque o executável correto era **`hf`** e porque, em muitas instalações, `~/.local/bin` precisa estar no PATH do shell.

### 6.3 Por que `hf download` é superior para esse caso
Para arquivos de múltiplos GB, `hf download` oferece:
- seleção por nome exato / include patterns
- melhor controle de erros e consistência de repositório
- menor probabilidade de ficar com “arquivo parcial que parece completo”

Isso foi crucial porque o ambiente já havia demonstrado fragilidade anterior com downloads interrompidos (energia/rede) e a equipe não aceitou “baixou, acho que foi” como critério.

### 6.4 O erro “Entry Not Found” e o que ele revela
O erro aconteceu porque o nome do arquivo GGUF solicitado não existia no repo — o arquivo real tinha um prefixo diferente (por exemplo, `Qwen_Qwen3-...` em vez de `Qwen3-...`).

**Lição infra:** para artefatos versionados, *nome exato* é parte do contrato. A infraestrutura foi ajustada para validar nomes e evitar suposições.

---

## 7) Por que compilar dessa forma (llama.cpp “nativo”, CUDA alinhado ao SM) — e não aceitar fallback

### 7.1 Objetivo da compilação: performance + previsibilidade
Compilar “do jeito certo” significa:
- gerar binário `Release`
- ativar backend CUDA (GPU)
- desativar superfícies não necessárias (tests/examples) para reduzir pontos de falha
- direcionar a arquitetura CUDA (`CMAKE_CUDA_ARCHITECTURES`) para o SM real do hardware

### 7.2 O erro crítico: `nvcc fatal: Unsupported gpu architecture 'compute_120'`
Ao configurar `compute_120`, o `nvcc` falhou no teste simples do CMake. Isso prova que:
- o runtime do driver pode estar OK,
- mas o **toolkit CUDA (nvcc)** era antigo e não conhecia a arquitetura alvo.

**Diagnóstico correto:** não é “bug do llama.cpp”; é incompatibilidade de toolchain.

### 7.3 Por que não usar “arquitetura genérica” (quando o objetivo é extrair o máximo)
Usar arquiteturas antigas ou genéricas pode:
- gerar código subótimo
- forçar PTX JIT ou caminhos de compatibilidade
- aumentar latência, reduzir throughput e piorar comportamento sob carga

Como o requisito era “máximo do hardware”, a infra foi orientada a compilar para a arquitetura nativa da GPU.

### 7.4 CUDA usado e por que foi necessário trocar
**CUDA Toolkit instalado:** **12.9** (em `/usr/local/cuda-12.9`)  
Motivo: versões anteriores do `nvcc` não suportavam `compute_120`, bloqueando build direcionado.

A escolha foi instalar o toolkit oficial da NVIDIA (via repositório/keyring) e evitar depender do `nvidia-cuda-toolkit` da distro quando este se mostrou defasado para o alvo.

### 7.5 Consequências práticas do build “limpo”
O build foi feito com:
- diretório `build` recriado do zero (evita cache/config corrompida)
- gerador Ninja (melhor feedback e rapidez)
- paralelismo moderado (evita OOM em 16 GB RAM)

Resultado: `llama-server` foi compilado e executado com sucesso com CUDA habilitado.

---

## 8) Servidor LLM: por que API local, por que loopback, por que esse modelo aparece em `/v1/models`

### 8.1 API local (OpenAI-like) como “contrato” entre cérebro e corpo
Servir via HTTP local cria um contrato estável:
- o agente pode ser refeito sem tocar no runtime do modelo
- o modelo pode ser trocado sem reescrever o agente
- o mesmo padrão se estende para múltiplos workers no futuro

### 8.2 Segurança por padrão: bind em `127.0.0.1`
`127.0.0.1` significa:
- somente processos locais conseguem acessar
- não há superfície exposta na LAN/WAN
- você decide conscientemente quando (e como) publicar

### 8.3 Evidência de funcionamento (resultado observado)
A chamada `GET /v1/models` retornou um objeto contendo:
- `id` do modelo: `Qwen_Qwen3-8B-Q4_K_M.gguf`
- metadados (params, vocab, ctx_train, size)

Isso comprova que:
- o binário está executando,
- carregou o GGUF,
- e expõe o endpoint esperado.

---

## 9) Convivência LLM + Navegador: disciplina de recursos para operação de longa duração

O sistema foi montado para rodar “lado a lado” com browser. O risco principal nessa convivência é **VRAM**.

### 9.1 Por que o browser deve evitar GPU (na maioria dos cenários de automação)
Automação web:
- é dominada por IO, DOM, JS e latência de rede
- raramente precisa de throughput gráfico
- pode “roubar” VRAM do LLM de modo imprevisível

Portanto, para maximizar o LLM:
- browser com `--disable-gpu` (quando aplicável)
- manter contexto conservador inicialmente (ex.: 4096) para não inflar KV-cache

### 9.2 Por que “contexto enorme” é um erro estratégico no começo
Mesmo que o modelo treine em 32k, o custo operacional do contexto alto é:
- KV-cache maior => VRAM/RAM maior
- latência por token maior (atenção mais cara)
- risco de OOM/fragmentação em workloads longos

Em agentes, estabilidade e previsibilidade superam “contexto máximo” no estágio fundacional.

---

## 10) Fatos atuais (estado **observado** — sem especulação, sem próximos passos)

- O servidor executa **Pop!_OS (base Ubuntu 24.04)** com **systemd**.
- A GPU utilizada é **NVIDIA GeForce RTX 5060 Ti** com **8 GB de VRAM**.
- A RAM do host é **16 GB**.
- O modelo em produção local é **`Qwen_Qwen3-8B-Q4_K_M.gguf`** (GGUF quantizado).
- O servidor `llama-server` está operacional em **`http://127.0.0.1:8080`**.
- A rota **`GET /v1/models`** responde e lista o modelo carregado.
- Metadados reportados pelo servidor para o modelo carregado:
  - `n_params`: **8.190.735.360**
  - `size`: **5.021.827.072 bytes**
  - `n_ctx_train`: **32.768**
  - `n_vocab`: **151.936**
- O host opera com Python **3.12** e política **PEP 668**, e o tooling de download foi instalado de forma isolada (pipx).
- O compilador CUDA (`nvcc`) foi atualizado para suportar **compute_120**, e o toolkit ativo é **CUDA 12.9** em `/usr/local/cuda-12.9`.

---

## 11) Cláusulas de governança técnica (para preservar esta fundação)

1) **Não “corrigir” PEP 668 com força bruta**: evitar `--break-system-packages`. Isolar CLIs com pipx e libs com venv por projeto.  
2) **Não publicar o LLM sem segurança**: manter loopback por padrão; ao expor, usar firewall, autenticação e/ou reverse proxy.  
3) **Não sacrificar estabilidade por contexto**: contexto alto só após métricas e testes de stress.  
4) **Não permitir disputa de VRAM sem medir**: navegador GPU vs LLM deve ser decisão consciente, baseada em VRAM e métricas.  
5) **Não perder reprodutibilidade do build**: versões de CUDA, flags de arquitetura e método de build devem permanecer documentados.

---

**Fim do Documento (Revisão ampliada)**
