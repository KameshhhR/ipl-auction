# RR ScoutX — IPL 2027 Scouting Dashboard

A Streamlit-based cricket scouting dashboard built around the supplied SupeRR Selector Season 2 data pack and the two supplied RR scouting reports.

## Features
- Overview of the supplied competitions, teams, matches, deliveries and player mapping.
- All-player explorer using the complete competition/team/player mapping.
- Batting and bowling leaderboards calculated from ball-by-ball data.
- The 10 batting + 10 bowling names from the supplied scouting reports, retained even when an exact name match is absent from the mapping.
- Interactive player comparison.
- **Pressure Performance Lab** with batting and bowling pressure-context leaderboards, scatter plots, sample-size filters and CSV exports.
- Data quality and methodology notes.

## Theme
The dashboard uses the supplied bright-pink reference (`#FD10C2`) with dark plum panels, pink chart accents and a premium sports-analytics layout.

## Run locally
1. Install Python 3.10 or newer.
2. Extract this ZIP.
3. Open the `RR-ScoutX` folder in a terminal.
4. Run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. The app loads the bundled `data_pack.zip` automatically. You do not need to download the dataset separately.

## Pressure metric — read before interpreting
The Pressure Performance Lab uses an **exploratory delivery-context proxy**: death overs (16–20), later overs after at least four wickets have fallen, and overs 7+ after at least six wickets have fallen. It does not know the chase target, required run rate, match importance, opposition strength or venue context. It is therefore not a validated clutch-performance label or predictive model.

- Batting score: within-dataset percentile composite of pressure strike rate (50%), pressure runs (30%) and boundary-run share (20%).
- Bowling score: within-dataset percentile composite of lower pressure economy (45%), pressure wickets (35%) and pressure dot-ball rate (20%).
- Minimum pressure-ball filters are provided to reduce tiny-sample rankings. Always inspect sample size and compare players in role/context.

## Data and eligibility notes
- The All Players page uses player IDs in `competition_team_player_mapping.csv`.
- The 20 report candidates are kept separately from the data-pack mapping; a missing exact name match does not remove a candidate.
- Historical dataset presence does not prove current active status or IPL 2027 auction eligibility. Verify eligibility and recent figures against official sources before submission.
- No machine-learning prediction is claimed in this dashboard.
