from flask import Flask, request, render_template
import requests
from datetime import datetime, timedelta
from dateutil import parser  # Add dateutil for flexible parsing

app = Flask(__name__)

def get_user_info(cookie):
    try:
        session = requests.Session()
        session.cookies[".ROBLOSECURITY"] = cookie

        # Get user profile
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

        # Get Robux spent (past year)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        transactions_url = f"https://economy.roblox.com/v2/users/{user_id}/transactions?transactionType=Purchase&limit=100"
        transactions_response = session.get(transactions_url)
        transactions_response.raise_for_status()
        transactions_data = transactions_response.json()
        robux_spent = 0
        for tx in transactions_data.get("data", []):
            if tx["currency"]["type"] == "Robux" and tx["currency"]["amount"] < 0:
                try:
                    # Parse transaction date flexibly
                    tx_date = parser.parse(tx["created"])
                    if start_date <= tx_date.replace(tzinfo=None) <= end_date:
                        robux_spent += abs(tx["currency"]["amount"])
                except ValueError:
                    continue  # Skip malformed dates

        # Get recently played games (presence-based)
        presence_url = "https://presence.roblox.com/v1/presence/users"
        presence_response = session.post(presence_url, json={"userIds": [user_id]})
        if presence_response.status_code == 429:
            recent_games = ["Rate limit exceeded, try again later"]
        else:
            presence_response.raise_for_status()
            presence_data = presence_response.json()
            last_game = presence_data["userPresences"][0].get("lastLocation", "No recent games")
            recent_games = [last_game] if last_game != "No recent games" else ["No recent games"]

        # Get premium status
        premium_url = f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership"
        premium_response = session.get(premium_url)
        premium_status = "Yes" if premium_response.status_code == 200 else "No"

        # Get creation date
        creation_date_url = f"https://users.roblox.com/v1/users/{user_id}"
        creation_date_response = session.get(creation_date_url)
        creation_date_response.raise_for_status()
        creation_date_data = creation_date_response.json()
        # Parse creation date flexibly
        creation_date = parser.parse(creation_date_data["created"]).strftime("%Y-%m-%d %H:%M:%S")

        # Get avatar image
        avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        avatar_response = session.get(avatar_url)
        avatar_response.raise_for_status()
        avatar_data = avatar_response.json()
        avatar_image_url = avatar_data["data"][0]["imageUrl"] if avatar_data["data"] else "N/A"

        # Get groups owned and group Robux
        groups_url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        groups_response = session.get(groups_url)
        groups_response.raise_for_status()
        groups_data = groups_response.json()
        groups_owned = sum(1 for group in groups_data["data"] if group["role"]["rank"] == 255)
        group_robux = 0
        for group in groups_data["data"]:
            if group["role"]["rank"] == 255:  # User is owner
                group_id = group["group"]["id"]
                group_economy_url = f"https://economy.roblox.com/v1/groups/{group_id}/currency"
                group_economy_response = session.get(group_economy_url)
                if group_economy_response.status_code == 200:
                    group_economy_data = group_economy_response.json()
                    group_robux += group_economy_data.get("robux", 0)

        return {
            "username": username,
            "display_name": display_name,
            "robux": robux_balance,
            "robux_spent": robux_spent,
            "premium": premium_status,
            "creation_date": creation_date,
            "user_id": user_id,
            "avatar_url": avatar_image_url,
            "groups_owned": groups_owned,
            "group_robux": group_robux,
            "recent_games": recent_games,
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
