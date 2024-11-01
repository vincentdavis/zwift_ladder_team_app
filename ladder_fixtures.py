import datetime
import json

import pandas as pd
import streamlit as st

from data_api import get_ladder
from logger_config import logger

st.set_page_config(page_title="Ladder Fixtures", layout="wide", initial_sidebar_state="collapsed")


def datetime_handler(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


fixture_columns = [
    "Date",
    "Time",
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
def cache_ladder():
    return get_ladder()


logger.info("Load Ladder Fixture data")
ladder = cache_ladder()

df_ladder = pd.DataFrame(ladder["fixtures"])
df_ladder["Link"] = df_ladder.apply(lambda row: f"/Match?home_id={row['Home id']}&away_id={row['Away id']}", axis=1)
df_ladder.sort_values(by=["date_time"], inplace=True)

col1, col2 = st.columns(2)


with col1:
    if st.button("🔄 Reload data"):
        st.cache_data.clear()
        st.success("Data reloaded!")
        st.rerun()
with col2:
    st.download_button(
        label="Download JSON",
        data=json.dumps(ladder, default=datetime_handler, indent=2),
        file_name="ladder.json",
        mime="application/json",
    )

st.dataframe(
    df_ladder[fixture_columns], column_config={"Link": st.column_config.LinkColumn("View Match", display_text="Open")}
)
