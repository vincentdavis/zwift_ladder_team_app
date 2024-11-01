import pandas as pd
import plotly.express as px


def match_power_plot(df):
    # Define the time points (in seconds)
    time_intervals = [5, 10, 15, 30, 60, 120, 300, 600, 1200, 1800]
    differance = []
    teams = df["Team"].unique()
    for interval in time_intervals:
        row = {"Seconds": interval}
        for comp in ["w", "wkg"]:
            home_avg = df[(df["Team"] == teams[0]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].mean()
            away_avg = df[(df["Team"] == teams[1]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].mean()
            home_max = df[(df["Team"] == teams[0]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].max()
            away_max = df[(df["Team"] == teams[1]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].max()
            home_min = df[(df["Team"] == teams[0]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].min()
            away_min = df[(df["Team"] == teams[1]) & (df[f"w{interval}"] > 0)][f"{comp}{interval}"].min()
            row.update(
                {
                    f"{comp}_Avg": home_avg - away_avg,
                    f"{comp}_Max": home_max - away_max,
                    f"{comp}_Min": home_min - away_min,
                }
            )

        differance.append(row)
    df_differance = pd.DataFrame(differance)

    w_fig = px.line(
        df_differance, x="Seconds", y=["w_Min", "w_Avg", "w_Max"], title="Power Differance Curve", line_shape="spline"
    )
    w_fig.update_layout(yaxis_title="Home - Away")

    watt_y_range = max(
        abs(df_differance[["w_Min", "w_Avg", "w_Max"]].values.min()),
        abs(df_differance[["w_Min", "w_Avg", "w_Max"]].values.max()),
    )

    w_fig.update_layout(
        yaxis_title=f"{teams[0]} - {teams[1]}",
        yaxis=dict(
            range=[-watt_y_range, watt_y_range]  # This centers 0
        ),
        height=600,
    )

    wkg_fig = px.line(
        df_differance,
        x="Seconds",
        y=["wkg_Min", "wkg_Avg", "wkg_Max"],
        title="WKG Differance Curve",
        line_shape="spline",
    )
    wkg_y_range = max(
        abs(df_differance[["wkg_Min", "wkg_Avg", "wkg_Max"]].values.min()),
        abs(df_differance[["wkg_Min", "wkg_Avg", "wkg_Max"]].values.max()),
    )

    wkg_fig.update_layout(
        yaxis_title=f"{teams[0]} - {teams[1]}",
        yaxis=dict(
            range=[-wkg_y_range, wkg_y_range]  # This centers 0
        ),
        height=600,
    )

    return df_differance, w_fig, wkg_fig
