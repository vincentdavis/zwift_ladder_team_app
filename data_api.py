import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx
from bs4 import BeautifulSoup


def format_timedelta(td: timedelta) -> str:
    """Formats a timedelta into a human-readable string showing hours and minutes.

    Args:
        td: Timedelta to format
    Returns:
        str: Formatted string like "2h 30m" or "Past" for negative timedeltas

    """
    if td.total_seconds() < 0:
        return "Past"

    total_hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)

    if total_hours > 24:
        days = total_hours // 24
        hours = total_hours % 24
        return f"{days}d {hours}h {minutes}m"
    return f"{total_hours}h {minutes}m"


def parse_fixtures(html_content: str) -> list[dict]:
    """Parse fixture table data from the provided HTML content.

    Args:
        html_content (str): Raw HTML content containing the fixture table

    Returns:
        List[Dict]: List of fixtures with parsed data

    """
    soup = BeautifulSoup(html_content, "html.parser")
    fixture_table = soup.find("div", class_="fixtureTab")

    fixtures = []
    current_date = None

    # Iterate through all rows in the table
    for row in fixture_table.find_all("tr"):
        # Check if it's a date boundary row
        if "dayBounds" in row.get("class", []):
            current_date = row.find("td").text.strip().lower()
            if current_date == "today":
                current_date = date.today()
            else:
                current_date = datetime.strptime(current_date, "%Y-%m-%d").date()
            continue

        # Skip blank fixture rows
        if "blankFixturesRow" in row.get("class", []):
            continue

        # Process fixture rows
        if "fixFuture" in row.get("class", []) or "fixToday" in row.get("class", []):
            # Extract data from the row
            cells = row.find_all("td")
            if len(cells) >= 5:
                # Get powerups
                powerups = [img["alt"] for img in cells[4].find_all("img", class_="pup-small")]

                home_team_span = cells[1].find("span", class_="teamOpener")
                home_team_id = home_team_span.get("data-team-id") if home_team_span else None
                home_team_name = home_team_span.text.strip() if home_team_span else None

                away_team_span = cells[2].find("span", class_="teamOpener")
                away_team_id = away_team_span.get("data-team-id") if away_team_span else None
                away_team_name = away_team_span.text.strip() if away_team_span else None

                # Create fixture dictionary
                fixture = {
                    "Date": current_date,
                    "Time": cells[0].text.strip(),
                    "date_time": datetime.strptime(f"{current_date} {cells[0].text.strip()}", "%Y-%m-%d %H:%M"),
                    "Home id": home_team_id,
                    "Home Name": home_team_name,
                    "Away id": away_team_id,
                    "Away Name": away_team_name,
                    "Route": cells[3].text.strip(),
                    "Power ups": powerups,
                    "Fixture id": row.get("data-id"),
                    "Status": "future" if "fixFuture" in row.get("class", []) else "today",
                }
                fixtures.append(fixture)

    return fixtures


def get_squad(team_id: int) -> dict:
    """Parse player cards from the MVP section.

    Args:
        html_content (str): Raw HTML content containing the player cards

    Returns:
        List[PlayerCard]: List of parsed player data

    """
    try:
        with httpx.Client() as client:
            response = client.get(f"https://ladder.cycleracing.club/openteam/n/{team_id}")
            response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Error fetching squad: {e}")

    soup = BeautifulSoup(response.content, "html.parser")
    # find the script with the data
    script_tag = soup.find("script", string=re.compile(r"Ladder\.thisteam\s*="))
    script_content = script_tag.string
    str_data = {
        "thisteam": re.search(r"Ladder\.thisteam\s*=\s*({.*?});", script_content, re.DOTALL),
        "pageclub": re.search(r"Ladder\.pageclub\s*=\s*({.*?});", script_content, re.DOTALL),
        "stats": re.search(r"Ladder\.stats\s*=\s*({.*?});", script_content, re.DOTALL),
        "team": re.search(r"Ladder\.team\s*=\s*({.*?});", script_content, re.DOTALL),
        "belts": re.search(r"Ladder\.belts\s*=\s*({.*?});", script_content, re.DOTALL),
        "roster": re.search(r"Ladder\.roster\s*=\s*(\[.*?\]);", script_content, re.DOTALL),
    }

    json_data = {"id": team_id}
    for key, value in str_data.items():
        if value:
            json_data[key] = json.loads(value.group(1))
        else:
            json_data[key] = {}
    return json_data


def get_ladder(url: str = "https://ladder.cycleracing.club/summary") -> dict[str, list[dict]]:
    """Fetch and parse fixtures from the website.

    Args:
        url (str): URL to fetch fixtures from

    Returns:
        List[Dict]: List of parsed fixtures

    """
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Error fetching fixtures: {e}")
        return {}

    # Parse the page
    data = {"fixtures": parse_fixtures(response.text)}
    return data


@dataclass
class FormResult:
    result: str  # 'W' for win, 'L' for loss, 'D' for defend
    is_defend: bool = False  # True for defended wins


@dataclass
class TeamRanking:
    position: int
    team_name: str
    club_name: str
    team_id: str
    region_id: str
    form: list[FormResult]
    movement: str  # '▲' up, '▼' down, '=' static
    movement_amount: int | None = None
    is_zombie: bool = False
    has_bonus_drop: bool = False


def parse_form_square(square_div) -> FormResult:
    """Parse a single form square to get the result and if it was a defend."""
    if not square_div.text.strip():
        return FormResult("")

    # Check if it's a defended win (underlined W)
    span = square_div.find("span")
    is_defend = span is not None and "text-decoration:underline" in str(span)

    result = square_div.text.strip()
    if result and result[0] in "WL":
        return FormResult(result[0], is_defend)
    return FormResult("")


def parse_ladder_table(html_content: str) -> list[TeamRanking]:
    """Parse the ladder table and return a list of team rankings."""
    soup = BeautifulSoup(html_content, "html.parser")
    ladder_table = soup.find("table", class_="template-ladder")
    if not ladder_table:
        return []

    rankings = []

    for row in ladder_table.find("tbody").find_all("tr", class_="ladderRow"):
        # Get base team data
        position = int(row.find("td", class_="nposCol").text.strip())
        team_name = row.find("td", class_="highlightBold").text.strip()
        club_name = row.find("td", class_="clubReplace").text.strip()

        # Get team IDs and region
        team_id = row.get("data-team-id", "")
        region_id = row.get("data-team-region", "")

        # Check if team is zombie
        is_zombie = "zombieTeamRow" in row.get("class", [])

        # Parse form squares
        form_div = row.find("span", class_="d-flex")
        form_squares = form_div.find_all("div", class_="formSquare") if form_div else []
        form = [parse_form_square(square) for square in form_squares]

        # Parse movement
        move_div = row.find("div", class_="movebubble")
        if move_div:
            movement = (
                "="
                if "staticMove" in move_div.get("class", [])
                else "▲"
                if "upMove" in move_div.get("class", [])
                else "▼"
                if "downMove" in move_div.get("class", [])
                else "="
            )

            # Get movement amount if present
            move_text = move_div.text.strip()
            try:
                # Find any numbers in the movement text
                movement_amount = int("".join(filter(str.isdigit, move_text)))
            except ValueError:
                movement_amount = None
        else:
            movement = "="
            movement_amount = None

        # Check for bonus drop
        bonus_drop = bool(row.find("span", string=lambda x: x and "Bonus Drop" in x))

        ranking = TeamRanking(
            position=position,
            team_name=team_name,
            club_name=club_name,
            team_id=team_id,
            region_id=region_id,
            form=form,
            movement=movement,
            movement_amount=movement_amount,
            is_zombie=is_zombie,
            has_bonus_drop=bonus_drop,
        )

        rankings.append(ranking)

    return rankings


def get_ladder_rankings(url: str = "https://ladder.cycleracing.club") -> list[TeamRanking]:
    """Fetch and parse the ladder rankings from the website."""
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            return parse_ladder_table(response.text)
    except httpx.RequestError as e:
        print(f"Error fetching ladder rankings: {e}")
        return []


def datetime_handler(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
