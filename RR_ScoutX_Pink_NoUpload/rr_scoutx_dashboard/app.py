import io
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# RR SCOUTX | Cricket talent scouting dashboard
# Data source: supplied SupeRR Selector Season 2 data pack
# Shortlists: supplied batting and bowling scouting reports
# ------------------------------------------------------------

st.set_page_config(
    page_title="RR ScoutX | IPL 2027 Scouting",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark, compact sports-analytics styling
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(circle at 8% 0%, #47123d 0%, #1b1025 38%, #100d19 100%); color: #fff4fb; }
[data-testid="stHeader"] { background: rgba(16,13,25,.88); }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#241027 0%,#130d1b 100%); border-right: 1px solid #6e285c; }
.block-container { padding-top: 1.35rem; padding-bottom: 2rem; max-width: 1550px; }
.hero { background: linear-gradient(115deg,#fd10c2 0%,#a51b86 46%,#32143b 100%); border:1px solid rgba(255,255,255,.24); border-radius:22px; padding:26px 30px; margin-bottom:20px; box-shadow:0 12px 38px rgba(253,16,194,.20); }
.hero-kicker { color:#ffe0f7; font-size:.78rem; letter-spacing:.17em; font-weight:850; }
.hero-title { color:#fff; font-size:2.5rem; font-weight:900; line-height:1.1; margin:7px 0; }
.hero-sub { color:#ffe6f8; font-size:.98rem; }
.section-note { color:#d8b7d1; font-size:.86rem; }
.metric-card { background:linear-gradient(145deg,#35152f,#211427); border:1px solid #81336f; border-radius:16px; padding:15px 17px; min-height:100px; box-shadow:0 7px 22px rgba(0,0,0,.18); }
.metric-label { color:#e8b9dc; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { color:#fff; font-size:1.8rem; font-weight:850; margin-top:5px; }
.candidate-card { background:linear-gradient(145deg,#35152f,#211427); border:1px solid #81336f; border-radius:15px; padding:16px 18px; margin-bottom:11px; }
.candidate-name { color:#fff; font-size:1.08rem; font-weight:850; }
.candidate-meta { color:#e5b8d9; font-size:.82rem; margin:4px 0 9px 0; }
.candidate-body { color:#f5e2f0; font-size:.9rem; }
.stButton>button, .stDownloadButton>button { background:linear-gradient(90deg,#fd10c2,#c82ca6); color:white; border:0; border-radius:11px; font-weight:750; }
.stButton>button:hover, .stDownloadButton>button:hover { border:1px solid #fff; color:white; box-shadow:0 0 18px rgba(253,16,194,.35); }
[data-testid="stDataFrame"] { border:1px solid #71305f; border-radius:12px; }
[data-testid="stMetric"] { background:#28152a; border:1px solid #71305f; padding:12px; border-radius:13px; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#ff73dc; border-bottom-color:#fd10c2; }
</style>
""", unsafe_allow_html=True)

DATA_FILES = {
    "competitions": "competitions.csv",
    "teams": "teams.csv",
    "matches": "matches.csv",
    "ball": "ball_by_ball.csv",
    "mapping": "competition_team_player_mapping.csv",
    "playing": "playing_eleven.csv",
}

# Candidate profiles transcribed from the user's two scouting reports.
# Report-supplied figures are kept separate from calculations on the data pack.
BATTING_CANDIDATES = [
    {"rank":1,"name":"Manisankar Murasingh","country":"India","role":"Left-hand middle/lower-middle-order batter; seam-bowling all-rounder","best_role":"No. 5–7","recent":"SMAT 2025–26: 277 runs in 7 matches; average 46.17; strike rate 172.05; 21 sixes; 6 wickets.","strength":"Boundary hitting, finishing potential and an additional bowling option.","rr_fit":"Middle-order power and lower-middle-order flexibility."},
    {"rank":2,"name":"Abhinav Manohar","country":"India","role":"Right-hand middle-order batter","best_role":"No. 5 or No. 6","recent":"Maharaja Trophy 2025: 284 runs at SR 165.12. 2026: 189 runs in 9 T20 matches at SR 154.9. Maharaja Trophy 2024: 507 runs at SR 196.51.","strength":"Power hitter who can target boundaries in middle and death overs.","rr_fit":"Middle-order power-hitting option after the top order."},
    {"rank":3,"name":"Samant Jakhar","country":"India","role":"Right-hand middle-order batter; right-arm medium bowler","best_role":"No. 5 or No. 6","recent":"SMAT 2025–26: 198 runs in 11 matches; average 24.75; strike rate 178.38; 20 sixes; highest score 60.","strength":"High strike rate, boundary hitting and medium-pace option.","rr_fit":"Aggressive middle-order batting with a part-time bowling option."},
    {"rank":4,"name":"Mridul Surroch","country":"India","role":"Right-hand batter; right-arm off-spinner","best_role":"Middle order","recent":"SMAT 2025–26: 201 runs in 7 matches; average 50.25; strike rate 164.75; 9 sixes. Also 52 off 35 in the opening match of SMAT 2026–27.","strength":"Strong recent average with attacking strike rate; can contribute off-spin.","rr_fit":"Domestic batting option who can build and accelerate."},
    {"rank":5,"name":"Vansh Bedi","country":"India","role":"Wicketkeeper-batter","best_role":"No. 6 or No. 7","recent":"Available player database T20 record: 393 runs in 22 matches at SR 196.50. 2026 entry: 206 runs in 13 matches at SR 206.","strength":"Aggressive scoring profile and wicketkeeping ability.","rr_fit":"Lower-middle-order option and wicketkeeping cover."},
    {"rank":6,"name":"Salman Nizar","country":"India","role":"Left-hand middle-order batter; occasional right-arm off-spin","best_role":"No. 5–7","recent":"Kerala Cricket League 2026: 306 runs in 12 matches; average 61.20; strike rate 157.73.","strength":"Left-handed power hitter with boundary-clearing ability against pace and spin.","rr_fit":"Indian left-handed middle-order option."},
    {"rank":7,"name":"Virat Singh","country":"India","role":"Left-hand batter","best_role":"No. 3–5","recent":"SMAT 2025–26: 382 runs in 11 innings; average 42.44; strike rate 169.77.","strength":"Run production with an attacking strike rate and domestic T20 experience.","rr_fit":"Indian left-hander who can stabilise and maintain momentum."},
    {"rank":8,"name":"Deepak Hooda","country":"India","role":"Right-hand middle-order batter; off-spin option","best_role":"No. 4 or No. 5","recent":"SMAT 2025–26: 305 runs in 10 innings; average 38.12; strike rate 163.97; 15 sixes; highest score 90 not out.","strength":"Middle-order experience, innings-building and acceleration; occasional off-spin.","rr_fit":"Experienced batting depth. Report notes he is India-capped, not an uncapped prospect."},
    {"rank":9,"name":"Daryl Mitchell","country":"New Zealand","role":"Right-hand middle-order batter; seam-bowling all-rounder","best_role":"No. 4 or No. 5","recent":"2026 T20Is: 176 runs from 101 balls at SR 174.26. PSL 2026: 255 runs from 204 balls.","strength":"Strong against pace, international experience and occasional medium pace.","rr_fit":"Overseas middle-order experience and all-round flexibility."},
    {"rank":10,"name":"Shai Hope","country":"West Indies","role":"Right-hand wicketkeeper-batter","best_role":"Primarily top order; flexible batting / wicketkeeping option","recent":"2026 T20I season: 601 runs in 16 innings; average 50.08; strike rate 152.50; 2 centuries and 4 fifties. 261 runs in 4 T20Is during the October 2026 India series.","strength":"Can anchor and accelerate; wicketkeeping cover and international experience.","rr_fit":"Overseas wicketkeeper-batter. Report notes his established role is top order, not specialist No. 6 or No. 7."},
]

BOWLING_CANDIDATES = [
    {"rank":1,"name":"Chama Milind","country":"India","role":"Left-arm medium-fast bowler","phase":"Death overs","recent":"SMAT 2025–26: 17 wickets; average 15.29; economy 7.50.","strength":"Left-arm angle, pace variation and slower deliveries.","rr_fit":"Indian left-arm pace option for death overs."},
    {"rank":2,"name":"Daniel Sams","country":"Australia","role":"Left-arm fast-medium bowling all-rounder; left-hand batter","phase":"Pace bowling and lower-order batting","recent":"CPL 2026: 15 wickets in 10 matches at economy 7.25. T20 Blast 2026: 19 wickets in 14 matches at economy 7.92. BBL 2025–26: 12 wickets in 10 matches.","strength":"Left-arm pace, variations and lower-order hitting.","rr_fit":"Two-skill overseas option adding pace and batting depth."},
    {"rank":3,"name":"Mustafizur Rahman","country":"Bangladesh","role":"Left-arm fast-medium bowler","phase":"Death overs","recent":"PSL 2026: 6 wickets in 5 matches at economy 6.97. ILT20 2025–26: 15 wickets in 8 matches at economy 7.81.","strength":"Cutters, slower balls and changes of pace.","rr_fit":"Experienced left-arm death-bowling option."},
    {"rank":4,"name":"KM Asif","country":"India","role":"Right-arm medium-fast bowler","phase":"Powerplay and seam bowling","recent":"SMAT 2025–26: 15 wickets in 6 matches; average 9.20; economy 6.73; best 5/24.","strength":"Recent wicket-taking ability and economical spells.","rr_fit":"Indian fast-bowling option for the powerplay."},
    {"rank":5,"name":"Shivam Shukla","country":"India","role":"Right-arm leg-spinner","phase":"Middle overs","recent":"SMAT 2025–26: 17 wickets in 10 matches; average 14.59; economy 7.26; best 4/23.","strength":"Attacking leg-spin and middle-over wicket-taking.","rr_fit":"Specialist leg-spin option for overs 7–15."},
    {"rank":6,"name":"Tanay Thyagarajan","country":"India","role":"Left-arm orthodox spin all-rounder","phase":"Middle overs","recent":"SMAT 2025–26: 16 wickets in 9 matches; average 18.00; economy 7.20; also 50 runs.","strength":"Left-arm spin control and lower-order batting.","rr_fit":"Spin option with batting flexibility."},
    {"rank":7,"name":"Taskin Ahmed","country":"Bangladesh","role":"Right-arm fast bowler","phase":"Powerplay","recent":"T20I career snapshot in report: 98 wickets in 84 matches at economy 7.79. BPL career: 128 wickets in 93 matches.","strength":"Pace, bounce and new-ball threat.","rr_fit":"High-pace powerplay wicket-taking option."},
    {"rank":8,"name":"Chetan Sakariya","country":"India","role":"Left-arm medium-fast bowler","phase":"Powerplay","recent":"T20 career snapshot: 77 wickets in 58 matches at economy 7.98. Recent 10-match sample: 11 wickets.","strength":"Left-arm angle and swing for early overs.","rr_fit":"Indian left-arm pace depth and powerplay matchup option."},
    {"rank":9,"name":"Mahli Beardman","country":"Australia","role":"Right-arm fast-medium bowler","phase":"Powerplay and middle overs","recent":"BBL 2025–26: 16 wickets in 13 matches; average 20.44; economy 7.98; best 3/17.","strength":"Young pace prospect with a strong BBL wicket return.","rr_fit":"Overseas pace prospect and longer-term development option."},
    {"rank":10,"name":"Kamlesh Nagarkoti","country":"India","role":"Right-arm fast bowler","phase":"Indian pace depth","recent":"T20 career snapshot: 32 wickets in 31 bowling innings at economy 8.19. Recent 10-match sample: 16 wickets at economy 8.14.","strength":"Domestic pace option, previous IPL experience and lower-order batting.","rr_fit":"Additional Indian fast-bowling depth."},
]

def read_data_pack(uploaded_bytes):
    """Read the six CSVs directly from the supplied ZIP archive."""
    data = {}
    with zipfile.ZipFile(io.BytesIO(uploaded_bytes)) as zf:
        names = zf.namelist()
        for key, filename in DATA_FILES.items():
            matches = [n for n in names if n.replace("\\", "/").endswith("/" + filename)]
            if not matches:
                matches = [n for n in names if n.replace("\\", "/") == filename]
            if not matches:
                raise FileNotFoundError(f"Could not find {filename} inside the ZIP.")
            data[key] = pd.read_csv(zf.open(matches[0]), low_memory=False)
    return data

@st.cache_data(show_spinner=False)
def cached_read_data_pack(uploaded_bytes):
    return read_data_pack(uploaded_bytes)

def safe_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

def build_batting(ball):
    d = ball.copy()
    d["runs"] = safe_num(d["runs"])
    d["is_four"] = d["is_four"].fillna(False).astype(bool)
    d["is_six"] = d["is_six"].fillna(False).astype(bool)
    extras = d["extras_type"].fillna("").astype(str).str.lower()
    # A wide is not a ball faced by the striker.
    d["ball_faced"] = ~extras.str.contains("wide", na=False)
    d["dismissed_batter"] = (
        safe_num(d["dismissed_player_id"]).eq(safe_num(d["striker_id"]))
        & d["is_wicket"].fillna(False).astype(bool)
    )
    g = d.groupby(["striker_id", "striker_name"], dropna=False)
    out = g.agg(
        runs=("runs", "sum"),
        balls_faced=("ball_faced", "sum"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
        dismissals=("dismissed_batter", "sum"),
        matches=("match_id", "nunique"),
        innings=("innings", lambda s: d.loc[s.index, ["match_id", "innings"]].drop_duplicates().shape[0]),
    ).reset_index()
    out["strike_rate"] = (out["runs"] / out["balls_faced"].replace(0, pd.NA) * 100).fillna(0)
    out["average"] = (out["runs"] / out["dismissals"].replace(0, pd.NA)).fillna(0)
    out["boundary_runs"] = out["fours"] * 4 + out["sixes"] * 6
    out["boundary_pct"] = (out["boundary_runs"] / out["runs"].replace(0, pd.NA) * 100).fillna(0)
    return out.rename(columns={"striker_id":"player_id", "striker_name":"player_name"})

def build_bowling(ball):
    d = ball.copy()
    extras = d["extras_type"].fillna("").astype(str).str.lower()
    # Overstep is the data-pack label for a no-ball.
    d["legal_ball"] = ~extras.str.contains("wide|overstep", na=False)
    d["bat_runs"] = safe_num(d["runs"])
    d["extra1"] = safe_num(d["extras1_runs"])
    d["extra2"] = safe_num(d["extras_2_runs"])
    # Byes/leg-byes are not charged to the bowler; other recorded extras are.
    non_charged = extras.str.contains("legbyes|byes|penalty", na=False)
    d["bowler_runs"] = d["bat_runs"] + d["extra1"] + d["extra2"]
    d.loc[non_charged, "bowler_runs"] = d.loc[non_charged, "bat_runs"]
    d["dismissal"] = d["dismissal_type"].fillna("").astype(str).str.lower()
    not_bowler_wicket = d["dismissal"].str.contains(
        "run.?out|retire|obstruct", na=False
    )
    d["bowler_wicket"] = (
        d["is_wicket"].fillna(False).astype(bool) & ~not_bowler_wicket
    )
    g = d.groupby(["bowler_id", "bowler_name"], dropna=False)
    out = g.agg(
        runs_conceded=("bowler_runs", "sum"),
        legal_balls=("legal_ball", "sum"),
        wickets=("bowler_wicket", "sum"),
        matches=("match_id", "nunique"),
    ).reset_index()
    out["overs"] = out["legal_balls"] / 6
    out["economy"] = (out["runs_conceded"] * 6 / out["legal_balls"].replace(0, pd.NA)).fillna(0)
    out["bowling_average"] = (out["runs_conceded"] / out["wickets"].replace(0, pd.NA)).fillna(0)
    out["bowling_strike_rate"] = (out["legal_balls"] / out["wickets"].replace(0, pd.NA)).fillna(0)
    return out.rename(columns={"bowler_id":"player_id", "bowler_name":"player_name"})

def build_pressure_tables(ball_df):
    """Exploratory pressure proxy from delivery context; not a verified win-probability model."""
    d = ball_df.copy()
    d["over_num"] = pd.to_numeric(d["overid"], errors="coerce").fillna(0)
    d["ball_num"] = pd.to_numeric(d["innings_ball_num"], errors="coerce").fillna(0)
    d["runs_num"] = safe_num(d["runs"])
    d["wicket_flag"] = d["is_wicket"].fillna(False).astype(bool)
    d["extras_text"] = d["extras_type"].fillna("").astype(str).str.lower()
    d["legal_ball"] = ~d["extras_text"].str.contains("wide|overstep", na=False)
    d["dismissal_text"] = d["dismissal_type"].fillna("").astype(str).str.lower()
    d["bowler_wicket"] = d["wicket_flag"] & ~d["dismissal_text"].str.contains("run.?out|retire|obstruct", na=False)
    d["bowler_runs"] = d["runs_num"] + safe_num(d["extras1_runs"]) + safe_num(d["extras_2_runs"])
    non_charged = d["extras_text"].str.contains("legbyes|byes|penalty", na=False)
    d.loc[non_charged, "bowler_runs"] = d.loc[non_charged, "runs_num"]
    d = d.sort_values(["match_id", "innings", "ball_num"])
    d["wickets_before"] = d.groupby(["match_id", "innings"])["wicket_flag"].transform(lambda x: x.cumsum().shift(fill_value=0))
    # Proxy pressure contexts: death overs, or a late innings with several wickets already down.
    d["pressure_delivery"] = (d["over_num"] >= 16) | ((d["over_num"] >= 10) & (d["wickets_before"] >= 4)) | ((d["over_num"] >= 7) & (d["wickets_before"] >= 6))
    bat = d[d["pressure_delivery"]].copy()
    bat["batter_ball"] = ~bat["extras_text"].str.contains("wide", na=False)
    bat["four"] = bat["is_four"].fillna(False).astype(bool)
    bat["six"] = bat["is_six"].fillna(False).astype(bool)
    bat["batter_dismissal"] = bat["wicket_flag"] & (pd.to_numeric(bat["dismissed_player_id"], errors="coerce") == pd.to_numeric(bat["striker_id"], errors="coerce"))
    b = bat.groupby(["striker_id", "striker_name"], dropna=False).agg(
        pressure_runs=("runs_num", "sum"), pressure_balls=("batter_ball", "sum"),
        pressure_fours=("four", "sum"), pressure_sixes=("six", "sum"),
        pressure_dismissals=("batter_dismissal", "sum"), pressure_matches=("match_id", "nunique")
    ).reset_index()
    b["pressure_sr"] = (b["pressure_runs"] / b["pressure_balls"].replace(0, pd.NA) * 100).fillna(0)
    b["pressure_average"] = (b["pressure_runs"] / b["pressure_dismissals"].replace(0, pd.NA)).fillna(0)
    b["pressure_boundary_pct"] = ((4*b["pressure_fours"] + 6*b["pressure_sixes"]) / b["pressure_runs"].replace(0, pd.NA) * 100).fillna(0)
    b["pressure_score"] = (0.50*b["pressure_sr"].rank(pct=True) + 0.30*b["pressure_runs"].rank(pct=True) + 0.20*b["pressure_boundary_pct"].rank(pct=True))*100
    b = b.rename(columns={"striker_id":"player_id", "striker_name":"player_name"})
    bowl = d[d["pressure_delivery"]].copy()
    bowl["dot_ball"] = bowl["legal_ball"] & bowl["bowler_runs"].eq(0)
    w = bowl.groupby(["bowler_id", "bowler_name"], dropna=False).agg(
        pressure_runs_conceded=("bowler_runs", "sum"), pressure_legal_balls=("legal_ball", "sum"),
        pressure_wickets=("bowler_wicket", "sum"), pressure_dots=("dot_ball", "sum"),
        pressure_matches=("match_id", "nunique")
    ).reset_index()
    w["pressure_economy"] = (w["pressure_runs_conceded"]*6 / w["pressure_legal_balls"].replace(0, pd.NA)).fillna(0)
    w["pressure_dot_pct"] = (w["pressure_dots"] / w["pressure_legal_balls"].replace(0, pd.NA)*100).fillna(0)
    economy_strength = 1 - w["pressure_economy"].rank(pct=True)
    w["pressure_score"] = (0.45*economy_strength + 0.35*w["pressure_wickets"].rank(pct=True) + 0.20*w["pressure_dot_pct"].rank(pct=True))*100
    w = w.rename(columns={"bowler_id":"player_id", "bowler_name":"player_name"})
    return b, w

def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="section-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def candidate_status(name, mapping):
    found = mapping[mapping["player_name"].astype(str).str.casefold() == name.casefold()]
    if len(found):
        return f"Found in supplied data pack ({found['player_id'].nunique()} player ID(s))"
    return "Not found by exact name in supplied player mapping — report candidate retained separately"

def show_candidate_cards(items, mapping, kind):
    for item in items:
        status = candidate_status(item["name"], mapping)
        if kind == "batting":
            details = (
                f'<b>Role:</b> {item["role"]}<br>'
                f'<b>Recent figures (from supplied scouting report):</b> {item["recent"]}<br>'
                f'<b>Strength:</b> {item["strength"]}<br>'
                f'<b>RR fit stated in report:</b> {item["rr_fit"]}'
            )
            meta = f'{item["country"]} · {item["best_role"]} · Rank #{item["rank"]}'
        else:
            details = (
                f'<b>Role:</b> {item["role"]}<br>'
                f'<b>Primary phase:</b> {item["phase"]}<br>'
                f'<b>Recent figures (from supplied scouting report):</b> {item["recent"]}<br>'
                f'<b>Strength:</b> {item["strength"]}<br>'
                f'<b>RR fit stated in report:</b> {item["rr_fit"]}'
            )
            meta = f'{item["country"]} · {item["phase"]} · Rank #{item["rank"]}'
        st.markdown(
            f'<div class="candidate-card"><div class="candidate-name">{item["rank"]}. {item["name"]}</div>'
            f'<div class="candidate-meta">{meta}<br>{status}</div>'
            f'<div class="candidate-body">{details}</div></div>',
            unsafe_allow_html=True,
        )

# ---------------- SIDEBAR: DATA SOURCE ----------------
st.sidebar.markdown("## 🏏 RR SCOUTX")
st.sidebar.caption("IPL 2027 · Cricket Talent Intelligence")
default_zip = Path(__file__).parent / "data_pack.zip"
# Dataset is bundled with this project and loads automatically.
# No manual upload control is shown in the sidebar.
if default_zip.exists():
    zip_bytes = default_zip.read_bytes()
    st.sidebar.success("Cricket dataset loaded automatically")
else:
    zip_bytes = None
    st.sidebar.error("Bundled data_pack.zip is missing. Re-extract the complete project ZIP.")

if zip_bytes is None:
    st.title("RR ScoutX")
    st.error("The bundled dataset could not be found. Please re-download and extract the complete RR ScoutX project.")
    st.stop()

try:
    with st.spinner("Loading cricket data..."):
        data = cached_read_data_pack(zip_bytes)
except Exception as e:
    st.error(f"Unable to read the data pack: {e}")
    st.stop()

players = data["mapping"].copy()
matches = data["matches"].copy()
ball = data["ball"].copy()
teams = data["teams"].copy()
competitions = data["competitions"].copy()
playing = data["playing"].copy()

for col in ["player_id", "team_id", "comp_id"]:
    if col in players.columns:
        players[col] = pd.to_numeric(players[col], errors="coerce")

batting = build_batting(ball)
bowling = build_bowling(ball)
pressure_batting, pressure_bowling = build_pressure_tables(ball)

page = st.sidebar.radio(
    "NAVIGATION",
    ["Overview", "All Players", "Batting Analytics", "Bowling Analytics",
     "Your RR Shortlists", "Pressure Performance", "Player Comparison", "Data Quality & Notes"],
)

st.markdown(
    '<div class="hero"><div class="hero-kicker">RAJASTHAN ROYALS · IPL 2027</div>'
    '<div class="hero-title">RR ScoutX</div>'
    '<div class="hero-sub">Cricket talent intelligence · pressure-performance scouting · auction shortlist explorer</div></div>',
    unsafe_allow_html=True,
)

# ---------------- OVERVIEW ----------------
if page == "Overview":
    st.subheader("Scouting overview")
    st.caption("Counts are calculated from the supplied data pack. The batting and bowling shortlist is transcribed from your uploaded scouting reports.")
    c = st.columns(4)
    c[0].metric("Unique player IDs", f"{players['player_id'].nunique():,}", "From competition-player mapping")
    c[1].metric("Matches", f"{matches['match_id'].nunique():,}")
    c[2].metric("Ball-by-ball records", f"{len(ball):,}")
    c[3].metric("Teams", f"{teams['team_id'].nunique():,}")
    st.markdown("")
    c = st.columns(4)
    c[0].metric("Competitions", f"{competitions['comp_id'].nunique():,}")
    c[1].metric("Player mapping rows", f"{len(players):,}")
    c[2].metric("Playing XI records", f"{len(playing):,}")
    c[3].metric("Report shortlist", "20 players", "10 batting + 10 bowling")

    left, right = st.columns(2)
    with left:
        st.markdown("### Competition formats")
        fmt = competitions["match_format"].fillna("Unknown").value_counts().rename_axis("Format").reset_index(name="Competitions")
        fig = px.pie(fmt, names="Format", values="Competitions", hole=.55,
                     color_discrete_sequence=["#fd10c2", "#5aa6c9", "#9b87d5"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10), legend_title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Matches by year")
        dates = pd.to_datetime(matches["match_date"], errors="coerce")
        year_df = dates.dt.year.value_counts().sort_index().rename_axis("Year").reset_index(name="Matches")
        fig = px.bar(year_df, x="Year", y="Matches", color_discrete_sequence=["#fd10c2"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Your scouting reports")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**Batting targets**")
        st.dataframe(pd.DataFrame(BATTING_CANDIDATES)[["rank","name","country","best_role"]], hide_index=True, use_container_width=True)
    with b2:
        st.markdown("**Bowling targets**")
        st.dataframe(pd.DataFrame(BOWLING_CANDIDATES)[["rank","name","country","phase"]], hide_index=True, use_container_width=True)

    st.info("The report shortlists are included independently of the data-pack player mapping. A candidate may appear in your report even if their exact name is not present in the supplied proprietary player mapping.")

# ---------------- ALL PLAYERS ----------------
elif page == "All Players":
    st.subheader("All players in the supplied data pack")
    st.caption("One row per player ID. A player can have multiple team/competition records in the original mapping.")
    all_players = (players.groupby(["player_id", "player_name"], dropna=False)
                   .agg(teams=("team_name", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
                        competitions=("comp_name", "nunique"),
                        competition_names=("comp_name", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
                        mapping_records=("comp_id", "count"))
                   .reset_index())
    all_players["player_name"] = all_players["player_name"].fillna("Unknown")
    q1, q2, q3 = st.columns([2,1,1])
    search = q1.text_input("Search player name or ID", placeholder="e.g. Shai Hope")
    team_opts = ["All"] + sorted(players["team_name"].dropna().astype(str).unique().tolist())
    team_filter = q2.selectbox("Team", team_opts)
    comp_opts = ["All"] + sorted(players["comp_name"].dropna().astype(str).unique().tolist())
    comp_filter = q3.selectbox("Competition", comp_opts)
    filtered = players.copy()
    if team_filter != "All":
        filtered = filtered[filtered["team_name"].astype(str) == team_filter]
    if comp_filter != "All":
        filtered = filtered[filtered["comp_name"].astype(str) == comp_filter]
    filtered_ids = set(filtered["player_id"].dropna().tolist())
    all_filtered = all_players[all_players["player_id"].isin(filtered_ids)].copy()
    if search:
        all_filtered = all_filtered[
            all_filtered["player_name"].astype(str).str.contains(search, case=False, na=False)
            | all_filtered["player_id"].astype(str).str.contains(search, case=False, na=False)
        ]
    st.metric("Players matching filters", f"{all_filtered['player_id'].nunique():,}")
    st.dataframe(
        all_filtered[["player_id","player_name","teams","competitions","mapping_records"]],
        use_container_width=True, hide_index=True,
        column_config={
            "player_id": st.column_config.NumberColumn("Player ID", format="%d"),
            "competitions": st.column_config.NumberColumn("Competitions", format="%d"),
        }
    )
    st.download_button("Download filtered player list CSV",
                       all_filtered.to_csv(index=False).encode("utf-8"),
                       "rr_scoutx_all_players_filtered.csv", "text/csv")

    st.markdown("### Player performance lookup")
    names = all_filtered.sort_values("player_name")["player_name"].dropna().unique().tolist()
    if names:
        chosen = st.selectbox("Select a player", names, key="all_player_detail")
        ids = all_filtered.loc[all_filtered["player_name"] == chosen, "player_id"].dropna().tolist()
        bid = batting[batting["player_id"].isin(ids)].sort_values("runs", ascending=False)
        wid = bowling[bowling["player_id"].isin(ids)].sort_values("wickets", ascending=False)
        x, y = st.columns(2)
        with x:
            st.markdown("**Batting records from ball-by-ball data**")
            st.dataframe(bid[["player_name","matches","innings","runs","balls_faced","average","strike_rate","fours","sixes"]].head(10),
                         use_container_width=True, hide_index=True)
        with y:
            st.markdown("**Bowling records from ball-by-ball data**")
            st.dataframe(wid[["player_name","matches","overs","wickets","runs_conceded","economy","bowling_average"]].head(10),
                         use_container_width=True, hide_index=True)

# ---------------- BATTING ----------------
elif page == "Batting Analytics":
    st.subheader("Batting analytics")
    st.caption("Aggregated from ball_by_ball.csv. Strike rate excludes wides from balls faced. Average uses dismissals attributed to the batter.")
    min_balls = st.slider("Minimum balls faced", 0, 500, 30, 10)
    view = batting[batting["balls_faced"] >= min_balls].copy()
    a,b,c,d = st.columns(4)
    a.metric("Batters in ball data", f"{batting['player_id'].nunique():,}")
    b.metric("Runs in records", f"{int(batting['runs'].sum()):,}")
    c.metric("Total fours", f"{int(batting['fours'].sum()):,}")
    d.metric("Total sixes", f"{int(batting['sixes'].sum()):,}")
    left,right = st.columns(2)
    with left:
        st.markdown("### Top run scorers")
        top = view.sort_values("runs", ascending=False).head(15)
        fig = px.bar(top.sort_values("runs"), x="runs", y="player_name", orientation="h",
                     hover_data=["matches","average","strike_rate"], color_discrete_sequence=["#fd10c2"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", margin=dict(l=5,r=5,t=10,b=5))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Strike rate vs runs")
        fig = px.scatter(view, x="runs", y="strike_rate", size="balls_faced", color="average",
                         hover_name="player_name", hover_data=["matches","fours","sixes"],
                         color_continuous_scale="Plasma")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Batting leaderboard")
    st.dataframe(view.sort_values(["runs","strike_rate"], ascending=False)[
        ["player_id","player_name","matches","innings","runs","balls_faced","average","strike_rate","fours","sixes","boundary_pct"]
    ], use_container_width=True, hide_index=True)
    st.download_button("Download batting leaderboard CSV",
                       view.to_csv(index=False).encode("utf-8"),
                       "rr_scoutx_batting_leaderboard.csv", "text/csv")

# ---------------- BOWLING ----------------
elif page == "Bowling Analytics":
    st.subheader("Bowling analytics")
    st.caption("Economy uses recorded runs plus bowler-chargeable extras, excluding byes, leg-byes and penalty extras. Wickets exclude run outs, retired outs and obstructing-the-field dismissals.")
    min_balls = st.slider("Minimum legal balls bowled", 0, 600, 30, 10)
    view = bowling[bowling["legal_balls"] >= min_balls].copy()
    a,b,c,d = st.columns(4)
    a.metric("Bowlers in ball data", f"{bowling['player_id'].nunique():,}")
    b.metric("Wickets credited", f"{int(bowling['wickets'].sum()):,}")
    c.metric("Legal deliveries", f"{int(bowling['legal_balls'].sum()):,}")
    d.metric("Bowlers meeting filter", f"{len(view):,}")
    left,right = st.columns(2)
    with left:
        st.markdown("### Top wicket takers")
        top = view.sort_values("wickets", ascending=False).head(15)
        fig = px.bar(top.sort_values("wickets"), x="wickets", y="player_name", orientation="h",
                     hover_data=["matches","economy","bowling_average"], color_discrete_sequence=["#ff75d9"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", margin=dict(l=5,r=5,t=10,b=5))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Economy vs wickets")
        fig = px.scatter(view, x="economy", y="wickets", size="legal_balls",
                         hover_name="player_name", hover_data=["matches","overs","bowling_average"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Bowling leaderboard")
    st.dataframe(view.sort_values(["wickets","economy"], ascending=[False,True])[
        ["player_id","player_name","matches","overs","legal_balls","wickets","runs_conceded","economy","bowling_average","bowling_strike_rate"]
    ], use_container_width=True, hide_index=True)
    st.download_button("Download bowling leaderboard CSV",
                       view.to_csv(index=False).encode("utf-8"),
                       "rr_scoutx_bowling_leaderboard.csv", "text/csv")

# ---------------- PRESSURE PERFORMANCE ----------------
elif page == "Pressure Performance":
    st.subheader("Pressure performance lab")
    st.caption("Exploratory delivery-context proxy: death overs (16–20), or later innings phases with multiple wickets already lost. This is not a verified match-pressure label or predictive model.")
    min_balls = st.slider("Minimum pressure balls / deliveries", 0, 100, 12, 4, key="pressure_min_balls")
    tab_bat, tab_bowl = st.tabs(["Batting under pressure", "Bowling under pressure"])
    with tab_bat:
        v = pressure_batting[pressure_batting["pressure_balls"] >= min_balls].copy()
        x1,x2,x3 = st.columns(3)
        x1.metric("Batters with pressure data", f"{len(v):,}")
        x2.metric("Pressure-context runs", f"{int(pressure_batting['pressure_runs'].sum()):,}")
        x3.metric("Pressure-context balls", f"{int(pressure_batting['pressure_balls'].sum()):,}")
        left,right = st.columns(2)
        with left:
            st.markdown("### Pressure score leaderboard")
            top = v.sort_values("pressure_score", ascending=False).head(15)
            fig = px.bar(top.sort_values("pressure_score"), x="pressure_score", y="player_name", orientation="h", color="pressure_score", color_continuous_scale=[[0,"#7d286e"],[.55,"#fd10c2"],[1,"#ffb7ed"]], hover_data=["pressure_runs","pressure_balls","pressure_sr","pressure_matches"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", coloraxis_showscale=False, margin=dict(l=5,r=5,t=10,b=5))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.markdown("### Strike rate vs pressure runs")
            fig = px.scatter(v, x="pressure_runs", y="pressure_sr", size="pressure_balls", color="pressure_score", hover_name="player_name", color_continuous_scale="Plasma", hover_data=["pressure_matches","pressure_average","pressure_boundary_pct"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(v.sort_values("pressure_score",ascending=False)[["player_name","pressure_matches","pressure_runs","pressure_balls","pressure_sr","pressure_average","pressure_boundary_pct","pressure_score"]], use_container_width=True, hide_index=True)
        st.download_button("Download batting pressure analysis", v.to_csv(index=False).encode("utf-8"), "rr_scoutx_batting_pressure.csv", "text/csv")
    with tab_bowl:
        v = pressure_bowling[pressure_bowling["pressure_legal_balls"] >= min_balls].copy()
        x1,x2,x3 = st.columns(3)
        x1.metric("Bowlers with pressure data", f"{len(v):,}")
        x2.metric("Pressure-context wickets", f"{int(pressure_bowling['pressure_wickets'].sum()):,}")
        x3.metric("Pressure-context legal balls", f"{int(pressure_bowling['pressure_legal_balls'].sum()):,}")
        left,right = st.columns(2)
        with left:
            st.markdown("### Pressure bowling score leaderboard")
            top = v.sort_values("pressure_score", ascending=False).head(15)
            fig = px.bar(top.sort_values("pressure_score"), x="pressure_score", y="player_name", orientation="h", color="pressure_score", color_continuous_scale=[[0,"#7d286e"],[.55,"#fd10c2"],[1,"#ffb7ed"]], hover_data=["pressure_wickets","pressure_economy","pressure_dot_pct","pressure_matches"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", coloraxis_showscale=False, margin=dict(l=5,r=5,t=10,b=5))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.markdown("### Economy vs wickets in pressure context")
            fig = px.scatter(v, x="pressure_economy", y="pressure_wickets", size="pressure_legal_balls", color="pressure_score", hover_name="player_name", color_continuous_scale="Plasma", hover_data=["pressure_matches","pressure_dot_pct"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(v.sort_values("pressure_score",ascending=False)[["player_name","pressure_matches","pressure_wickets","pressure_runs_conceded","pressure_legal_balls","pressure_economy","pressure_dot_pct","pressure_score"]], use_container_width=True, hide_index=True)
        st.download_button("Download bowling pressure analysis", v.to_csv(index=False).encode("utf-8"), "rr_scoutx_bowling_pressure.csv", "text/csv")
    st.info("Score is a within-dataset percentile composite, not an absolute ability rating. Batting score weights pressure strike rate (50%), pressure runs (30%) and boundary-run share (20%). Bowling score weights lower pressure economy (45%), wickets (35%) and dot-ball rate (20%). Interpret alongside sample size, role, opposition, venue and match context; this proxy does not know the chase target or required run rate.")

# ---------------- USER REPORT SHORTLISTS ----------------
elif page == "Your RR Shortlists":
    st.subheader("Your uploaded RR scouting shortlists")
    st.caption("These 20 names and their profile notes are taken from the two PDFs you uploaded. They are shown alongside the complete data-pack player explorer, not substituted for it.")
    tab1, tab2 = st.tabs(["Batting targets · Top 10", "Bowling targets · Top 10"])
    with tab1:
        st.markdown("### IPL 2027 auction – batting target analysis")
        st.caption("Report focus: middle-order and finishing options, especially positions No. 4 to No. 7. Shai Hope is included as a requested overseas wicketkeeper-batter; the report notes his established role is top order.")
        show_candidate_cards(BATTING_CANDIDATES, players, "batting")
        st.download_button("Download batting shortlist CSV",
                           pd.DataFrame(BATTING_CANDIDATES).to_csv(index=False).encode("utf-8"),
                           "rr_batting_top10_from_report.csv", "text/csv")
    with tab2:
        st.markdown("### IPL 2027 auction – bowling target analysis")
        st.caption("Report focus: death-over bowling, left-arm variation, powerplay wicket-taking, middle-over spin and Indian pace depth.")
        show_candidate_cards(BOWLING_CANDIDATES, players, "bowling")
        st.download_button("Download bowling shortlist CSV",
                           pd.DataFrame(BOWLING_CANDIDATES).to_csv(index=False).encode("utf-8"),
                           "rr_bowling_top10_from_report.csv", "text/csv")
    st.warning("The scouting reports state that figures are research-snapshot statistics and should be confirmed against official scorecards, player registration, current franchise status and IPL 2027 auction announcements before final submission.")

# ---------------- PLAYER COMPARISON ----------------
elif page == "Player Comparison":
    st.subheader("Player comparison")
    st.caption("Choose players from the supplied data pack. Batting and bowling metrics are calculated from its ball-by-ball records.")
    bat_names = sorted(batting["player_name"].dropna().unique().tolist())
    bowl_names = sorted(bowling["player_name"].dropna().unique().tolist())
    mode = st.radio("Compare by skill", ["Batting", "Bowling"], horizontal=True)
    pool = bat_names if mode == "Batting" else bowl_names
    if len(pool) >= 2:
        left,right = st.columns(2)
        p1 = left.selectbox("Player 1", pool, index=0)
        p2 = right.selectbox("Player 2", pool, index=1)
        source = batting if mode == "Batting" else bowling
        chosen = source[source["player_name"].isin([p1,p2])].copy()
        if mode == "Batting":
            cols = ["player_name","matches","innings","runs","average","strike_rate","fours","sixes","balls_faced"]
            chart_cols = ["runs","average","strike_rate","fours","sixes"]
        else:
            cols = ["player_name","matches","overs","wickets","economy","bowling_average","bowling_strike_rate","runs_conceded"]
            chart_cols = ["wickets","economy","bowling_average","bowling_strike_rate"]
        st.dataframe(chosen[cols], use_container_width=True, hide_index=True)
        if len(chosen) == 2:
            fig = go.Figure()
            for _, row in chosen.iterrows():
                vals = [float(row[x]) if pd.notna(row[x]) else 0 for x in chart_cols]
                fig.add_trace(go.Bar(name=row["player_name"], x=chart_cols, y=vals))
            fig.update_layout(barmode="group", template="plotly_dark",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough player records to compare.")

# ---------------- DATA QUALITY ----------------
elif page == "Data Quality & Notes":
    st.subheader("Data quality, methodology and limitations")
    quality = []
    for key, df in data.items():
        quality.append({
            "Dataset": DATA_FILES[key],
            "Rows": len(df),
            "Columns": len(df.columns),
            "Missing cells": int(df.isna().sum().sum()),
            "Duplicate full rows": int(df.duplicated().sum()),
        })
    st.dataframe(pd.DataFrame(quality), use_container_width=True, hide_index=True)
    st.markdown("### Important interpretation notes")
    st.markdown("""
    - **All players:** The All Players page uses unique player IDs from `competition_team_player_mapping.csv`; it does not limit the pool to Rajasthan Royals players or only uncapped players.
    - **Report candidates:** The 20 candidates from your uploaded batting and bowling PDFs are retained even if their exact names do not appear in the proprietary player mapping.
    - **Player status:** Historical presence in the data pack does not establish current active/retired status or IPL 2027 auction eligibility. Verify these separately before making a final recommendation.
    - **Batting calculations:** Strike rate excludes wides from balls faced. Batting average uses dismissals attributed to the striker in the delivery file.
    - **Bowling calculations:** Wides and `Overstep` are excluded from legal balls. Run outs, retired outs and obstructing-the-field dismissals are excluded from bowler wickets. Economy is calculated from the available delivery and extras fields.
    - **Pressure analysis:** Pressure Performance uses an exploratory delivery-context proxy (death overs and later overs after wickets fall) and a within-dataset percentile composite. It does not use chase target / required run rate and must not be described as a validated pressure or clutch-performance model.
    - **ML:** No ML prediction is presented in this version. Clustering or prediction should only be added after target definition, feature validation and out-of-sample evaluation.
    - **Report figures:** Candidate statistics displayed in Your RR Shortlists are reproduced from the two uploaded scouting reports and are not recalculated from the proprietary CSVs.
    """)
    st.markdown("### Data-pack coverage")
    c1,c2 = st.columns(2)
    with c1:
        st.write("**Competition formats**")
        st.dataframe(competitions["match_format"].value_counts(dropna=False).rename_axis("Format").reset_index(name="Count"), hide_index=True)
    with c2:
        st.write("**Competition seasons**")
        st.dataframe(competitions["season"].value_counts(dropna=False).rename_axis("Season").reset_index(name="Count"), hide_index=True)
    st.markdown("### Candidate match check")
    candidate_names = [x["name"] for x in BATTING_CANDIDATES] + [x["name"] for x in BOWLING_CANDIDATES]
    check = []
    for name in candidate_names:
        rows = players[players["player_name"].astype(str).str.casefold() == name.casefold()]
        check.append({"Candidate":name, "Exact name found in mapping":not rows.empty,
                      "Player IDs":", ".join(map(str, rows["player_id"].dropna().unique().tolist()))})
    st.dataframe(pd.DataFrame(check), use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.caption("RR ScoutX · Built from your supplied data pack and scouting reports")
