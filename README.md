# Análise de Dados da Cesta Básica

Acessibilidade, sazonalidade e previsão de preços da cesta básica brasileira.

## Perguntas de pesquisa
1. A cesta básica está ficando menos acessível?
2. A época do ano influencia o preço dos alimentos?
3. Qual é o melhor momento para comprar cada produto?

## Estrutura
```
data/raw/        planilhas originais (não editar)
data/processed/  base limpa gerada pelo código do Integrante 1
src/             funções reutilizáveis (carga, limpeza)
notebooks/       análises de cada integrante (um por pessoa)
reports/figures/ gráficos exportados
docs/            rascunhos do relatório técnico
```

## Como rodar
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python src/limpeza.py
```

## Divisão
| Integrante | Parte | Pasta/arquivo |
|---|---|---|
| 1 | Preparação e análise exploratória | `src/limpeza.py`, `notebooks/01_exploratoria.ipynb` |
| 2 | Acessibilidade | `notebooks/02_acessibilidade.ipynb` |
| 3 | Sazonalidade | `notebooks/03_sazonalidade.ipynb` |
| 4 | Modelos de previsão | `notebooks/04_modelos.ipynb` |
| 5 | Avaliação e melhores períodos | `notebooks/05_avaliacao.ipynb` |

## Regras de colaboração
- Nunca commitar direto na `main`. Cada um trabalha na sua branch (`integrante-1`, `integrante-2`...).
- Todos leem a base de `data/processed/`, gerada pelo Integrante 1.
- Commits pequenos e com mensagem clara.
