import json

import pandas as pd
import streamlit as st

from ladder import get_squad

st.set_page_config(page_title="Ladder Fixtures", layout="wide", initial_sidebar_state="collapsed")
st.title("Match")
team_fields = [
    "club",
    "name",
    "LadderPos",
    "won",
    "ZRRankUpper",
    "ZRRank",
    "ZRRankSub",
    "ZRAvgScore",
    "ZRAvgActiveScore",
    "capName",
    "tzCaptain",
]


@st.cache_data
def cache_squad(id):
    return get_squad(id)


if not st.query_params:
    st.write("No query_params")
else:
    # st.write(st.query_params)
    with st.spinner(f"Loading match: {st.query_params["home_id"]} -vs- {st.query_params["away_id"]} ..."):
        home_team = cache_squad(st.query_params["home_id"])
        df_home_team = pd.DataFrame([{k: v for k, v in home_team["thisteam"].items() if k in team_fields}])
        away_team = cache_squad(st.query_params["away_id"])
        df_away_team = pd.DataFrame([{k: v for k, v in away_team["thisteam"].items() if k in team_fields}])

    st.success(f"Loaded match: {home_team["thisteam"]["name"]} -vs- {away_team["thisteam"]["name"]} ...")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Reload data"):
            st.cache_data.clear()
            st.success("Data reloaded!")
            st.rerun()
    with col2:
        st.download_button(
            label=f"Download {home_team["thisteam"]["name"]} data",
            data=json.dumps(home_team, indent=2),
            file_name=f"home_team_{home_team["thisteam"]["name"]}_{st.query_params["home_id"]}.json",
            mime="application/json",
        )
    with col3:
        st.download_button(
            label=f"Download {away_team["thisteam"]["name"]} data",
            data=json.dumps(home_team, indent=2),
            file_name=f"away_team_{away_team["thisteam"]["name"]}_{st.query_params["away_id"]}.json",
            mime="application/json",
        )
    df_teams = pd.concat([df_home_team, df_away_team], axis=0)
    st.dataframe(
        df_teams,
        hide_index=True,
    )

    home_roster = home_team.get("roster", None)
    away_roster = away_team.get("roster", None)
    if home_roster:
        riders = []
        for rider in home_roster:
            rider_data = {"name": rider["ZPName"], "FTP": rider["zwiftData"]["ftp"]}
            rider_data.update({k: v for k, v in rider["powerMax"]["ninety"].items()})
            riders.append(rider_data)
        df_home_roster = pd.DataFrame(riders)
    else:
        df_home_roster = pd.DataFrame()
    if away_roster:
        riders = []
        for rider in away_roster:
            rider_data = {"name": rider["ZPName"], "FTP": rider["zwiftData"]["ftp"]}
            rider_data.update({k: v for k, v in rider["powerMax"]["ninety"].items()})
            riders.append(rider_data)
        df_away_roster = pd.DataFrame(riders)
    else:
        df_away_roster = pd.DataFrame()

    df_rosters = pd.concat([df_home_roster, df_away_roster], axis=0)
    st.dataframe(df_rosters)
