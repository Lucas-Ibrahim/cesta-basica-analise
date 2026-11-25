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
# macOS ou Linux
source .venv/bin/activate
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/limpeza.py
```

Execute os comandos acima na raiz do repositório. Depois, no VS Code ou
no Jupyter, selecione o Python da `.venv` e execute todas as células de
cada notebook, nesta ordem:

1. `01_exploratoria.ipynb`
2. `02_acessibilidade.ipynb`
3. `03_sazonalidade.ipynb`
4. `04_modelos.ipynb`
5. `05_avaliacao_previsoes.ipynb`

Os notebooks ficam em `notebooks/`. Use essa pasta como diretório de
execução, pois a Parte 4 usa caminhos relativos a ela. A Parte 5 usa os
perfis sazonais da Parte 3 e as previsões da Parte 4.

## Divisão
| Integrante | Parte | Pasta/arquivo |
|---|---|---|
| 1 | Preparação e análise exploratória | `src/limpeza.py`, `notebooks/01_exploratoria.ipynb` |
| 2 | Acessibilidade | `notebooks/02_acessibilidade.ipynb` |
| 3 | Sazonalidade | `notebooks/03_sazonalidade.ipynb` |
| 4 | Modelos de previsão | `notebooks/04_modelos.ipynb` |
| 5 | Avaliação e melhores períodos | `notebooks/05_avaliacao_previsoes.ipynb` |

## Regras de colaboração
- Nunca commitar direto na `main`. Cada um trabalha na sua branch (`integrante-1`, `integrante-2`...).
- Todos leem a base de `data/processed/`, gerada pelo Integrante 1.
- Commits pequenos e com mensagem clara.
