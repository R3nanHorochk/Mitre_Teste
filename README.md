# Detecção de Intrusões em IoT com Aprendizado Federado (Flower), CTGAN e XAI

Sistema de Detecção de Intrusões (IDS) descentralizado e auditável para redes de Internet das Coisas (IoT). O pipeline integra emulação adversária com **MITRE Caldera**, sensoriamento de telemetria de borda (`collector.py`), balanceamento tabular com **CTGAN**, treinamento federado sem expor dados brutos com **Flower** (`FedAvg`) e explicabilidade causal com **SHAP** e **LIME**.

---

## 🛠️ 1. Instalação e Preparação do Ambiente

Abra o terminal na pasta do projeto e configure o ambiente virtual inicial:

### No Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install flwr==1.7.0 scikit-learn pandas numpy psutil shap lime ctgan
```

### No Linux / WSL / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install flwr==1.7.0 scikit-learn pandas numpy psutil shap lime ctgan
```

---

## 📊 2. Coleta de Telemetria (`collector.py`)

> **Nota:** Caso o arquivo `traffic_logs.csv` já exista na pasta do projeto, pule direto para o **Passo 3**.

1. **Tráfego Normal (Baseline - 2 minutos):**
   Com a `venv` ativada:
   ```bash
   python collector.py
   ```

2. **Tráfego sob Ataque (MITRE Caldera - 2 minutos):**
   Inicie a operação no painel web do Caldera (`http://localhost:8888`) com o perfil *Discovery*, altere no script o rótulo para `is_attack = 1` e execute com a `venv` ativada:
   ```bash
   python collector.py
   ```

---

## 🚀 3. Como Rodar o Treinamento Federado (3 Terminais Separados)

**Importante:** Todo terminal novo abre sem o ambiente virtual ativo por padrão. Portanto, **você precisa ativar a `venv` em cada um dos 3 terminais** antes de rodar os scripts.

O servidor precisa estar em escuta na porta `8080` antes da conexão dos clientes. Abra **3 janelas de terminal** e execute exatamente os passos abaixo:

---

### Terminal 1: Servidor Central (Flower)

1. Ative a `venv`:
   * **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   * **Linux / WSL / macOS:** `source venv/bin/activate`
2. Inicie o servidor central:
   ```bash
   python server.py
   ```
   *(Aguarde a mensagem indicando que o servidor está ouvindo na porta `8080`).*

---

### Terminal 2: Cliente 1 (Nó de Borda)

1. Abra uma nova janela e navegue até a pasta do projeto.
2. Ative a `venv`:
   * **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   * **Linux / WSL / macOS:** `source venv/bin/activate`
3. Inicie o primeiro cliente:
   ```bash
   python client.py
   ```

---

### Terminal 3: Cliente 2 (Nó de Borda)

1. Abra uma terceira janela e navegue até a pasta do projeto.
2. Ative a `venv`:
   * **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   * **Linux / WSL / macOS:** `source venv/bin/activate`
3. Inicie o segundo cliente:
   ```bash
   python client.py
   ```

---

## 🔍 4. O que Acontece Durante a Execução e XAI

Assim que o segundo cliente se conecta ao servidor:

1. **Treinamento Federado:** O servidor executa 3 rodadas de agregação via `FedAvg`. Os clientes treinam seus classificadores locais (`SGDClassifier`), usando **CTGAN** caso as anomalias representem menos de 15% dos dados, e transmitem apenas os pesos (`coef_` e `intercept_`) via gRPC.
2. **Convergência:** Na 3ª rodada, o modelo alcança 100% de acurácia sobre os dados de validação.
3. **Auditoria com XAI:**
   - **SHAP (`LinearExplainer`):** Exibe a importância global das variáveis, comprovando que o volume de conexões ativas (`conn_count`) tem o maior peso positivo (~43), caracterizando as varreduras do Caldera.
   - **LIME (`LimeTabularExplainer`):** Audita localmente uma amostra individual de teste sob suspeita de invasão, expondo as regras exatas que acionaram o alerta.

---

## 🛑 5. Encerramento e Limpeza

- **Parar os processos:** Pressione `Ctrl + C` em cada terminal aberto.
- **Encerrar o agente do Caldera (Windows):**
  ```powershell
  Stop-Process -Name "splunkd" -Force
  ```
- **Desativar a venv:**
  ```bash
  deactivate
  ```

