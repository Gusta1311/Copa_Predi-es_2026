# 🏆 Copa do Mundo 2026 — Gerador de Previsões Estatísticas

Modelo estatístico para previsão de resultados da Copa do Mundo 2026 com interface web interativa.

---

## O que o modelo faz

Para cada jogo informado, o sistema calcula:

- **Probabilidades** de vitória do time A, empate e vitória do time B
- **Gols esperados** (xG) para cada seleção
- **Mercados de apostas**: Ambos marcam, Over/Under 2.5 e 1.5 gols
- **Top 3 placares** mais prováveis com porcentagem de ocorrência
- **Grau de confiança** de 0 a 100 com base na diferença de nível entre as equipes
- **Avisos de lesões** mapeados para a Copa 2026

---

## Metodologia

O modelo combina quatro camadas de análise:

### 1. Elo Rating
Sistema de ranking dinâmico adaptado para seleções nacionais (baseado em eloratings.net). A diferença de Elo entre as equipes define a probabilidade base de cada resultado.

### 2. Dixon-Coles
Extensão do modelo de Poisson que corrige a subestimação de placares baixos (0x0, 1x0, 0x1, 1x1), que são mais comuns no futebol do que o Poisson simples prevê.

### 3. Monte Carlo
Cada jogo é simulado 50.000 vezes usando distribuições de Poisson com os gols esperados calculados. O resultado é a distribuição real de todos os placares possíveis.

### 4. Ajustes específicos
- **Força tática**: coeficientes de ataque e defesa calibrados por seleção
- **Altitude das sedes**: ajuste para as 16 cidades-sede da Copa 2026 (o Azteca fica a 2.240m)
- **Fator pressão de Copa**: jogos de torneio oficial têm menos gols que amistosos
- **Lesões e suspensões**: penalidades aplicadas sobre os lambdas com base nos dados levantados antes da Copa

---

## Modos de entrada

### Seleção manual
Escolhe os times e a rodada por menus dropdown. Ideal para analisar jogos específicos.

### Texto livre
Cola uma lista de jogos no formato `Time A x Time B, Rodada N`. Suporta múltiplos jogos de uma vez, linhas de comentário com `#` e detecção automática de apelidos comuns dos times.

---

## Times disponíveis

Todos os 48 participantes da Copa do Mundo 2026, incluindo:

Argentina, França, Espanha, Inglaterra, Brasil, Portugal, Bélgica, Holanda, Alemanha, Itália, Croácia, Marrocos, Senegal, Colômbia, Uruguai, México, EUA, Japão, Equador, Austrália, Turquia, Suíça, Coreia do Sul, Suécia, Áustria, Rep. Tcheca, Noruega, Egito, Canadá, Costa do Marfim, Argélia, Irã, Escócia, Arábia Saudita, Paraguai, Gana, Bósnia, Panamá, Uzbequistão, RD Congo, Tunísia, Nova Zelândia, Jordânia, Iraque, Curaçao, Catar, Cabo Verde, Haiti, África do Sul.

---

## Como rodar localmente

**Pré-requisito:** Python 3.9 ou superior instalado.

```bash
# 1. Clone ou baixe os arquivos para uma pasta
# 2. Instale as dependências (só na primeira vez)
pip install -r requirements.txt

# 3. Rode o app
streamlit run app.py
```

O navegador abre automaticamente em `http://localhost:8501`.

---

## Arquivos do projeto

```
copa2026/
├── app.py              # Interface Streamlit (web)
├── predictor_core.py   # Modelo estatístico
├── requirements.txt    # Dependências Python
└── README.md           # Este arquivo
```

---

## Deploy no Streamlit Cloud (grátis)

1. Suba os arquivos para um repositório público no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório e selecione `app.py` como arquivo principal
4. Clique em **Deploy** — pronto, você terá uma URL pública para compartilhar

---

## Limitações

- Os Elo Ratings são estimativas baseadas em junho de 2026 e podem variar
- Lesões e suspensões foram mapeadas manualmente — atualize o `predictor_core.py` conforme novas informações surgirem
- Futebol tem alta variância: mesmo um modelo calibrado erra ~35-40% dos resultados
- O modelo não leva em conta dados de xG históricos reais por falta de API aberta — usa coeficientes calibrados manualmente

---

## Créditos

Desenvolvido por **Gustavo Carvalho**.

Dados de referência: eloratings.net, ranking FIFA junho 2026, pesquisa pública de elencos e lesões.
