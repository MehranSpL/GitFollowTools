import requests
import os
import json
import math
import random
import time

# --- Configuration ---
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_LIMIT = int(os.environ.get("GITHUB_LIMIT", "1000")) 
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

def get_user_info(username, token):
    url = f"{API_URL}/users/{username}"
    response = requests.get(url, headers={"Authorization": f"token {token}"})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user info for {username}: {response.status_code} - {response.text}")
        return None

def get_following_subset(username, token, limit):
    user_info = get_user_info(username, token)
    if not user_info:
        return None
    
    total_following = user_info.get('following', 0)
    if total_following == 0:
        print(f"{username} is not following anyone.")
        return []

    items_per_page = 100
    total_pages = math.ceil(total_following / items_per_page)
    
    pages_to_fetch_count = min(math.ceil(limit / items_per_page), total_pages)

    if pages_to_fetch_count <= 0:
        return []

    random_pages = set()
    while len(random_pages) < pages_to_fetch_count:
        rand_page = random.randint(1, total_pages)
        random_pages.add(rand_page)
    
    following_users_data = []
    for page_num in sorted(list(random_pages)):
        url = f"{API_URL}/users/{username}/following"
        page_data = get_github_data(url, token, params={'page': page_num, 'per_page': items_per_page})
        if page_data is None:
            continue 
        following_users_data.extend(page_data)
        
    return following_users_data[:limit]

def get_followers_logins(username, token):
    url = f"{API_URL}/users/{username}/followers"
    followers_data = get_github_data(url, token)
    if followers_data is None:
        return None
    return set(f['login'] for f in followers_data)

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

print("\n--- Identifying those who not following back ---")
if not GITHUB_USERNAME or not GITHUB_TOKEN:
    print("Error: GITHUB_USERNAME and GITHUB_TOKEN must be set as environment variables.")
    exit(1)

print(f"Fetching a subset of users you are following (up to {GITHUB_LIMIT})...")
current_following_logins_data = get_following_subset(GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_LIMIT)
if current_following_logins_data is None:
    print("Failed to get current following list. Exiting...")
    exit(1)
current_following_logins = {user['login'] for user in current_following_logins_data}

print("Fetching your current followers list...")
current_followers_logins = get_followers_logins(GITHUB_USERNAME, GITHUB_TOKEN)
if current_followers_logins is None:
    print("Failed to get current followers list. Cannot identify non-followers. Exiting...")
    exit(1)

non_followers_you_follow = current_following_logins - current_followers_logins

non_followers_to_unfollow = []
if non_followers_you_follow:
    print(f"\n--- Users you follow who do not follow you back ({len(non_followers_you_follow)} found): ---")
    non_followers_list_shuffled = list(non_followers_you_follow)
    random.shuffle(non_followers_list_shuffled)
    
    for login in non_followers_list_shuffled:
        print(f"- {login}")
        non_followers_to_unfollow.append(login)

    print("\nDo you want to unfollow these users? (yes/no)")
    
    confirmation = input("Enter 'yes' to proceed with unfollowing, or 'no' to skip: ").lower().strip()
    
    if confirmation == 'yes':
        print("\nInitiating unfollow process...")
        unfollowed_count = 0
        for login_to_unfollow in non_followers_to_unfollow:
            if unfollow_user(login_to_unfollow, GITHUB_TOKEN):
                unfollowed_count += 1
            time.sleep(1)
        print(f"\nFinished unfollow process. Successfully unfollowed {unfollowed_count} users.")
    else:
        print("\nUnfollow action cancelled by user. No one was unfollowed.")
        
else:
    print("\nAll users you are following also follow you back (within the fetched limit), or an error occurred.")

print("\nWe're done.")
