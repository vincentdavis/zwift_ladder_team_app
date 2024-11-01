import pandas as pd

from logger_config import logger

COL_BASE = ["Team", "Name", "ZP", "ZR", "FTP"]
COL_WATTS = ["w5", "w10", "w15", "w30", "w60", "w120", "w300", "w600", "w1200", "w1800"]
COL_WKG = ["wkg5", "wkg10", "wkg15", "wkg30", "wkg60", "wkg120", "wkg300", "wkg600", "wkg1200", "wkg1800"]
COL_OTHER = ["wkg", "watts", "wtotal", "wkgtotal"]


def compare_rosters(home_team: dict, away_team: dict) -> pd.DataFrame:
    home_roster = home_team.get("roster")
    away_roster = away_team.get("roster")
    if home_roster:
        riders = []
        for rider in home_roster:
            rider_data = {
                "Team": home_team["thisteam"]["name"],
                "Name": rider["ZPName"],
                "ZP": f"https://zwiftpower.com/profile.php?z={rider['id']}",
                "ZR": f"https://www.zwiftracing.app/riders/{rider['id']}",
                "FTP": rider["zwiftData"]["ftp"],
            }
            rider_data.update({k: v for k, v in rider["powerMax"]["ninety"].items()})
            riders.append(rider_data)
        df_home_roster = pd.DataFrame(riders)
    else:
        logger.warning("No home roster found")
        df_home_roster = pd.DataFrame()
    if away_roster:
        riders = []
        for rider in away_roster:
            rider_data = {
                "Team": away_team["thisteam"]["name"],
                "Name": rider["ZPName"],
                "ZP": f"https://zwiftpower.com/profile.php?z={rider['id']}",
                "ZR": f"https://www.zwiftracing.app/riders/{rider['id']}",
                "FTP": rider["zwiftData"]["ftp"],
            }
            rider_data.update({k: v for k, v in rider["powerMax"]["ninety"].items()})
            riders.append(rider_data)
        df_away_roster = pd.DataFrame(riders)
    else:
        logger.warning("No away roster found")
        df_away_roster = pd.DataFrame()

    df_rosters = pd.concat([df_home_roster, df_away_roster], axis=0)
    df_rosters.sort_values(by=["Team", "FTP"], ascending=False, inplace=True)
    df_rosters.reset_index(drop=True, inplace=True)
    return df_rosters
