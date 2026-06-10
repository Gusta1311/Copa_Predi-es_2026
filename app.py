import streamlit as st
import time
import pandas as pd
from predictor_core_v3 import (
    predict_match, parse_match_line, ELO_RATINGS
)

st.set_page_config(
    page_title="Copa do Mundo 2026 — Previsões",
    page_icon="🏆",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .match-header { font-size: 1.4rem; font-weight: 700; text-align: center; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("🏆 Copa do Mundo 2026 — Previsões Estatísticas")
st.caption("Elo Rating + Dixon-Coles + Monte Carlo 50k simulações")

st.divider()

ALL_TEAMS = sorted(ELO_RATINGS.keys())
ROUNDS    = [1, 2, 3, "Oitavas", "Quartas", "Semi", "Final"]
MODES     = ["✏️ Seleção manual", "📝 Texto livre"]

mode = st.radio("Modo de entrada", MODES, horizontal=True)
st.divider()

games_to_predict = []
warnings_list    = []

if mode == MODES[0]:
    st.subheader("Adicionar jogos")
    if "game_list" not in st.session_state:
        st.session_state.game_list = []

    c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
    with c1: team_a = st.selectbox("Time A", ALL_TEAMS, key="sel_a")
    with c2: team_b = st.selectbox("Time B", ALL_TEAMS, index=1, key="sel_b")
    with c3: rnd    = st.selectbox("Rodada", ROUNDS, key="sel_rnd")
    with c4:
        st.write(""); st.write("")
        if st.button("➕ Adicionar"):
            if team_a == team_b:
                st.error("Times iguais.")
            else:
                rnd_val = rnd if isinstance(rnd, int) else 1
                st.session_state.game_list.append((team_a, team_b, rnd_val, str(rnd)))
                st.rerun()

    if st.session_state.game_list:
        st.write(f"**{len(st.session_state.game_list)} jogo(s) na fila:**")
        for i, (a, b, r, rl) in enumerate(st.session_state.game_list):
            ca, cb = st.columns([6, 1])
            ca.write(f"{i+1}. {a} x {b} — {rl}")
            if cb.button("🗑", key=f"del_{i}"):
                st.session_state.game_list.pop(i)
                st.rerun()
        if st.button("🗑 Limpar todos"):
            st.session_state.game_list = []
            st.rerun()

    games_to_predict = [(a, b, r) for a, b, r, _ in st.session_state.game_list]

else:
    st.subheader("Cole os jogos")
    st.caption("Formato: `Time A x Time B, Rodada N`  |  Linhas com # são ignoradas")
    exemplo = (
        "# Grupo C\n"
        "Brasil x Marrocos, 1\n"
        "Haiti x Escócia, 1\n\n"
        "# Grupo I\n"
        "França x Senegal, 1\n"
        "Argentina x Argélia, 1"
    )
    text_input = st.text_area("Jogos", value=exemplo, height=220)
    for line in text_input.splitlines():
        parsed = parse_match_line(line)
        if parsed:
            a, b, rnd, ok_a, ok_b = parsed
            games_to_predict.append((a, b, rnd))
            if not ok_a: warnings_list.append(f"⚠️ **{a}** não encontrado — Elo padrão aplicado")
            if not ok_b: warnings_list.append(f"⚠️ **{b}** não encontrado — Elo padrão aplicado")

st.divider()

if warnings_list:
    with st.expander("⚠️ Avisos", expanded=True):
        for w in warnings_list:
            st.warning(w)

if not games_to_predict:
    st.info("Adicione pelo menos um jogo para gerar as previsões.")
    st.stop()

st.write(f"**{len(games_to_predict)} jogo(s) prontos**")

if st.button("🔮 Gerar Previsões", type="primary", use_container_width=True):
    t0 = time.time()
    results  = []
    progress = st.progress(0, text="Calculando...")

    for i, (a, b, rnd) in enumerate(games_to_predict):
        res = predict_match(a, b, round_num=rnd, use_api=False)
        results.append(res)
        progress.progress(
            (i + 1) / len(games_to_predict),
            text=f"{i+1}/{len(games_to_predict)} — {a} x {b}"
        )

    elapsed = time.time() - t0
    progress.empty()
    st.success(f"✅ {len(results)} jogo(s) em {elapsed:.2f}s")
    st.divider()

    medals = ["🥇", "🥈", "🥉"]

    for res in results:
        st.markdown(
            f"<div class='match-header'>⚽ {res['team_a']}  x  {res['team_b']}</div>",
            unsafe_allow_html=True
        )
        st.caption(f"Grupo {res['group']}  •  Rodada {res['round']}  •  {res['venue']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Elo {res['team_a']}", res["elo_a"])
        c2.metric(f"Elo {res['team_b']}", res["elo_b"])
        c3.metric(f"xG {res['team_a']}", res["lambda_a"])
        c4.metric(f"xG {res['team_b']}", res["lambda_b"])

        st.write("**Probabilidades**")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.write(f"🟢 Vitória {res['team_a']}")
            st.progress(res["prob_home_win"] / 100)
            st.write(f"**{res['prob_home_win']}%**")
        with pc2:
            st.write("🟡 Empate")
            st.progress(res["prob_draw"] / 100)
            st.write(f"**{res['prob_draw']}%**")
        with pc3:
            st.write(f"🔴 Vitória {res['team_b']}")
            st.progress(res["prob_away_win"] / 100)
            st.write(f"**{res['prob_away_win']}%**")

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Ambos Marcam", f"{res['btts']}%")
        mc2.metric("Over 2.5",     f"{res['over_2_5']}%")
        mc3.metric("Under 2.5",    f"{res['under_2_5']}%")
        mc4.metric("Over 1.5",     f"{res['over_1_5']}%")

        sc1, sc2, sc3 = st.columns(3)
        for idx, ((ga, gb), prob) in enumerate(res["top3_scores"]):
            [sc1, sc2, sc3][idx].metric(
                f"{medals[idx]} {ga}x{gb}", f"{prob*100:.1f}%"
            )

        conf = res["confidence"]
        st.write(f"**Confiança:** {conf}/100")
        st.progress(conf / 100)

        for note in res.get("injury_notes", []):
            st.warning(f"⚠️ {note}")

        st.divider()

    st.subheader("📊 Tabela Resumo")
    rows = [{
        "Jogo":          f"{r['team_a']} x {r['team_b']}",
        "Grupo":         r["group"],
        "Rodada":        r["round"],
        "Vitória A (%)": r["prob_home_win"],
        "Empate (%)":    r["prob_draw"],
        "Vitória B (%)": r["prob_away_win"],
        "Placar":        f"{r['most_likely'][0]}x{r['most_likely'][1]}",
        "xG A":          r["lambda_a"],
        "xG B":          r["lambda_b"],
        "Confiança":     r["confidence"],
    } for r in results]

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="previsoes_copa2026.csv",
        mime="text/csv"
    )

with st.sidebar:
    st.header("ℹ️ Sobre")
    st.markdown("""
**Metodologia:**
- Elo Rating
- Dixon-Coles
- Monte Carlo 50k simulações
- Ajustes táticos por seleção
- Altitude das 16 sedes
- Lesões e desfalques da Copa 2026

**Dados calibrados manualmente**
com base em informações de junho 2026.

---
**Criado por:** Gustavo Carvalho
    """)
    st.header("📋 Times")
    st.write(", ".join(sorted(ELO_RATINGS.keys())))
