import json

import pandas as pd
import streamlit as st

from data_api import get_squad
from data_plots import match_power_plot
from data_stats import compare_rosters
from logger_config import logger

st.set_page_config(page_title="Match", layout="wide", initial_sidebar_state="collapsed")


# Constants
TEAM_FIELDS = [
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
def cache_squad(team_id):
    return get_squad(team_id)


if not st.query_params:
    logger.error("No query_params")
    st.warning("No query_params")
else:
    logger.info(f"query_params: {st.query_params}")
    with st.spinner(f"Loading match: {st.query_params["home_id"]} -vs- {st.query_params["away_id"]} ..."):
        home_team = cache_squad(st.query_params["home_id"])
        df_home_team = pd.DataFrame([{k: v for k, v in home_team["thisteam"].items() if k in TEAM_FIELDS}])
        away_team = cache_squad(st.query_params["away_id"])
        df_away_team = pd.DataFrame([{k: v for k, v in away_team["thisteam"].items() if k in TEAM_FIELDS}])

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

    df_rosters = compare_rosters(home_team, away_team)
    st.dataframe(df_rosters)

    df_differance, w_fig, wkg_fig = match_power_plot(df_rosters)
    st.plotly_chart(w_fig, use_container_width=True)
    st.plotly_chart(wkg_fig, use_container_width=True)
    st.dataframe(df_differance)
    st.download_button(
        label="Download Comparison data",
        data=df_differance.to_csv(index=False),
        file_name=f"home_team_{home_team["thisteam"]["name"]}_vs_{away_team["thisteam"]["name"]}.csv",
        mime="application/csv",
    )
