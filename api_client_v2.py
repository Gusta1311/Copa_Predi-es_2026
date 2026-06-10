import os
import json
import time
import hashlib
import requests
from pathlib import Path

API_BASE = "https://v3.football.api-sports.io"
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 6 * 3600

NATIONAL_TEAM_IDS = {
    "Argentina": 26, "França": 2, "Espanha": 9, "Inglaterra": 10,
    "Brasil": 6, "Portugal": 27, "Bélgica": 1, "Holanda": 8,
    "Alemanha": 25, "Itália": 3, "Croácia": 22, "Marrocos": 32,
    "Senegal": 34, "Colômbia": 56, "Uruguai": 28, "México": 16,
    "EUA": 15, "Japão": 21, "Equador": 58, "Austrália": 24,
    "Turquia": 20, "Suíça": 13, "Coreia do Sul": 48, "Suécia": 11,
    "Áustria": 19, "Rep. Tcheca": 29, "Noruega": 23, "Egito": 36,
    "Canadá": 14, "Costa do Marfim": 33, "Argélia": 31, "Irã": 44,
    "Escócia": 1178, "Arábia Saudita": 46, "Paraguai": 57, "Gana": 37,
    "Bósnia": 18, "Panamá": 89, "Uzbequistão": 121, "RD Congo": 38,
    "Tunísia": 35, "Nova Zelândia": 186, "Jordânia": 116, "Iraque": 43,
    "Curaçao": 1228, "Catar": 30, "Cabo Verde": 174, "Haiti": 93,
    "África do Sul": 39,
}

COMPETITION_WEIGHTS = {
    "FIFA World Cup":          1.00,
    "World Cup":               1.00,
    "FIFA World Cup - Group":  1.00,
    "Eliminatorias":           0.85,
    "FIFA World Cup Qualification": 0.85,
    "CONMEBOL":                0.85,
    "UEFA":                    0.85,
    "CAF":                     0.80,
    "AFC":                     0.80,
    "CONCACAF":                0.80,
    "Nations League":          0.75,
    "Copa America":            0.90,
    "Euro":                    0.90,
    "Africa Cup":              0.85,
    "Friendly":                0.50,
    "International Friendly":  0.50,
}

WORLD_CUP_2026_LEAGUE_ID = 1
WORLD_CUP_2026_LEAGUE_ID_ALT = 777


def get_api_key():
    return os.environ.get("FOOTBALL_API_KEY") or os.environ.get("RAPIDAPI_KEY")


def api_available():
    return get_api_key() is not None


def get_headers():
    key = get_api_key()
    if not key:
        return None
    return {"x-apisports-key": key}


def cache_key_path(key):
    h = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def load_cache(key):
    path = cache_key_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if time.time() - data.get("_ts", 0) > CACHE_TTL:
            return None
        return data.get("payload")
    except Exception:
        return None


def save_cache(key, payload):
    path = cache_key_path(key)
    try:
        path.write_text(json.dumps({"_ts": time.time(), "payload": payload}))
    except Exception:
        pass


def api_get(endpoint, params=None):
    cache_key = f"{endpoint}_{sorted((params or {}).items())}"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached, True

    headers = get_headers()
    if not headers:
        return None, False

    try:
        resp = requests.get(
            f"{API_BASE}/{endpoint}",
            headers=headers,
            params=params,
            timeout=12
        )
        if resp.status_code != 200:
            return None, False
        data = resp.json()
        if data.get("errors"):
            return None, False
        payload = data.get("response", [])
        save_cache(cache_key, payload)
        return payload, False
    except Exception:
        return None, False


def get_team_id(team_name):
    for key, tid in NATIONAL_TEAM_IDS.items():
        if key.lower() == team_name.lower():
            return tid
    return None


def get_competition_weight(league_name):
    if not league_name:
        return 0.60
    for key, w in COMPETITION_WEIGHTS.items():
        if key.lower() in league_name.lower():
            return w
    return 0.60


def parse_fixture(fixture, team_id):
    home = fixture.get("teams", {}).get("home", {})
    away = fixture.get("teams", {}).get("away", {})
    goals = fixture.get("goals", {})
    league = fixture.get("league", {}).get("name", "")

    is_home = home.get("id") == team_id
    gf = goals.get("home") if is_home else goals.get("away")
    ga = goals.get("away") if is_home else goals.get("home")

    if gf is None or ga is None:
        return None

    return {
        "date": fixture.get("fixture", {}).get("date", ""),
        "league": league,
        "weight": get_competition_weight(league),
        "gf": int(gf),
        "ga": int(ga),
        "win": gf > ga,
        "draw": gf == ga,
        "loss": gf < ga,
        "is_home": is_home,
    }


def get_recent_matches(team_name, n=10):
    tid = get_team_id(team_name)
    if not tid:
        return None

    matches = []
    for season in [2026, 2025, 2024]:
        data, _ = api_get("fixtures", {
            "team": tid,
            "season": season,
            "status": "FT"
        })
        if data:
            for fixture in data:
                parsed = parse_fixture(fixture, tid)
                if parsed:
                    matches.append(parsed)
        if len(matches) >= n:
            break

    matches = sorted(matches, key=lambda x: x["date"], reverse=True)[:n]
    return matches if matches else None


def get_h2h(team_a, team_b, n=8):
    tid_a = get_team_id(team_a)
    tid_b = get_team_id(team_b)
    if not tid_a or not tid_b:
        return None

    data, _ = api_get("fixtures/headtohead", {
        "h2h": f"{tid_a}-{tid_b}",
        "season": 2026,
        "status": "FT"
    })
    if not data:
        return None

    matches = []
    for fixture in data:
        parsed = parse_fixture(fixture, tid_a)
        if parsed:
            matches.append(parsed)

    return matches if matches else None


def get_wc2026_results():
    data, _ = api_get("fixtures", {
        "league": WORLD_CUP_2026_LEAGUE_ID,
        "season": 2026,
        "status": "FT"
    })
    if not data:
        data, _ = api_get("fixtures", {
            "league": WORLD_CUP_2026_LEAGUE_ID_ALT,
            "season": 2026,
            "status": "FT"
        })
    if not data:
        return []

    results = []
    for fixture in data:
        home = fixture.get("teams", {}).get("home", {}).get("name", "")
        away = fixture.get("teams", {}).get("away", {}).get("name", "")
        gh = fixture.get("goals", {}).get("home")
        ga = fixture.get("goals", {}).get("away")
        if gh is None or ga is None:
            continue
        results.append({
            "home": home, "away": away,
            "home_goals": int(gh), "away_goals": int(ga),
            "date": fixture.get("fixture", {}).get("date", ""),
        })

    return results


def calculate_weighted_form(matches):
    if not matches or len(matches) < 2:
        return None

    import numpy as np

    base_weights = np.exp(np.linspace(0, 1, len(matches)))
    comp_weights = np.array([m["weight"] for m in matches])
    weights = base_weights * comp_weights
    weights /= weights.sum()

    gf = np.array([m["gf"] for m in matches], dtype=float)
    ga = np.array([m["ga"] for m in matches], dtype=float)
    wins = np.array([m["win"] for m in matches], dtype=float)
    draws = np.array([m["draw"] for m in matches], dtype=float)

    return {
        "goals_per_game":          float(np.average(gf, weights=weights)),
        "goals_conceded_per_game": float(np.average(ga, weights=weights)),
        "win_rate":                float(np.average(wins, weights=weights)),
        "draw_rate":               float(np.average(draws, weights=weights)),
        "points_per_game":         float(np.average(wins * 3 + draws, weights=weights)),
        "matches_used":            len(matches),
        "leagues":                 list(set(m["league"] for m in matches))[:4],
    }


def calculate_h2h_stats(matches_from_a_perspective):
    if not matches_from_a_perspective:
        return None

    total = len(matches_from_a_perspective)
    wins  = sum(1 for m in matches_from_a_perspective if m["win"])
    draws = sum(1 for m in matches_from_a_perspective if m["draw"])
    losses= sum(1 for m in matches_from_a_perspective if m["loss"])
    avg_gf = sum(m["gf"] for m in matches_from_a_perspective) / total
    avg_ga = sum(m["ga"] for m in matches_from_a_perspective) / total

    return {
        "total": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": wins / total,
        "draw_rate": draws / total,
        "avg_gf": avg_gf,
        "avg_ga": avg_ga,
    }


def get_wc2026_team_stats(team_name, wc_results=None):
    if wc_results is None:
        wc_results = get_wc2026_results()

    team_games = []
    for r in wc_results:
        if r["home"].lower() == team_name.lower():
            team_games.append({"gf": r["home_goals"], "ga": r["away_goals"]})
        elif r["away"].lower() == team_name.lower():
            team_games.append({"gf": r["away_goals"], "ga": r["home_goals"]})

    if not team_games:
        return None

    gf  = sum(g["gf"] for g in team_games)
    ga  = sum(g["ga"] for g in team_games)
    wins= sum(1 for g in team_games if g["gf"] > g["ga"])

    return {
        "games_played": len(team_games),
        "goals_scored": gf,
        "goals_conceded": ga,
        "wins": wins,
        "avg_gf": gf / len(team_games),
        "avg_ga": ga / len(team_games),
    }


def fetch_all_for_match(team_a, team_b):
    wc_results = get_wc2026_results()

    recent_a  = get_recent_matches(team_a)
    recent_b  = get_recent_matches(team_b)
    h2h_raw   = get_h2h(team_a, team_b)
    wc_a      = get_wc2026_team_stats(team_a, wc_results)
    wc_b      = get_wc2026_team_stats(team_b, wc_results)

    form_a    = calculate_weighted_form(recent_a)
    form_b    = calculate_weighted_form(recent_b)
    h2h_stats = calculate_h2h_stats(h2h_raw)

    return {
        "form_a":    form_a,
        "form_b":    form_b,
        "h2h":       h2h_stats,
        "wc_a":      wc_a,
        "wc_b":      wc_b,
        "available": any([form_a, form_b, h2h_stats]),
    }
