# Detecção de Intrusões em IoT com Aprendizado Federado (Flower), CTGAN e XAI

Sistema de Detecção de Intrusões (IDS) descentralizado e auditável para redes de Internet das Coisas (IoT). O pipeline integra emulação adversária com **MITRE Caldera**, sensoriamento de telemetria de borda (`collector.py`), balanceamento tabular com **CTGAN**, treinamento federado sem expor dados brutos com **Flower** (`FedAvg`) e explicabilidade causal com **SHAP** e **LIME**.

---

## 🛠️ 1. Instalação e Preparação do Ambiente

Abra o terminal na pasta do projeto e configure o ambiente virtual:

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
   ```bash
   python collector.py
   ```

2. **Tráfego sob Ataque (MITRE Caldera - 2 minutos):**
   - Inicie a operação no painel web do Caldera (`http://localhost:8888`) com o perfil *Discovery*.
   - Altere no script o rótulo para `is_attack = 1` e execute:
   ```bash
   python collector.py
   ```

---

## 🚀 3. Como Rodar o Servidor e os Clientes Juntos (1 Única Linha)

O servidor precisa escutar na porta 8080 antes de receber os clientes. Com o ambiente virtual ativado, rode a linha única do seu sistema operacional para subir o servidor e os 2 clientes simultaneamente sem travar o terminal:

### No Windows (PowerShell):
```powershell
Start-Process python -ArgumentList "server.py"; Start-Sleep -Seconds 2; Start-Process python -ArgumentList "client.py"; Start-Process python -ArgumentList "client.py"
```

### No Linux / WSL / macOS:
```bash
python server.py & sleep 2 && python client.py & python client.py & wait
```

---

## 🔍 4. O que Acontece Durante a Execução e XAI

Assim que os 2 clientes se conectam:

1. **Treinamento Federado:** O servidor executa 3 rodadas de agregação via `FedAvg`. Os clientes treinam seus classificadores locais (`SGDClassifier`), usando CTGAN caso as anomalias representem menos de 15% dos dados, e transmitem apenas os pesos (`coef_` e `intercept_`) via gRPC.
2. **Convergência:** Na 3ª rodada, o modelo alcança 100% de acurácia sobre os dados de validação.
3. **Auditoria com XAI:**
   - **SHAP (`LinearExplainer`):** Exibe a importância global das variáveis, comprovando que o volume de conexões ativas (`conn_count`) tem o maior peso positivo (~43), caracterizando as varreduras do Caldera.
   - **LIME (`LimeTabularExplainer`):** Audita localmente uma amostra individual de teste sob suspeita de invasão, expondo as regras exatas que acionaram o alerta.

---

## 🛑 5. Encerramento e Limpeza

- **Parar os processos:** Pressione `Ctrl + C` no terminal.
- **Encerrar o agente do Caldera (Windows):**
  ```powershell
  Stop-Process -Name "splunkd" -Force
  ```
- **Desativar a venv:**
  ```bash
  deactivate
  ```
