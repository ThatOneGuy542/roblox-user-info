from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cookie = request.form['cookie']
        try:
            # Fetch user data using cookie
            headers = {'Cookie': f'.ROBLOSECURITY={cookie}'}
            
            # Get user ID
            user_info = requests.get('https://users.roblox.com/v1/users/authenticated', headers=headers).json()
            user_id = user_info['id']
            
            # Get user profile (username, display name, etc.)
            profile = requests.get(f'https://users.roblox.com/v1/users/{user_id}', headers=headers).json()
            
            # Get Robux balance
            robux = requests.get('https://economy.roblox.com/v1/user/currency', headers=headers).json()['robux']
            
            # Get Robux spent summary (potentially problematic)
            summary = requests.get('https://economy.roblox.com/v1/users/{user_id}/transaction-totals?timeFilter=Year', headers=headers).json()
            robux_spent = summary.get('spentRobux', 0)  # This may be incorrect
            
            # Get recently played games (potentially problematic)
            games = requests.get(f'https://games.roblox.com/v1/users/{user_id}/games', headers=headers).json()['data']
            recent_games = [game['name'] for game in games[:5]]
            
            # Other data (avatar, premium status, etc.)
            avatar = requests.get(f'https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png').json()['data'][0]['imageUrl']
            premium = requests.get(f'https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership', headers=headers).json()['isPremium']
            
            # Render results
            return render_template('result.html', username=profile['name'], display_name=profile['displayName'],
                                 robux=robux, robux_spent=robux_spent, recent_games=recent_games, avatar=avatar, premium=premium)
        except Exception as e:
            return render_template('index.html', error=f"Invalid cookie or API error: {str(e)}")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
