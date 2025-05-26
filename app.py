from flask import Flask, request, render_template
import requests
from datetime import datetime

app = Flask(__name__)

def get_user_info(cookie):
    try:
        session = requests.Session()
        session.cookies[".ROBLOSECURITY"] = cookie

        # Get user profile information
        profile_url = "https://users.roblox.com/v1/users/authenticated"
        profile_response = session.get(profile_url)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        user_id = profile_data["id"]
        username = profile_data["name"]
        display_name = profile_data["displayName"]

        # Get Robux balance
        robux_url = "https://economy.roblox.com/v1/user/currency"
        robux_response = session.get(robux_url)
        robux_response.raise_for_status()
        robux_data = robux_response.json()
        robux_balance = robux_data["robux"]

        # Check premium status
        premium_url = "https://premiumfeatures.roblox.com/v1/users/authenticated/premium"
        premium_response = session.get(premium_url)
        premium_status = "Yes" if premium_response.status_code == 200 else "No"

        # Get account creation date
        creation_date_url = f"https://users.roblox.com/v1/users/{user_id}"
        creation_date_response = session.get(creation_date_url)
        creation_date_response.raise_for_status()
        creation_date_data = creation_date_response.json()
        creation_date = datetime.strptime(creation_date_data["created"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")

        # Get avatar image
        avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        avatar_response = session.get(avatar_url)
        avatar_response.raise_for_status()
        avatar_data = avatar_response.json()
        avatar_image_url = avatar_data["data"][0]["imageUrl"] if avatar_data["data"] else "N/A"

        # Get groups owned and their Robux balance
        groups_url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        groups_response = session.get(groups_url)
        groups_response.raise_for_status()
        groups_data = groups_response.json()
        groups_owned = sum(1 for group in groups_data["data"] if group["role"]["rank"] == 255)  # Rank 255 is owner

        # Fetch group Robux balance (only for owned groups)
        group_robux = 0
        for group in groups_data["data"]:
            if group["role"]["rank"] == 255:  # User is owner
                group_id = group["group"]["id"]
                group_economy_url = f"https://economy.roblox.com/v1/groups/{group_id}/currency"
                group_economy_response = session.get(group_economy_url)
                if group_economy_response.status_code == 200:
                    group_economy_data = group_economy_response.json()
                    group_robux += group_economy_data.get("robux", 0)

        # Placeholder data (since Roblox API doesn't provide these directly)
        pending_robux = 0  # Not available via public API
        summary = 11429  # Placeholder for total Robux spent
        rap = 0  # Recent Average Price, not available
        credit = 0  # Credit balance, not available
        recently_played = [
            "💵[2X] Adopt Me!💵", "[⛲] Grow a Garden 🍅", "PLS DONATE 💸", "[☄️⭐GRAVITY] Blox Fruits",
            "🔹 Jailbreak", "The Strongest Battlegrounds", "Phantom Forces", "[🎂BIRTHDAY] BedWars",
            "Dead Rails [Alpha]", "[HIORI] Blue Lock: Rivals", "Catalog Avatar Creator", "Murderers VS Sheriffs DUELS",
            "Blade Ball", "⚡Race Clicker", "LEL", "Attack on Titan Revolution", "[NEW GEAR] PARKOUR Legacy",
            "[ONE EYED] GHOUL://RE", "Murder Mystery 2", "Getting Over it[Remastered]🔨", "Dash World",
            "Guess The Meme 🔊", "Barber Bus", "Longest Answer Wins [NEW QUESTIONS]", "Tower of Hell",
            "Sol's RNG [ Eon 1-4.5 ]", "[🌕UPDATE 5.5🌕] Anime Vanguards", "RIVALS", "Truck Chaos [ABILITIES!]",
            "[BEASTS UPDATE] Azure Latch", "[🤹APRIL FOOL'S🤡] AA", "Neon Run [UPDATE🎁]", "Shrimp"
        ]

        return {
            "username": username,
            "display_name": display_name,
            "robux": robux_balance,
            "pending_robux": pending_robux,
            "premium": premium_status,
            "creation_date": creation_date,
            "user_id": user_id,
            "avatar_url": avatar_image_url,
            "groups_owned": groups_owned,
            "group_robux": group_robux,
            "summary": summary,
            "rap": rap,
            "credit": credit,
            "recently_played": recently_played,
            "error": None
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"Error fetching data: {e}. The cookie may be invalid."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cookie = request.form.get("cookie").strip()
        if not cookie:
            return render_template("index.html", error="Please enter a valid cookie.")
        result = get_user_info(cookie)
        return render_template("result.html", result=result)
    return render_template("index.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)
