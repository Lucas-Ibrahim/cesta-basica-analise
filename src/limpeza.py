"""Integrante 1: carga e limpeza da base ICB_DADOS_2026.

Uso (na raiz do repositório): python src/limpeza.py
Entrada : data/raw/ICB_DADOS_2026.xlsx
Saídas  : data/processed/cesta_limpa.csv   (1 linha por coleta, já limpa)
          data/processed/cesta_mensal.csv  (1 linha por produto/mês, mediana do PPK)
PPK = preço por kg (ou por unidade padrão), calculado como Preco / Quantidade.
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw/ICB_DADOS_2026.xlsx")
OUT = Path("data/processed")

# Unifica nomes diferentes do mesmo produto. Confirmar com o grupo!
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
MIN_MESES = 12          # produto com menos meses de dados é descartado da série mensal
LIM_INF, LIM_SUP = 0.2, 5  # outlier: PPK fora de [0,2x ; 5x] da mediana do produto


def carregar() -> pd.DataFrame:
    df = pd.read_excel(RAW)
    df.columns = df.columns.str.lower()
    df = df.rename(columns={"mes_ano_data": "mes", "preco": "preco"})
    df["mes"] = pd.to_datetime(df["mes"]).dt.to_period("M").dt.to_timestamp()
    df["data_coleta"] = pd.to_datetime(df["data_coleta"])
    df["produto"] = df["produto"].str.strip().replace(PADRONIZA)
    return df


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.drop_duplicates()
    print(f"duplicatas removidas: {n0 - len(df)}")

    med = df.groupby("produto")["ppk"].transform("median")
    ok = df["ppk"].between(LIM_INF * med, LIM_SUP * med)
    print(f"outliers removidos: {(~ok).sum()}")
    df = df[ok]

    meses = df.groupby("produto")["mes"].nunique()
    fracos = meses[meses < MIN_MESES].index.tolist()
    print("produtos descartados (poucos meses):", fracos)
    return df[~df["produto"].isin(fracos)].reset_index(drop=True)


def mensal(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["mes", "produto"])["ppk"]
              .agg(ppk_mediana="median", ppk_media="mean", n_coletas="size")
              .reset_index())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    df = limpar(carregar())
    df.to_csv(OUT / "cesta_limpa.csv", index=False)
    m = mensal(df)
    m.to_csv(OUT / "cesta_mensal.csv", index=False)
    print(df.shape, m.shape, df["produto"].nunique(), "produtos")
    print(m.groupby("produto")["mes"].nunique().sort_values().to_string())
