"""Integrante 1: carga, validação e limpeza da base ICB_DADOS_2026.

Entrada: data/raw/ICB_DADOS_2026.xlsx

Saídas:
    data/processed/cesta_limpa.csv
    data/processed/cesta_mensal.csv
    data/processed/cesta_limpa_completa.csv

PPK = Preco / Quantidade.
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/ICB_DADOS_2026.xlsx"
OUT = ROOT / "data/processed"

PADRONIZA = {
    "Carne Acem": "Carne Bovina Acém",
    "Carne Bovina Acem": "Carne Bovina Acém",
    "Carne Coxão Mole": "Carne Bovina Coxão Mole",
    "Pernil": "Carne Suína Pernil",
    "Carne Pernil": "Carne Suína Pernil",
    "Farinha": "Farinha de Trigo",
    "Macarrão com Ovos": "Macarrão",
    "Pão": "Pão Francês",
}

MIN_MESES = 12
LIM_INF, LIM_SUP = 0.2, 5
TOLERANCIA_PPK = 0.025


def carregar() -> pd.DataFrame:
    df = pd.read_excel(RAW)

    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={"mes_ano_data": "mes"})

    df["mes"] = (
        pd.to_datetime(df["mes"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["data_coleta"] = pd.to_datetime(
        df["data_coleta"], errors="coerce"
    )

    df["produto"] = df["produto"].str.strip().replace(PADRONIZA)

    for coluna in ["preco", "quantidade", "ppk"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df


def limpar(df: pd.DataFrame, filtrar_historico=True) -> pd.DataFrame:
    df = df.copy()

    # Validação dos campos essenciais.
    numericos = df[["preco", "quantidade", "ppk"]]

    invalidos = (
        df["mes"].isna()
        | df["produto"].isna()
        | df["produto"].eq("")
        | df["estab"].isna()
        | (~np.isfinite(numericos)).any(axis=1)
        | (numericos <= 0).any(axis=1)
    )

    print(f"Registros inválidos: {invalidos.sum()}")
    df = df[~invalidos].copy()

    # Validação do PPK.
    diferenca = (df["ppk"] - df["preco"] / df["quantidade"]).abs()
    inconsistentes = diferenca > TOLERANCIA_PPK

    print(f"PPK inconsistentes: {inconsistentes.sum()}")
    print(f"Maior diferença no PPK: {diferenca.max():.8f}")

    df = df[~inconsistentes].copy()

    # Remoção de registros idênticos.
    n0 = len(df)
    df = df.drop_duplicates()

    print(f"Duplicatas removidas: {n0 - len(df)}")

    # Filtro de valores extremos.
    med = df.groupby("produto")["ppk"].transform("median")
    ok = df["ppk"].between(LIM_INF * med, LIM_SUP * med)

    print(f"Outliers removidos: {(~ok).sum()}")
    df = df[ok].copy()

    # Preserva todos os produtos quando solicitado.
    if not filtrar_historico:
        return df.reset_index(drop=True)

    # Mantém a compatibilidade com os demais integrantes.
    meses = df.groupby("produto")["mes"].nunique()
    fracos = meses[meses < MIN_MESES].index.tolist()

    print("Produtos com histórico curto:", fracos)

    return df[~df["produto"].isin(fracos)].reset_index(drop=True)


def mensal(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["mes", "produto"])["ppk"]
        .agg(
            ppk_mediana="median",
            ppk_media="mean",
            n_coletas="size"
        )
        .reset_index()
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    original = carregar()

    print("\n=== BASE ORIGINAL ===")
    print("Registros:", len(original))
    print("\nValores ausentes:")
    print(original.isna().sum().to_string())

    print("\n=== LIMPEZA ===")
    completa = limpar(original, filtrar_historico=False)

    # Base completa, incluindo produtos com histórico curto.
    completa.to_csv(OUT / "cesta_limpa_completa.csv", index=False)

    # Base utilizada pelos demais integrantes.
    meses = completa.groupby("produto")["mes"].nunique()
    fracos = meses[meses < MIN_MESES].index.tolist()

    df = completa[~completa["produto"].isin(fracos)].reset_index(drop=True)

    df.to_csv(OUT / "cesta_limpa.csv", index=False)

    m = mensal(df)
    m.to_csv(OUT / "cesta_mensal.csv", index=False)

    print("\n=== RESULTADO FINAL ===")
    print("Registros da base completa:", len(completa))
    print("Produtos da base completa:", completa["produto"].nunique())
    print("Produtos com histórico curto:", fracos)
    print("Registros da base filtrada:", len(df))
    print("Produtos da base filtrada:", df["produto"].nunique())
    print("Registros mensais:", len(m))

    print("\n=== COBERTURA TEMPORAL ===")
    print(m.groupby("produto")["mes"].nunique().sort_values().to_string())