import sys
import warnings
import re
import time
import textwrap
from collections import defaultdict

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import poisson

ELO_RATINGS = {
    "Argentina": 2082, "França": 2063, "Espanha": 2058,
    "Inglaterra": 2043, "Brasil": 2001, "Portugal": 1985,
    "Bélgica": 1954, "Países Baixos": 1948, "Alemanha": 1942,
    "Holanda": 1948, "Itália": 1918, "Croácia": 1895,
    "Marrocos": 1882, "Senegal": 1871, "Colômbia": 1865,
    "Uruguai": 1858, "México": 1840, "EUA": 1829,
    "Japão": 1821, "Equador": 1815, "Austrália": 1798,
    "Turquia": 1792, "Suíça": 1788, "Dinamarca": 1785,
    "Coreia do Sul": 1779, "Suécia": 1771, "Áustria": 1768,
    "Rep. Tcheca": 1762, "República Tcheca": 1762, "Noruega": 1759,
    "Egito": 1751, "Canadá": 1745, "Costa do Marfim": 1741,
    "Argélia": 1738, "Irã": 1731, "Escócia": 1724,
    "Polônia": 1718, "Arábia Saudita": 1712, "Paraguai": 1709,
    "Gana": 1703, "Costa Rica": 1698, "Bósnia": 1691,
    "Sérvia": 1688, "Grécia": 1682, "Venezuela": 1678,
    "Panamá": 1674, "Honduras": 1668, "Bolívia": 1661,
    "Peru": 1658, "Chile": 1652, "Uzbequistão": 1648,
    "Tunísia": 1641, "Camarões": 1638, "Nigéria": 1635,
    "Mali": 1628, "Burkina Faso": 1621, "RD Congo": 1589,
    "Cabo Verde": 1572, "Haiti": 1548,
    "Catar": 1512, "Curaçao": 1521, "Jordânia": 1498,
    "Iraque": 1491, "Nova Zelândia": 1487, "África do Sul": 1467,
    "Rep. Dominicana": 1340, "Guatemala": 1352, "El Salvador": 1358,
    "Jamaica": 1401, "Trinidad e Tobago": 1380,
}

COPA_2026_GRUPOS = {
    "A": ["México", "África do Sul", "Coreia do Sul", "Rep. Tcheca"],
    "B": ["Canadá", "Bósnia", "Catar", "Suíça"],
    "C": ["Brasil", "Marrocos", "Haiti", "Escócia"],
    "D": ["EUA", "Paraguai", "Austrália", "Turquia"],
    "E": ["Alemanha", "Curaçao", "Costa do Marfim", "Equador"],
    "F": ["Holanda", "Japão", "Suécia", "Tunísia"],
    "G": ["Bélgica", "Egito", "Irã", "Nova Zelândia"],
    "H": ["Espanha", "Cabo Verde", "Arábia Saudita", "Uruguai"],
    "I": ["França", "Senegal", "Iraque", "Noruega"],
    "J": ["Argentina", "Argélia", "Áustria", "Jordânia"],
    "K": ["Portugal", "Uzbequistão", "Colômbia", "RD Congo"],
    "L": ["Inglaterra", "Croácia", "Gana", "Panamá"],
}

VENUES_ALTITUDE = {
    "Azteca (Cidade do México)": 2240, "Guadalajara": 1566,
    "Monterrey": 538, "Dallas": 170, "Los Angeles": 84,
    "Seattle": 54, "Vancouver": 0, "Toronto": 76,
    "Nova Jersey": 2, "Boston": 6, "Houston": 14,
    "Kansas City": 320, "Miami": 4, "Filadélfia": 12,
    "Atlanta": 285, "San Jose": 2, "San Francisco": 2,
    "default": 0,
}

VENUE_MAP = {
    "A1": "Azteca (Cidade do México)", "A2": "Guadalajara",
    "B1": "Toronto", "B2": "San Jose",
    "C1": "Nova Jersey", "C2": "Boston",
    "D1": "Los Angeles", "D2": "Vancouver",
    "E1": "Houston", "E2": "Filadélfia",
    "F1": "Dallas", "F2": "Monterrey",
    "G1": "Seattle", "G2": "Los Angeles",
    "H1": "Atlanta", "H2": "Miami",
    "I1": "Nova Jersey", "I2": "Boston",
    "J1": "Kansas City", "J2": "San Francisco",
    "K1": "Houston", "K2": "Azteca (Cidade do México)",
    "L1": "Dallas", "L2": "Toronto",
}

TEAM_ADJUSTMENTS = {
    "Argentina":      {"attack": 1.20, "defense": 0.80},
    "França":         {"attack": 1.18, "defense": 0.82},
    "Espanha":        {"attack": 1.15, "defense": 0.83},
    "Inglaterra":     {"attack": 1.13, "defense": 0.84},
    "Brasil":         {"attack": 1.10, "defense": 0.85},
    "Portugal":       {"attack": 1.12, "defense": 0.85},
    "Alemanha":       {"attack": 1.14, "defense": 0.84},
    "Países Baixos":  {"attack": 1.10, "defense": 0.87},
    "Holanda":        {"attack": 1.10, "defense": 0.87},
    "Bélgica":        {"attack": 1.07, "defense": 0.88},
    "Marrocos":       {"attack": 0.93, "defense": 0.80},
    "Senegal":        {"attack": 0.98, "defense": 0.87},
    "Japão":          {"attack": 0.98, "defense": 0.85},
    "Croácia":        {"attack": 0.98, "defense": 0.86},
    "Noruega":        {"attack": 1.08, "defense": 0.90},
    "México":         {"attack": 0.98, "defense": 0.88},
    "Colômbia":       {"attack": 1.02, "defense": 0.90},
    "Equador":        {"attack": 0.94, "defense": 0.83},
    "Suíça":          {"attack": 0.92, "defense": 0.82},
    "Uruguai":        {"attack": 0.90, "defense": 0.85},
    "EUA":            {"attack": 0.96, "defense": 0.92},
    "Austrália":      {"attack": 0.91, "defense": 0.93},
    "Turquia":        {"attack": 1.00, "defense": 0.91},
    "Áustria":        {"attack": 0.98, "defense": 0.90},
    "Suécia":         {"attack": 1.05, "defense": 0.92},
    "Coreia do Sul":  {"attack": 0.95, "defense": 0.91},
    "Escócia":        {"attack": 0.93, "defense": 0.90},
    "Egito":          {"attack": 0.97, "defense": 0.88},
    "Irã":            {"attack": 0.86, "defense": 0.87},
    "Costa do Marfim":{"attack": 0.99, "defense": 0.92},
    "Canadá":         {"attack": 0.97, "defense": 0.93},
    "Bósnia":         {"attack": 0.92, "defense": 0.93},
    "Paraguai":       {"attack": 0.87, "defense": 0.90},
    "Gana":           {"attack": 0.93, "defense": 0.94},
    "Argélia":        {"attack": 0.88, "defense": 0.93},
    "África do Sul":  {"attack": 0.80, "defense": 0.98},
    "Rep. Tcheca":    {"attack": 0.91, "defense": 0.92},
    "Arábia Saudita": {"attack": 0.82, "defense": 0.98},
    "Cabo Verde":     {"attack": 0.72, "defense": 1.10},
    "Haiti":          {"attack": 0.68, "defense": 1.15},
    "Panamá":         {"attack": 0.78, "defense": 1.05},
    "Uzbequistão":    {"attack": 0.75, "defense": 0.96},
    "RD Congo":       {"attack": 0.79, "defense": 0.97},
    "Tunísia":        {"attack": 0.80, "defense": 0.96},
    "Nova Zelândia":  {"attack": 0.72, "defense": 1.08},
    "Jordânia":       {"attack": 0.68, "defense": 1.15},
    "Iraque":         {"attack": 0.71, "defense": 1.10},
    "Curaçao":        {"attack": 0.62, "defense": 1.18},
    "Catar":          {"attack": 0.73, "defense": 1.08},
}

INJURY_ADJUSTMENTS_2026 = {
    "Brasil":   {"attack_penalty": 0.88, "notes": "Militão, Rodrygo, Estêvão fora"},
    "Paraguai": {"attack_penalty": 0.92, "notes": "Enciso fora na 1ª rodada"},
    "Japão":    {"attack_penalty": 0.90, "notes": "Mitoma fora (lesão)"},
    "Bélgica":  {"attack_penalty": 0.92, "defense_penalty": 0.94, "notes": "De Bruyne e Lukaku com lesões recentes"},
    "Gana":     {"attack_penalty": 0.88, "notes": "Kudus fora (lesão na coxa)"},
    "Suécia":   {"attack_penalty": 0.93, "notes": "Isak voltando de fratura na perna"},
}

WC_AVG_GOALS = 1.20
COPA_PRESSURE = 0.94

TEAM_ALIASES = {
    "holanda": "Holanda", "netherlands": "Holanda", "países baixos": "Holanda",
    "paises baixos": "Holanda", "holland": "Holanda",
    "eua": "EUA", "estados unidos": "EUA", "usa": "EUA", "united states": "EUA",
    "rep. tcheca": "Rep. Tcheca", "republica tcheca": "Rep. Tcheca",
    "república tcheca": "Rep. Tcheca", "czech republic": "Rep. Tcheca",
    "tchéquia": "Rep. Tcheca", "tchequia": "Rep. Tcheca",
    "rd congo": "RD Congo", "rdc": "RD Congo", "congo": "RD Congo",
    "bosnia": "Bósnia", "bósnia e herzegovina": "Bósnia",
    "costa do marfim": "Costa do Marfim", "marfim": "Costa do Marfim",
    "africa do sul": "África do Sul", "south africa": "África do Sul",
    "arabia saudita": "Arábia Saudita", "saudi arabia": "Arábia Saudita",
    "franca": "França", "france": "França",
    "alemanha": "Alemanha", "germany": "Alemanha",
    "belgica": "Bélgica", "belgium": "Bélgica",
    "espanha": "Espanha", "spain": "Espanha",
    "brasil": "Brasil", "brazil": "Brasil",
    "mexico": "México", "coreia do sul": "Coreia do Sul",
    "south korea": "Coreia do Sul", "uzbequistao": "Uzbequistão",
    "uzbequistão": "Uzbequistão", "uzbekistan": "Uzbequistão",
    "ira": "Irã", "iran": "Irã",
    "austria": "Áustria",
    "argentina": "Argentina", "inglaterra": "Inglaterra",
    "portugal": "Portugal", "noruega": "Noruega",
    "suecia": "Suécia", "suécia": "Suécia",
    "suica": "Suíça", "suíça": "Suíça",
    "uruguai": "Uruguai", "turquia": "Turquia",
    "canada": "Canadá", "japao": "Japão", "japão": "Japão",
    "escocia": "Escócia", "croacia": "Croácia", "croácia": "Croácia",
    "senegal": "Senegal", "colombia": "Colômbia", "colômbia": "Colômbia",
    "equador": "Equador", "paraguai": "Paraguai", "gana": "Gana",
    "nigeria": "Nigéria", "tunisia": "Tunísia", "egito": "Egito",
    "marrocos": "Marrocos", "haiti": "Haiti",
}


def get_elo(team):
    for key in ELO_RATINGS:
        if key.lower() == team.lower():
            return ELO_RATINGS[key]
    return 1600


def get_team_adj(team):
    for key in TEAM_ADJUSTMENTS:
        if key.lower() == team.lower():
            return TEAM_ADJUSTMENTS[key]
    elo = get_elo(team)
    if elo >= 1900: return {"attack": 1.05, "defense": 0.90}
    if elo >= 1800: return {"attack": 0.98, "defense": 0.92}
    if elo >= 1700: return {"attack": 0.90, "defense": 0.96}
    return {"attack": 0.78, "defense": 1.05}


def get_injury_adj(team):
    for key in INJURY_ADJUSTMENTS_2026:
        if key.lower() == team.lower():
            return INJURY_ADJUSTMENTS_2026[key]
    return {}


def get_altitude_factor(altitude_m):
    if altitude_m < 500:  return 1.00
    if altitude_m < 1000: return 0.98
    if altitude_m < 1500: return 0.96
    if altitude_m < 2000: return 0.93
    return 0.90


def find_team_group(team):
    for grp, teams in COPA_2026_GRUPOS.items():
        for t in teams:
            if t.lower() == team.lower():
                return grp
    return "?"


def normalize_team(name):
    name = name.strip()
    alias = TEAM_ALIASES.get(name.lower())
    if alias:
        return alias, True
    for key in ELO_RATINGS:
        if key.lower() == name.lower():
            return key, True
    for key in ELO_RATINGS:
        if name.lower() in key.lower():
            return key, True
    return name.title(), False


def parse_match_line(text):
    text = text.strip()
    if not text or text.startswith("#"):
        return None

    round_num = 1
    round_match = re.search(r'[,\s]+(?:rodada\s*)?(\d)\s*$', text, re.IGNORECASE)
    if round_match:
        round_num = int(round_match.group(1))
        text = text[:round_match.start()].strip()

    sep = re.split(r'\s+[xX×vs]+\s+', text, maxsplit=1)
    if len(sep) != 2:
        return None

    team_a, ok_a = normalize_team(sep[0])
    team_b, ok_b = normalize_team(sep[1])
    return team_a, team_b, round_num, ok_a, ok_b


def calculate_lambdas(team_a, team_b, venue=None, round_num=1):
    elo_a = get_elo(team_a)
    elo_b = get_elo(team_b)
    adj_a = get_team_adj(team_a)
    adj_b = get_team_adj(team_b)

    dr_a = (elo_a - elo_b) / 400
    elo_prob_a = 1 / (1 + 10 ** (-dr_a))
    elo_prob_b = 1 - elo_prob_a

    lambda_a = WC_AVG_GOALS * adj_a["attack"] * adj_b["defense"] * (0.5 + elo_prob_a * 0.8)
    lambda_b = WC_AVG_GOALS * adj_b["attack"] * adj_a["defense"] * (0.5 + elo_prob_b * 0.8)

    altitude = 0
    if venue:
        for v_key, v_alt in VENUES_ALTITUDE.items():
            if v_key.lower() in venue.lower() or venue.lower() in v_key.lower():
                altitude = v_alt
                break

    alt_factor = get_altitude_factor(altitude)
    lambda_a *= alt_factor * COPA_PRESSURE
    lambda_b *= alt_factor * COPA_PRESSURE

    inj_a = get_injury_adj(team_a)
    inj_b = get_injury_adj(team_b)
    lambda_a *= inj_a.get("attack_penalty", 1.0)
    lambda_b *= inj_b.get("attack_penalty", 1.0)
    if "defense_penalty" in inj_a:
        lambda_b *= (1 / inj_a["defense_penalty"])
    if "defense_penalty" in inj_b:
        lambda_a *= (1 / inj_b["defense_penalty"])

    return max(0.30, lambda_a), max(0.20, lambda_b)


def dixon_coles_correction(i, j, la, lb, rho=-0.12):
    if i == 0 and j == 0: return 1 - la * lb * rho
    if i == 1 and j == 0: return 1 + lb * rho
    if i == 0 and j == 1: return 1 + la * rho
    if i == 1 and j == 1: return 1 - rho
    return 1.0


def build_score_matrix(la, lb, max_goals=8):
    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            matrix[i, j] = (
                poisson.pmf(i, la) *
                poisson.pmf(j, lb) *
                dixon_coles_correction(i, j, la, lb)
            )
    matrix /= matrix.sum()
    return matrix


def monte_carlo_simulate(la, lb, n=50_000):
    rng = np.random.default_rng(42)
    ga = rng.poisson(la, n)
    gb = rng.poisson(lb, n)

    score_counts = defaultdict(int)
    for a, b in zip(ga, gb):
        score_counts[(int(a), int(b))] += 1

    score_probs = {k: v / n for k, v in score_counts.items()}
    top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:10]

    return {
        "home_win": float(np.mean(ga > gb)),
        "draw":     float(np.mean(ga == gb)),
        "away_win": float(np.mean(ga < gb)),
        "btts":     float(np.mean((ga > 0) & (gb > 0))),
        "over_2_5": float(np.mean((ga + gb) > 2.5)),
        "over_1_5": float(np.mean((ga + gb) > 1.5)),
        "top_scores": top_scores,
        "avg_goals": float((ga + gb).mean()),
    }


def calculate_confidence(elo_a, elo_b):
    elo_diff = abs(elo_a - elo_b)
    return min(95, max(40, round(45 + elo_diff / 55)))


def predict_match(team_a, team_b, venue=None, round_num=1):
    elo_a = get_elo(team_a)
    elo_b = get_elo(team_b)

    if not venue:
        grp = find_team_group(team_a)
        venue = VENUE_MAP.get(f"{grp}{round_num}", "default")

    la, lb = calculate_lambdas(team_a, team_b, venue, round_num)
    mc = monte_carlo_simulate(la, lb)
    matrix = build_score_matrix(la, lb)

    score_probs = {}
    for i in range(9):
        for j in range(9):
            score_probs[(i, j)] = matrix[i, j]
    top3 = sorted(score_probs.items(), key=lambda x: -x[1])[:3]

    inj_a = get_injury_adj(team_a)
    inj_b = get_injury_adj(team_b)
    injury_notes = []
    if inj_a: injury_notes.append(f"{team_a}: {inj_a.get('notes', '')}")
    if inj_b: injury_notes.append(f"{team_b}: {inj_b.get('notes', '')}")

    return {
        "team_a": team_a,
        "team_b": team_b,
        "venue": venue,
        "round": round_num,
        "group": find_team_group(team_a),
        "elo_a": elo_a,
        "elo_b": elo_b,
        "elo_diff": elo_a - elo_b,
        "lambda_a": round(la, 3),
        "lambda_b": round(lb, 3),
        "prob_home_win": round(mc["home_win"] * 100, 1),
        "prob_draw":     round(mc["draw"]     * 100, 1),
        "prob_away_win": round(mc["away_win"] * 100, 1),
        "btts":          round(mc["btts"]     * 100, 1),
        "over_2_5":      round(mc["over_2_5"] * 100, 1),
        "under_2_5":     round((1 - mc["over_2_5"]) * 100, 1),
        "over_1_5":      round(mc["over_1_5"] * 100, 1),
        "top3_scores": top3,
        "most_likely": top3[0][0] if top3 else (1, 0),
        "avg_total_goals": round(mc["avg_goals"], 2),
        "confidence": calculate_confidence(elo_a, elo_b),
        "injury_notes": injury_notes,
    }
