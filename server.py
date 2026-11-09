import flwr as fl

def get_evaluate_fn():
    def evaluate(server_round, parameters, client_instructions):
        print(f"-> Servidor finalizou agregação da rodada {server_round}.")
        return None
    return evaluate

def main():
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        min_fit_clients=2,
        min_available_clients=2,
        evaluate_fn=get_evaluate_fn(),
    )
    print("====================================================")
    print("    INICIANDO ORQUESTRADOR FLOWER CENTRAL (XAI-FL)   ")
    print("====================================================")
    fl.server.start_server(
        server_address="127.0.0.1:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )

if __name__ == "__main__":
    main()