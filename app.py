from flask import Flask, request, render_template
import requests
from datetime import datetime
from dateutil import parser

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

        # Get Robux pending
        pending_url = "https://economy.roblox.com/v1/users/authenticated/revenue/summary/pending"
        pending_response = session.get(pending_url)
        pending_response.raise_for_status()
        pending_data = pending_response.json()
        robux_pending = pending_data.get("pendingRobux", 0)

        # Get premium status
        premium_url = f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership"
        premium_response = session.get(premium_url)
        premium_status = "Yes" if premium_response.status_code == 200 else "No"

        # Get creation date
        creation_date_url = f"https://users.roblox.com/v1/users/{user_id}"
        creation_date_response = session.get(creation_date_url)
        creation_date_response.raise_for_status()
        creation_date_data = creation_date_response.json()
        creation_date = parser.parse(creation_date_data["created"]).strftime("%Y-%m-%d %H:%M:%S")

        # Get avatar image
        avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        avatar_response = session.get(avatar_url)
        avatar_response.raise_for_status()
        avatar_data = avatar_response.json()
        avatar_image_url = avatar_data["data"][0]["imageUrl"] if avatar_data["data"] else "N/A"

        # Get groups owned, group Robux, and group pending
        groups_url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        groups_response = session.get(groups_url)
        groups_response.raise_for_status()
        groups_data = groups_response.json()
        groups_owned = sum(1 for group in groups_data["data"] if group["role"]["rank"] == 255)
        group_robux = 0
        group_pending = 0
        for group in groups_data["data"]:
            if group["role"]["rank"] == 255:  # User is owner
                group_id = group["group"]["id"]
                # Group Robux
                group_economy_url = f"https://economy.roblox.com/v1/groups/{group_id}/currency"
                group_economy_response = session.get(group_economy_url)
                if group_economy_response.status_code == 200:
                    group_economy_data = group_economy_response.json()
                    group_robux += group_economy_data.get("robux", 0)
                # Group Pending
                group_pending_url = f"https://economy.roblox.com/v1/groups/{group_id}/revenue/summary/pending"
                group_pending_response = session.get(group_pending_url)
                if group_pending_response.status_code == 200:
                    group_pending_data = group_pending_response.json()
                    group_pending += group_pending_data.get("pendingRobux", 0)

        # Get credit balance (approximated from Robux)
        credit_balance = round(robux_balance * 0.0035, 2)  # Roblox exchange rate: 1 Robux ≈ $0.0035

        # Get email verification status
        email_url = "https://accountsettings.roblox.com/v1/email"
        email_response = session.get(email_url)
        email_response.raise_for_status()
        email_data = email_response.json()
        email_verified = "Yes" if email_data.get("verified", False) else "No"

        # Get RAP (Recent Average Price)
        rap = 0
        inventory_url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=100"
        inventory_response = session.get(inventory_url)
        if inventory_response.status_code == 200:
            inventory_data = inventory_response.json()
            for item in inventory_data.get("data", []):
                rap += item.get("recentAveragePrice", 0)

        return {
            "username": username,
            "display_name": display_name,
            "robux": robux_balance,
            "robux_pending": robux_pending,
            "premium": premium_status,
            "creation_date": creation_date,
            "user_id": user_id,
            "avatar_url": avatar_image_url,
            "groups_owned": groups_owned,
            "group_robux": group_robux,
            "group_pending": group_pending,
            "credit_balance": credit_balance,
            "email_verified": email_verified,
            "rap": rap,
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
