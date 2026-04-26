import requests
import os
import json
import math
from datetime import datetime
import time

# --- Configuration ---
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_LIMIT = int(os.environ.get("GITHUB_LIMIT", "1000")) 
FOLLOWER_SNAPSHOT_FILE = "Followers.json"
API_URL = "https://api.github.com"

# --- Helper Functions ---
def get_github_data(url, token, params=None):
    headers = {"Authorization": f"token {token}"}
    all_data = []
    page = 1
    while True:
        current_params = params.copy() if params else {}
        current_params['page'] = page
        current_params['per_page'] = 100

        response = requests.get(url, headers=headers, params=current_params)
        
        if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
            print("Rate limit exceeded. Waiting for 60 seconds...")
            time.sleep(60)
            continue
        elif response.status_code != 200:
            print(f"Error fetching data from {url} (Page {page}): {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        if not data:
            break

        all_data.extend(data)
        
        if len(data) < 100:
            break
        page += 1
        
    return all_data

def get_followers_logins(username, token):
    url = f"{API_URL}/users/{username}/followers"
    followers_data = get_github_data(url, token)
    if followers_data is None:
        return None
    return set(f['login'] for f in followers_data)

def save_snapshot(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(list(data), f, ensure_ascii=False, indent=4)
        print(f"Snapshot saved to {filename}")
    except IOError as e:
        print(f"Error saving snapshot to {filename}: {e}")

def load_snapshot(filename):
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Snapshot loaded from {filename}")
        return set(data)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading snapshot from {filename}: {e}")
        return None

def unfollow_user(username_to_unfollow, token):
    url = f"{API_URL}/user/following/{username_to_unfollow}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 204: 
        print(f"Successfully unfollowed {username_to_unfollow}")
        return True
    else:
        print(f"Failed to unfollow {username_to_unfollow}: {response.status_code} - {response.text}")
        if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
            print("Rate limit exceeded during unfollow. Waiting for 60 seconds...")
            time.sleep(60)
            return unfollow_user(username_to_unfollow, token) 
        elif response.status_code == 403:
            print("Permission denied. Ensure your token has 'user:follow' scope.")
        return False
    

print("\n--- Follower Identifying Started ---")
if not GITHUB_USERNAME or not GITHUB_TOKEN:
    print("Error: GITHUB_USERNAME and GITHUB_TOKEN must be set as environment variables.")
    exit(1)

print("Fetching current followers list...")
current_followers_logins = get_followers_logins(GITHUB_USERNAME, GITHUB_TOKEN)
if current_followers_logins is None:
    print("Failed to get current followers list. Cannot perform comparison or save snapshot. Exiting...")
    exit(1)

print(f"Attempting to load previous follower snapshot from '{FOLLOWER_SNAPSHOT_FILE}'...")
previous_followers_logins = load_snapshot(FOLLOWER_SNAPSHOT_FILE)

if previous_followers_logins is not None:
    print("Comparing current followers with the previous snapshot...")
    unfollowed_you = previous_followers_logins - current_followers_logins
    
    if unfollowed_you:
        print("\n--- Users who unfollowed you since last check: ---")
        for login in sorted(list(unfollowed_you)):
            print(login)
        print(f"\nTotal unfollowed: {len(unfollowed_you)}")
        auth = input("Unfollow them? (yes/no): ")
        if (auth == "yes"):
            unfollow_user(login, GITHUB_TOKEN)
    else:
        print("\nNo one has unfollowed you since the last check.")
else:
    print("\nNo valid previous follower snapshot found. This may be the first run.")
    print("The current followers list will be saved for future comparisons.")

print(f"Saving current followers list as snapshot to '{FOLLOWER_SNAPSHOT_FILE}'...")
save_snapshot(current_followers_logins, FOLLOWER_SNAPSHOT_FILE)

print("\nWe're done.")
