"""Integrante 3: análise reproduzível, sem modificar dados ou entregas anteriores.

Execute na raiz: python src/sazonalidade.py
Saídas exclusivas: reports/sazonalidade/ e reports/figures/sazonalidade/.
"""
from pathlib import Path
import hashlib
import json
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/cesta_mensal.csv"
OUT = ROOT / "reports/sazonalidade"
FIG = ROOT / "reports/figures/sazonalidade"
MESES = np.array(["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"])


def carregar():
    df = pd.read_csv(INPUT, parse_dates=["mes"])
    required = ["mes", "produto", "ppk_mediana", "n_coletas"]
    if df[required].isna().any().any() or df.duplicated(["produto", "mes"]).any():
        raise ValueError("Base contém ausências ou produto/mês duplicado.")
    if not np.isfinite(df.ppk_mediana).all() or (df.ppk_mediana <= 0).any():
        raise ValueError("Preços devem ser positivos e finitos.")
    if (df.n_coletas <= 0).any() or (df.mes.dt.day != 1).any():
        raise ValueError("Datas ou contagens inválidas.")
    return df.sort_values(["produto", "mes"]).reset_index(drop=True)


def ajustar(y, meses, quadratica=False, lags=3):
    """Ciclo anual harmônico em log-preços; tendência e covariância HAC."""
    t = np.linspace(-1, 1, len(y))
    x = pd.DataFrame({"const": 1., "t": t,
                      "sin": np.sin(2 * np.pi * (meses - 1) / 12),
                      "cos": np.cos(2 * np.pi * (meses - 1) / 12)})
    if quadratica:
        x["t2"] = t ** 2
    fit = sm.OLS(np.asarray(y), x).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": True})
    r = np.zeros((2, x.shape[1]))
    r[0, 2], r[1, 3] = 1, 1
    p = float(fit.wald_test(r, scalar=True, use_f=False).pvalue)
    return fit, p


def salvar_fig(fig, nome):
    fig.tight_layout()
    fig.savefig(FIG / nome, dpi=160, bbox_inches="tight")
    plt.close(fig)


def analisar(df):
    cobertura, resultados, perfis, componentes = [], [], [], []
    for produto, g in df.groupby("produto", sort=True):
        g = g.sort_values("mes")
        calendario = pd.date_range(g.mes.min(), g.mes.max(), freq="MS")
        faltantes = len(calendario) - len(g)
        elegivel = len(g) >= 36 and faltantes == 0
        cobertura.append(dict(produto=produto, inicio=g.mes.min(), fim=g.mes.max(),
                              n_meses=len(g), meses_ausentes=faltantes,
                              minimo_repeticoes_mes=int(g.groupby(g.mes.dt.month).size().min()),
                              min_coletas=int(g.n_coletas.min()), max_coletas=int(g.n_coletas.max()),
                              elegivel=elegivel))
        if not elegivel:
            continue
        y = np.log(g.ppk_mediana.to_numpy())
        meses = g.mes.dt.month.to_numpy()
        fit, p = ajustar(y, meses)
        _, p_quad = ajustar(y, meses, quadratica=True)
        _, p_lag = ajustar(y, meses, lags=6)
        angle = 2 * np.pi * np.arange(12) / 12
        seasonal = fit.params["sin"] * np.sin(angle) + fit.params["cos"] * np.cos(angle)
        stl = STL(y, period=12, seasonal=13, robust=True).fit()
        den = np.var(stl.seasonal + stl.resid)
        strength = max(0., 1 - np.var(stl.resid) / den) if den > 0 else 0.
        lb = float(acorr_ljungbox(fit.resid, lags=[12], return_df=True).lb_pvalue.iloc[0])
        resultados.append(dict(produto=produto, n_meses=len(g), p_hac3=p,
                               p_tendencia_quadratica=p_quad, p_hac6=p_lag,
                               mes_menor=MESES[seasonal.argmin()], mes_maior=MESES[seasonal.argmax()],
                               amplitude_pico_vale_pct=100 * np.expm1(seasonal.max() - seasonal.min()),
                               forca_stl=strength, r2=fit.rsquared, p_ljungbox12=lb))
        for m in range(1, 13):
            values = g.loc[g.mes.dt.month == m, "ppk_mediana"]
            perfis.append(dict(produto=produto, mes_num=m, mes=MESES[m-1], n_anos=len(values),
                               media_nominal=values.mean(), mediana_nominal=values.median(),
                               indice_harmonico=100 * np.exp(seasonal[m-1]),
                               efeito_stl_pct=100 * np.expm1(stl.seasonal[meses == m].mean())))
        componentes.append(pd.DataFrame(dict(produto=produto, mes=g.mes.to_numpy(),
                                            preco=g.ppk_mediana.to_numpy(), tendencia=np.exp(stl.trend),
                                            sazonal_pct=100*np.expm1(stl.seasonal), residuo_log=stl.resid)))
    res = pd.DataFrame(resultados)
    for source, target in [("p_hac3", "q_bh"), ("p_tendencia_quadratica", "q_quadratica"), ("p_hac6", "q_hac6")]:
        res[target] = multipletests(res[source], method="fdr_bh")[1]
    res["evidencia_principal"] = res.q_bh < .05
    res["estavel_sensibilidade"] = res.evidencia_principal & (res.q_quadratica < .05) & (res.q_hac6 < .05)
    return pd.DataFrame(cobertura), res.sort_values("q_bh"), pd.DataFrame(perfis), pd.concat(componentes, ignore_index=True)


def graficos(df, cov, res, perfil, comp):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(10, 7))
    c = cov.sort_values("n_meses")
    ax.barh(c.produto, c.n_meses, color=np.where(c.elegivel, "#247f92", "#b9bec5"))
    ax.axvline(36, ls="--", color="#bd592c", label="Mínimo adotado: 36 meses")
    ax.set(xlabel="Meses observados", title="Cobertura: séries curtas ficam fora dos testes")
    ax.legend(); salvar_fig(fig, "01_cobertura.png")

    nomes = res.produto.tolist()
    fig, axes = plt.subplots(5, 3, figsize=(15, 15))
    for ax, nome in zip(axes.flat, nomes):
        d = comp[comp.produto == nome]
        ax.plot(d.mes, d.preco, label="Mediana mensal", lw=1.5)
        ax.plot(d.mes, d.tendencia, label="Tendência STL", color="#be592c", lw=2)
        ax.set_title(nome); ax.set_ylabel("R$/unidade padrão"); ax.tick_params(axis="x", rotation=35)
    for ax in list(axes.flat)[len(nomes):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("Evolução dos preços e tendência — escalas próprias por produto", y=1.005)
    salvar_fig(fig, "02_evolucao_tendencia.png")

    mat = perfil.pivot(index="produto", columns="mes_num", values="indice_harmonico").reindex(nomes) - 100
    fig, ax = plt.subplots(figsize=(13, 9))
    limite = max(abs(mat.to_numpy()).max(), 1)
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-limite, vmax=limite, aspect="auto")
    ax.set_xticks(range(12), MESES)
    labels = [n + (" *" if bool(res.set_index("produto").loc[n, "evidencia_principal"]) else "") for n in nomes]
    ax.set_yticks(range(len(nomes)), labels)
    for i in range(len(nomes)):
        for j in range(12):
            ax.text(j, i, f"{mat.iloc[i,j]:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(mat.iloc[i,j]) > limite * .6 else "black")
    ax.set_title("Efeito anual estimado após tendência linear (%)\n* q < 0,05; demais perfis são exploratórios")
    fig.colorbar(im, ax=ax, label="Desvio relativo ao nível sem ciclo anual (%)")
    salvar_fig(fig, "03_calendario_sazonal.png")

    fig, ax = plt.subplots(figsize=(10, 7))
    r = res.sort_values("amplitude_pico_vale_pct")
    ax.barh(r.produto, r.amplitude_pico_vale_pct, color=np.where(r.evidencia_principal, "#247f92", "#b9bec5"))
    ax.set(xlabel="Diferença estimada entre pico e vale (%)", title="Amplitude do ciclo anual ajustado\nAzul: q < 0,05; cinza: evidência insuficiente")
    salvar_fig(fig, "04_amplitudes.png")

    selecionados = res.head(4).produto.tolist()
    fig, axes = plt.subplots(len(selecionados), 3, figsize=(15, 3 * len(selecionados)))
    for row, nome in enumerate(selecionados):
        d = comp[comp.produto == nome]
        for col, (key, label) in enumerate([("tendencia", "Tendência (R$/unidade)"), ("sazonal_pct", "Componente sazonal (%)"), ("residuo_log", "Resíduo (log)")]):
            axes[row,col].plot(d.mes, d[key]); axes[row,col].set_title(f"{nome} — {label}")
            axes[row,col].tick_params(axis="x", rotation=35)
    salvar_fig(fig, "05_decomposicao_stl.png")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, nome in zip(axes.flat, selecionados):
        g = df[df.produto == nome].copy()
        g["ciclo"] = g.mes.dt.year - (g.mes.dt.month < 9).astype(int)
        for ciclo, bloco in g.groupby("ciclo"):
            idx = bloco.ppk_mediana / np.exp(np.log(bloco.ppk_mediana).mean()) * 100
            posicao = (bloco.mes.dt.month - 9) % 12
            ax.plot(posicao, idx, marker=".", label=f"Set/{ciclo}–Ago/{ciclo+1}")
        ax.set_title(nome)
        ax.set_xticks(range(12), np.roll(MESES, -8), rotation=45)
        ax.set_ylabel("Índice: média geométrica do ciclo = 100")
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("Repetição entre ciclos — normalização não remove tendência dentro do ciclo", y=1.02)
    salvar_fig(fig, "06_comparacao_ciclos.png")


def tabela_md(df):
    """Markdown sem dependência adicional de tabulate."""
    rows = ["| " + " | ".join(map(str, df.columns)) + " |", "| " + " | ".join(["---"] * len(df.columns)) + " |"]
    rows += ["| " + " | ".join(map(str, row)) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join(rows)


def relatorio(df, cov, res):
    sig = res[res.evidencia_principal]
    robustos = res[res.estavel_sensibilidade]
    t = res[["produto", "mes_menor", "mes_maior", "amplitude_pico_vale_pct", "q_bh", "estavel_sensibilidade"]].copy()
    t.amplitude_pico_vale_pct = t.amplitude_pico_vale_pct.map(lambda x: f"{x:.1f}%")
    t.q_bh = t.q_bh.map(lambda x: f"{x:.4g}")
    t.estavel_sensibilidade = t.estavel_sensibilidade.map({True: "Sim", False: "Não"})
    t.columns = ["Produto", "Vale estimado", "Pico estimado", "Pico/vale − 1", "q (BH)", "Estável nas sensibilidades"]
    achados = []
    for row in sig.itertuples():
        diagnostico = ("Há autocorrelação residual no diagnóstico (p < 0,05), exigindo cautela adicional mesmo com HAC."
                       if row.p_ljungbox12 < .05 else "O diagnóstico não rejeita ausência de autocorrelação até a defasagem 12; isso não prova independência.")
        achados.append(f"- **{row.produto}:** pico ajustado em {row.mes_maior} e vale em {row.mes_menor}, "
                       f"com diferença estimada de {row.amplitude_pico_vale_pct:.1f}% entre pico e vale. "
                       f"q principal = {row.q_bh:.4g}; q com tendência quadrática = {row.q_quadratica:.4g}; "
                       f"q com HAC(6) = {row.q_hac6:.4g}. {diagnostico}")
    proximos = res[(res.q_bh >= .05) & (res.q_bh < .10)]
    if not proximos.empty:
        achados.append("- **Resultados próximos ao limiar:** " + ", ".join(
            f"{r.produto} (q = {r.q_bh:.3f})" for r in proximos.itertuples()) +
            ". Não são classificados como evidência no teste principal, ainda que alguma especificação alternativa seja significativa.")
    diagnosticos = int((res.p_ljungbox12 < .05).sum())
    interpretacao = "\n".join(achados)
    meses_elegiveis = sorted(res.n_meses.unique())
    contagens = ", ".join(map(str, meses_elegiveis))
    texto = f"""# Análise de sazonalidade dos alimentos — Integrante 3

## Pergunta e conclusão
A época do ano influencia os preços? Nesta base, o teste do ciclo anual encontrou evidência de associação em **{len(sig)} de {len(res)} produtos elegíveis**, após correção de múltiplos testes (q < 0,05). Destes, **{len(robustos)}** mantiveram o resultado nas duas verificações de sensibilidade. A conclusão é exploratória e específica dos produtos e estabelecimentos representados na base; não demonstra causalidade nem sazonalidade de toda a cesta brasileira.

Produtos com evidência no modelo principal: {', '.join(sig.produto) or 'nenhum'}.

Produtos estáveis nas sensibilidades: {', '.join(robustos.produto) or 'nenhum'}.

## Base e cobertura
- Fonte: `data/processed/cesta_mensal.csv`, produzida na etapa anterior, sem alteração.
- Período: {df.mes.min():%m/%Y} a {df.mes.max():%m/%Y}; {len(df)} pares produto/mês; {df.produto.nunique()} produtos.
- Unidade de análise: mediana mensal do PPK (preço por kg ou unidade padrão do produto). Cada mês recebe o mesmo peso; coletas individuais não são tratadas como réplicas independentes.
- Critério definido antes dos testes: pelo menos 36 meses consecutivos, sem preenchimento de lacunas. Séries elegíveis: {len(res)}. Contagens observadas de meses por série elegível: {contagens}.
- Séries fora da inferência pelo critério de cobertura: {', '.join(cov.loc[~cov.elegivel, 'produto'])}. Seus valores permanecem nas tabelas descritivas.
- Preços nominais, sem correção por inflação. A tendência estatística não equivale a um deflator.

## Métodos
1. Auditoria de duplicatas, ausências, preços positivos, regularidade e contagens; tabelas de preços por mês do calendário e por ano. Médias anuais de 2022 e 2026 são parciais e não permitem comparação direta de anos completos.
2. Regressão por produto: `log(PPK) = constante + tendência linear + b_sen × sen(2π(mês−1)/12) + b_cos × cos(2π(mês−1)/12) + erro`. O tempo é centralizado e escalado entre −1 e 1. A hipótese nula conjunta é `b_sen = b_cos = 0`.
3. Teste Wald assintótico com covariância HAC (3 defasagens, correção de amostra). Correção Benjamini–Hochberg entre os {len(res)} produtos, com limiar q < 0,05. O ciclo harmônico testa um padrão anual suave; não cobre todo formato possível de sazonalidade.
4. Sensibilidades: tendência quadrática e HAC com 6 defasagens, cada uma com correção BH própria. “Estável” exige q < 0,05 nos três ajustes; não é prova definitiva.
5. STL robusta em log-preços, período 12 e janela sazonal 13, separa tendência, sazonalidade e resíduos. Força descritiva: `max(0, 1 − Var(resíduo)/Var(sazonal + resíduo))`. STL extrai um componente mesmo sem significância; sua força não é teste estatístico.
6. Ljung–Box dos resíduos em 12 defasagens é diagnóstico exploratório (sem correção de multiplicidade ou ajuste pelos regressores). Dependência residual reduz a confiança na inferência de amostra pequena.

## Períodos de maior e menor preço
Os meses abaixo são extremos do **ciclo ajustado**, não os extremos brutos de um ano específico. A amplitude é `100 × (exp(pico_log − vale_log) − 1)`. Os índices mensais são relativos ao nível previsto sem o componente anual. Para produtos sem q < 0,05, os meses são apenas descrições do ajuste e **não sustentam recomendação de compra**. Não foram calculados intervalos para a localização do pico; meses vizinhos podem ser indistinguíveis.

{tabela_md(t)}

## Discussão dos resultados observados
{interpretacao}

O diagnóstico Ljung–Box apresentou p < 0,05 em {diagnosticos} das {len(res)} séries. Isso indica que a regressão simples deixa dependência temporal em parte dos resíduos. Por esse motivo, os resultados são apresentados como evidência exploratória, não como confirmação definitiva. As sensibilidades ajudam a avaliar estabilidade, mas não substituem mais anos de observação ou modelos de erros temporais mais completos.

## Interpretação dos gráficos
- **01 — Cobertura:** mostra a quantidade de meses observados e distingue séries elegíveis pela cor.
- **02 — Evolução e tendência:** permite separar movimentos persistentes de oscilações de curto prazo. Escalas são próprias por produto, portanto alturas absolutas entre painéis não são comparáveis.
- **03 — Calendário sazonal:** azul representa preço abaixo do nível sem ciclo; vermelho, acima. Asterisco identifica evidência após BH. É uma estimativa suavizada, não uma média bruta.
- **04 — Amplitudes:** compara oscilações em termos percentuais. Amplitude elevada, isoladamente, não implica significância.
- **05 — STL:** exibe os quatro menores q do modelo principal, escolhidos para ilustração. Picos nos resíduos são movimentos que tendência e sazonalidade não explicam.
- **06 — Ciclos:** compara esses mesmos produtos em blocos completos setembro–agosto. Curvas divergentes indicam instabilidade entre anos; a normalização remove nível, mas não tendência dentro de cada bloco.

## Limitações e resposta à pesquisa
Há apenas quatro ciclos anuais: os testes HAC são aproximações assintóticas e podem ser instáveis em 48 observações. Tendências não lineares, choques de oferta e alterações na composição das coletas podem parecer sazonalidade. A regressão harmônica impõe um pico e um vale anuais; ausência de significância não prova ausência de outros padrões. A correção BH controla a taxa esperada de falsas descobertas sob suas condições usuais, não elimina erros individuais nem resolve toda dependência entre produtos.

A época do ano apresenta associação estatística com preços nos produtos destacados, condicionada ao modelo. Os resultados que resistem às sensibilidades são os candidatos mais consistentes para discussão. Não se pode atribuir o padrão a safra, clima ou demanda sem variáveis externas. Não se prevê preço futuro nem se garante economia em determinado mês. As séries curtas precisam de mais ciclos antes de uma conclusão sazonal confiável.

## Reprodução e entregas
Na raiz do repositório, instale as dependências de `requirements.txt` e execute `python src/sazonalidade.py`, ou execute `notebooks/03_sazonalidade.ipynb` de cima para baixo. O notebook usa o mesmo módulo para evitar divergência entre os resultados.

As saídas ficam exclusivamente em `reports/sazonalidade/` e `reports/figures/sazonalidade/`. O manifesto registra o hash da entrada, parâmetros e versões. As tabelas CSV incluem cobertura, resumo anual, resumo mensal bruto, perfis ajustados, testes e componentes STL.

## Referências dos métodos
- [STL e seus parâmetros — statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html).
- [Regressão OLS e inferência — statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html).
- [Correção de testes múltiplos — statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).
"""
    (OUT / "relatorio_sazonalidade.md").write_text(texto, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    df = carregar()
    cov, res, perfil, comp = analisar(df)
    anual = df.assign(ano=df.mes.dt.year).groupby(["produto", "ano"]).agg(
        media_ppk=("ppk_mediana", "mean"), minimo_ppk=("ppk_mediana", "min"),
        maximo_ppk=("ppk_mediana", "max"), meses_observados=("mes", "size")).reset_index()
    mensal = df.assign(mes_num=df.mes.dt.month).groupby(["produto", "mes_num"]).agg(
        media_ppk=("ppk_mediana", "mean"), mediana_ppk=("ppk_mediana", "median"),
        desvio_ppk=("ppk_mediana", "std"), n_anos=("mes", "size")).reset_index()
    for nome, tabela in [("cobertura", cov), ("testes_sazonalidade", res), ("perfis_mensais", perfil),
                         ("componentes_stl", comp), ("resumo_anual", anual), ("resumo_mensal_bruto", mensal)]:
        tabela.to_csv(OUT / f"{nome}.csv", index=False, encoding="utf-8-sig")
    graficos(df, cov, res, perfil, comp)
    relatorio(df, cov, res)
    manifesto = dict(entrada=str(INPUT.relative_to(ROOT)), sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),
                     minimo_meses=36, periodo=12, janela_stl=13, hac_principal=3, hac_sensibilidade=6,
                     alpha=.05, ajuste="fdr_bh", python=platform.python_version(),
                     pandas=pd.__version__, numpy=np.__version__, scipy=scipy.__version__,
                     statsmodels=statsmodels.__version__, matplotlib=matplotlib.__version__)
    (OUT / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(res[["produto", "q_bh", "mes_menor", "mes_maior", "estavel_sensibilidade"]].to_string(index=False))
    return cov, res, perfil, comp


if __name__ == "__main__":
    main()
