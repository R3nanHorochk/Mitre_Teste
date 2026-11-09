import flwr as fl
import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from ctgan import CTGAN
import shap
from lime import lime_tabular
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings("ignore")

print("Carregando telemetria capturada dos nós de borda...")
try:
    df = pd.read_csv("traffic_logs.csv")
except FileNotFoundError:
    print("[AVISO] 'traffic_logs.csv' não encontrado. Gerando dados de rede automáticos...")
    np.random.seed(42)
    dummy_data = np.random.rand(120, 5)
    df = pd.DataFrame(dummy_data, columns=['packet_size', 'packet_freq', 'cpu_usage', 'mem_usage', 'conn_count'])
    df['is_attack'] = np.random.choice([0, 1], size=120, p=[0.9, 0.1])
    df.to_csv("traffic_logs.csv", index=False)

X = df.drop(columns=['is_attack'])
y = df['is_attack']

# Balanceamento com CTGAN
if (df['is_attack'].value_counts().get(1, 0)) < (len(df) * 0.15):
    print("-> Dataset desbalanceado detectado. Inicializando CTGAN para gerar ataques sintéticos...")
    ctgan = CTGAN(epochs=5)
    attacks_only = df[df['is_attack'] == 1]
    if len(attacks_only) > 0:
        ctgan.fit(attacks_only)
        synthetic_data = ctgan.sample(int(len(df[df['is_attack'] == 0]) // 2))
        df = pd.concat([df, synthetic_data], ignore_index=True)
        X = df.drop(columns=['is_attack'])
        y = df['is_attack']
        print(f"-> CTGAN concluída. Novo tamanho do dataset: {len(df)} registros.")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Normalização essencial para convergência de modelos lineares/SGD
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Inicialização do classificador linear com coeficientes reais
model = SGDClassifier(loss='log_loss', penalty='l2', max_iter=20, random_state=42)
model.fit(X_train_scaled, y_train)

class EdgeSecurityClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        # Envia pesos e bias reais para o servidor FedAvg
        return [model.coef_, model.intercept_]

    def set_parameters(self, parameters):
        # Recebe os pesos agregados globais do servidor
        model.coef_ = parameters[0]
        model.intercept_ = parameters[1]

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        model.partial_fit(X_train_scaled, y_train)
        print("-> [FLOWER] Treinamento local finalizado com logs de simulação.")
        return self.get_parameters(config={}), len(X_train_scaled), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        preds = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, preds)
        loss = 1.0 - float(accuracy)
        print(f"-> [EVALUATE] Acurácia local corrente do nó de borda: {accuracy:.4f}")
        
        print("\n====================================================")
        print("   EXPLICABILIDADE LOCAL (LIME) - AMOSTRA DE ALERTA  ")
        print("====================================================")
        explainer_lime = lime_tabular.LimeTabularExplainer(
            training_data=X_train_scaled,
            feature_names=X.columns.tolist(),
            class_names=['Normal', 'Ataque_MITRE'],
            mode='classification',
            random_state=42
        )
        exp = explainer_lime.explain_instance(
            X_test_scaled[0], 
            model.predict_proba, 
            num_features=5
        )
        for feature, weight in exp.as_list():
            print(f" -> {feature:<35} | Peso LIME: {weight:+.4f}")

        print("\n====================================================")
        print("   EXPLICABILIDADE GLOBAL (SHAP) - PESOS FEDAVG      ")
        print("====================================================")
        # LinearExplainer com masker ajustado para evitar warnings de amostragem
        masker = shap.maskers.Independent(X_train_scaled, max_samples=len(X_train_scaled))
        explainer_shap = shap.LinearExplainer(model, masker=masker)
        shap_values = explainer_shap.shap_values(X_test_scaled)
        
        # Média da magnitude marginal por atributo
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        feature_importance = pd.DataFrame({
            'Feature': X.columns,
            'Importancia_Media_SHAP': mean_abs_shap
        }).sort_values(by='Importancia_Media_SHAP', ascending=False)
        
        for _, row in feature_importance.iterrows():
            print(f" -> {row['Feature']:<20} | Impacto Médio SHAP: {row['Importancia_Media_SHAP']:.4f}")
        print("====================================================\n")
        
        return loss, len(X_test_scaled), {"accuracy": float(accuracy)}

if __name__ == "__main__":
    fl.client.start_client(
        server_address="127.0.0.1:8080", 
        client=EdgeSecurityClient().to_client()
    )