import json
from datetime import datetime

import pandas as pd
import streamlit as st

from data_api import datetime_handler, format_timedelta, get_ladder
from logger_config import logger

st.set_page_config(page_title="Ladder Fixtures", layout="wide", initial_sidebar_state="collapsed")

FIXTURE_COLUMNS = [
    # "Date",
    # "Time",
    "Go Time",
    # "date_time",
    # "Home id",
    "Home Name",
    # "Away id",
    "Away Name",
    "Route",
    "Power ups",
    # "Fixture id",
    "Link",
]


@st.cache_data
def cache_ladder() -> dict:
    """Caches ladder fixtures data using Streamlit's caching mechanism.

    Returns:
        Dict: Ladder fixture data
    Raises:
        RuntimeError: If ladder data cannot be retrieved

    """
    try:
        logger.info("Loading ladder data")
        data = get_ladder()
        if not data["fixtures"]:  # Currently only using the ficture data
            raise ValueError("Invalid ladder fixture data structure")
        return data
    except Exception as e:
        logger.error(f"Failed to load ladder data: {e}")
        raise RuntimeError("Failed to load ladder data") from e


ladder = cache_ladder()

df_ladder = pd.DataFrame(ladder["fixtures"])
team_list = sorted(list(df_ladder["Home Name"].unique()) + list(df_ladder["Away Name"].unique()))
team_list.insert(0, "All Teams")

df_ladder["Link"] = df_ladder.apply(lambda row: f"/Match?home_id={row['Home id']}&away_id={row['Away id']}", axis=1)
now = datetime.now()
df_ladder["time_delta"] = df_ladder["date_time"] - now
df_ladder["Go Time"] = df_ladder["time_delta"].apply(format_timedelta)
df_ladder.sort_values(by=["date_time"], inplace=True)


def filter_dataframe(df, team: str = "All Teams"):
    """Filter dataframe based on selected team"""
    if team != "All Teams":
        df = df[(df["Home Name"] == team) | (df["Away Name"] == team)]
    st.dataframe(
        df[FIXTURE_COLUMNS],
        column_config={
            "Link": st.column_config.LinkColumn("View Match", display_text="Open"),
        },
        use_container_width=True,
    )


selected_team = st.selectbox(
    "Select team", team_list, index=0, on_change=filter_dataframe, args=(df_ladder, "team_filter"), key="team_filter"
)

filter_dataframe(df_ladder, selected_team)


col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Reload data"):
        st.cache_data.clear()
        st.success("Data reloaded!")
        st.rerun()
with col2:
    st.download_button(
        label="⬇️Download JSON",
        data=json.dumps(ladder, default=datetime_handler, indent=2),
        file_name="ladder.json",
        mime="application/json",
    )
