"""Integrante 1: carga e limpeza da base da cesta básica.

Uso: python src/limpeza.py
Lê  data/raw/<arquivo>  e grava  data/processed/cesta_limpa.csv
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed/cesta_limpa.csv")


def carregar(caminho: Path) -> pd.DataFrame:
    if caminho.suffix in {".xlsx", ".xls"}:
        return pd.read_excel(caminho)
    return pd.read_csv(caminho)


def explorar(df: pd.DataFrame) -> None:
    """Primeiro contato: estrutura, tipos, nulos, duplicatas."""
    print(df.shape)
    print(df.dtypes)
    print(df.isna().sum())
    print("duplicadas:", df.duplicated().sum())
    print(df.describe(include="all"))


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    # TODO: converter coluna de data com pd.to_datetime
    # TODO: tratar valores ausentes (decidir: remover, interpolar ou manter)
    # TODO: padronizar nomes dos produtos
    return df.drop_duplicates()


if __name__ == "__main__":
    arquivos = [p for p in RAW.iterdir() if p.suffix in {".xlsx", ".xls", ".csv"}]
    if not arquivos:
        raise SystemExit("Coloque a planilha em data/raw/ primeiro.")
    df = carregar(arquivos[0])
    explorar(df)
    limpar(df).to_csv(OUT, index=False)
    print("Salvo em", OUT)
