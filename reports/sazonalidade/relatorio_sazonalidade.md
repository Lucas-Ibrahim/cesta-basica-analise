# Análise de sazonalidade dos alimentos — Integrante 3

## Pergunta e conclusão
A época do ano influencia os preços? Nesta base, o teste do ciclo anual encontrou evidência de associação em **2 de 14 produtos elegíveis**, após correção de múltiplos testes (q < 0,05). Destes, **2** mantiveram o resultado nas duas verificações de sensibilidade. A conclusão é exploratória e específica dos produtos e estabelecimentos representados na base; não demonstra causalidade nem sazonalidade de toda a cesta brasileira.

Produtos com evidência no modelo principal: Tomate, Leite.

Produtos estáveis nas sensibilidades: Tomate, Leite.

## Base e cobertura
- Fonte: `data/processed/cesta_mensal.csv`, produzida na etapa anterior, sem alteração.
- Período: 09/2022 a 08/2026; 780 pares produto/mês; 20 produtos.
- Unidade de análise: mediana mensal do PPK (preço por kg ou unidade padrão do produto). Cada mês recebe o mesmo peso; coletas individuais não são tratadas como réplicas independentes.
- Critério definido antes dos testes: pelo menos 36 meses consecutivos, sem preenchimento de lacunas. As 14 séries elegíveis têm 48 meses e quatro observações de cada mês do calendário.
- Séries curtas, excluídas da inferência: Carne Bovina Acém, Carne Suína Pernil, Frango Peito, Frango Sobrecoxa, Macarrão, Ovo. Seus valores permanecem nas tabelas descritivas.
- Preços nominais, sem correção por inflação. A tendência estatística não equivale a um deflator.

## Métodos
1. Auditoria de duplicatas, ausências, preços positivos, regularidade e contagens; tabelas de preços por mês do calendário e por ano. Médias anuais de 2022 e 2026 são parciais e não permitem comparação direta de anos completos.
2. Regressão por produto: `log(PPK) = constante + tendência linear + b_sen × sen(2π(mês−1)/12) + b_cos × cos(2π(mês−1)/12) + erro`. O tempo é centralizado e escalado entre −1 e 1. A hipótese nula conjunta é `b_sen = b_cos = 0`.
3. Teste Wald assintótico com covariância HAC (3 defasagens, correção de amostra). Correção Benjamini–Hochberg entre os 14 produtos, com limiar q < 0,05. O ciclo harmônico testa um padrão anual suave; não cobre todo formato possível de sazonalidade.
4. Sensibilidades: tendência quadrática e HAC com 6 defasagens, cada uma com correção BH própria. “Estável” exige q < 0,05 nos três ajustes; não é prova definitiva.
5. STL robusta em log-preços, período 12 e janela sazonal 13, separa tendência, sazonalidade e resíduos. Força descritiva: `max(0, 1 − Var(resíduo)/Var(sazonal + resíduo))`. STL extrai um componente mesmo sem significância; sua força não é teste estatístico.
6. Ljung–Box dos resíduos em 12 defasagens é diagnóstico exploratório (sem correção de multiplicidade ou ajuste pelos regressores). Dependência residual reduz a confiança na inferência de amostra pequena.

## Períodos de maior e menor preço
Os meses abaixo são extremos do **ciclo ajustado**, não os extremos brutos de um ano específico. A amplitude é `100 × (exp(pico_log − vale_log) − 1)`. Os índices mensais são relativos ao nível previsto sem o componente anual. Para produtos sem q < 0,05, os meses são apenas descrições do ajuste e **não sustentam recomendação de compra**. Não foram calculados intervalos para a localização do pico; meses vizinhos podem ser indistinguíveis.

| Produto | Vale estimado | Pico estimado | Pico/vale − 1 | q (BH) | Estável nas sensibilidades |
| --- | --- | --- | --- | --- | --- |
| Tomate | Out | Abr | 55.2% | 0.0003631 | Sim |
| Leite | Jan | Jul | 16.8% | 0.02037 | Sim |
| Feijão | Nov | Mai | 17.7% | 0.0511 | Não |
| Banana Nanica | Mai | Nov | 16.9% | 0.07253 | Não |
| Farinha de Trigo | Mai | Nov | 3.5% | 0.09065 | Não |
| Óleo | Jul | Jan | 16.4% | 0.249 | Não |
| Banana Prata | Ago | Fev | 8.8% | 0.3227 | Não |
| Batata | Nov | Mai | 32.3% | 0.3524 | Não |
| Pão Francês | Nov | Mai | 1.5% | 0.9555 | Não |
| Café | Jul | Jan | 5.2% | 0.983 | Não |
| Açúcar | Mai | Nov | 1.6% | 0.983 | Não |
| Arroz | Ago | Fev | 3.4% | 0.983 | Não |
| Carne Bovina Coxão Mole | Jul | Jan | 3.5% | 0.983 | Não |
| Manteiga | Nov | Mai | 0.3% | 0.983 | Não |

## Discussão dos resultados observados
- **Tomate:** pico ajustado em Abr e vale em Out, com diferença estimada de 55.2% entre pico e vale. q principal = 0.0003631; q com tendência quadrática = 0.0006524; q com HAC(6) = 0.00416. O diagnóstico não rejeita ausência de autocorrelação até a defasagem 12; isso não prova independência.
- **Leite:** pico ajustado em Jul e vale em Jan, com diferença estimada de 16.8% entre pico e vale. q principal = 0.02037; q com tendência quadrática = 0.01686; q com HAC(6) = 0.03586. Há autocorrelação residual no diagnóstico (p < 0,05), exigindo cautela adicional mesmo com HAC.
- **Resultados próximos ao limiar:** Feijão (q = 0.051), Banana Nanica (q = 0.073), Farinha de Trigo (q = 0.091). Não são classificados como evidência no teste principal, ainda que alguma especificação alternativa seja significativa.

O diagnóstico Ljung–Box apresentou p < 0,05 em 12 das 14 séries. Isso indica que a regressão simples deixa dependência temporal em parte dos resíduos. Por esse motivo, os resultados são apresentados como evidência exploratória, não como confirmação definitiva. As sensibilidades ajudam a avaliar estabilidade, mas não substituem mais anos de observação ou modelos de erros temporais mais completos.

## Interpretação dos gráficos
- **01 — Cobertura:** diferencia quatro ciclos disponíveis das séries de apenas 18 meses.
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
