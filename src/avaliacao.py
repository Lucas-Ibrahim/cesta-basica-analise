"""Funções para avaliação dos modelos de previsão
e análise dos períodos de compra da cesta básica.
"""

import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)


MODELOS = {
    "pred_baseline": "Baseline",
    "pred_ridge": "Ridge Regression",
    "pred_rf": "Random Forest",
    "pred_hw": "Holt-Winters"
}


def calcular_metricas(df, cenario):
    """Calcula MAE e RMSE por produto e modelo."""

    resultados = []

    for produto, grupo in df.groupby("produto"):

        dados = grupo.dropna(
            subset=["ppk_mediana", *MODELOS.keys()]
        )

        if dados.empty:
            continue

        real = dados["ppk_mediana"]

        for coluna, modelo in MODELOS.items():

            previsto = dados[coluna]

            mae = mean_absolute_error(real, previsto)

            rmse = np.sqrt(
                mean_squared_error(real, previsto)
            )

            resultados.append({
                "produto": produto,
                "modelo": modelo,
                "cenario": cenario,
                "n_observacoes": len(dados),
                "MAE": mae,
                "RMSE": rmse
            })

    return pd.DataFrame(resultados)


def selecionar_melhores_modelos(metricas):
    """Seleciona o modelo com menor MAE por produto."""

    return (
        metricas
        .sort_values(
            ["produto", "cenario", "MAE", "RMSE", "modelo"]
        )
        .groupby(["produto", "cenario"])
        .head(1)
        .reset_index(drop=True)
    )


def comparar_baseline(metricas):
    """Compara os modelos com o modelo de referência."""

    baseline = (
        metricas[metricas["modelo"] == "Baseline"]
        [["produto", "cenario", "MAE", "RMSE"]]
        .rename(columns={
            "MAE": "MAE_baseline",
            "RMSE": "RMSE_baseline"
        })
    )

    comparacao = metricas.merge(
        baseline,
        on=["produto", "cenario"],
        how="left"
    )

    denominador = comparacao["MAE_baseline"].where(
        comparacao["MAE_baseline"] > 0
    )

    comparacao["melhoria_MAE_pct"] = (
        1 - comparacao["MAE"] / denominador
    ) * 100

    comparacao["superou_baseline"] = (
        comparacao["MAE"] < comparacao["MAE_baseline"]
    ).where(comparacao["MAE_baseline"].notna())

    return comparacao


def gerar_ranking(melhores_modelos):
    """Conta quantos produtos cada modelo venceu."""

    return (
        melhores_modelos
        .groupby(["cenario", "modelo"])
        .size()
        .reset_index(name="produtos_vencedores")
        .sort_values(
            ["cenario", "produtos_vencedores"],
            ascending=[True, False]
        )
        .reset_index(drop=True)
    )


def classificar_evidencia(linha):
    """Classifica oportunidades de compra.

    Critério exploratório, sem representar
    confiança estatística ou garantia de economia.
    """

    campos = [
        "MAE",
        "superou_baseline",
        "amplitude_prevista"
    ]

    if any(pd.isna(linha[campo]) for campo in campos):
        return "Dados insuficientes"

    if not linha["superou_baseline"]:
        return "Modelo não superou o Baseline"

    if linha["amplitude_prevista"] <= linha["MAE"]:
        return "Diferença pequena em relação ao erro"

    return "Indício favorável de compra"