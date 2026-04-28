# Libraries

import os
import sys
import json
import time
import argparse

try:
    import requests
except ImportError:
    raise ImportError("\"requests\" library is required. Install it with: pip install requests")

try:
    import yaml
except ImportError:
    yaml = None

# Metadata/Configurations

GITHUB_API_URL = "https://api.github.com"
CONFIG_FILE_NAME = "metadata.yaml"
DEFAULT_FOLLOWERS_FILE = "followers.json"
DEFAULT_CHECK_INTERVAL_HOURS = 6

# Helper Functions

def load_config():
    config = {
        "username": None,
        "token": None,
        "check_interval_hours": DEFAULT_CHECK_INTERVAL_HOURS,
        "followers_file": DEFAULT_FOLLOWERS_FILE,
        "auto_unfollow_non_followers": False
    }

    username_env = os.environ.get("GITHUB_USERNAME")
    token_env = os.environ.get("GITHUB_TOKEN")
    if username_env and token_env and username_env.strip() and token_env.strip():
        config["username"] = username_env.strip()
        config["token"] = token_env.strip()
        return config

    if os.path.exists(CONFIG_FILE_NAME):
        if yaml is None:
            print("PyYAML is required to read metadata.yaml. Install it with: pip install pyyaml")
            sys.exit(1)
        with open(CONFIG_FILE_NAME, "r") as f:
            data = yaml.safe_load(f)
            if data and "github" in data:
                github_cfg = data["github"]
                config["username"] = github_cfg.get("username")
                config["token"] = github_cfg.get("token")
            if data and "settings" in data:
                settings = data["settings"]
                if "check_interval_hours" in settings:
                    config["check_interval_hours"] = settings["check_interval_hours"]
                if "followers_file" in settings:
                    config["followers_file"] = settings["followers_file"]
                if "auto_unfollow_non_followers" in settings:
                    config["auto_unfollow_non_followers"] = settings["auto_unfollow_non_followers"]

    if not config["username"] or not config["token"]:
        print("GitHub credentials not found. Set GITHUB_USERNAME and GITHUB_TOKEN environment variables or create metadata.yaml")
        sys.exit(1)
    return config

def make_github_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def handle_rate_limit(response):
    if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
        if int(response.headers["X-RateLimit-Remaining"]) == 0:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            sleep_duration = max(reset_time - int(time.time()), 1) + 5
            print(f"Rate limit exceeded. Sleeping for {sleep_duration} seconds.")
            time.sleep(sleep_duration)
            return True
    return False

def github_get_paginated(url, headers):
    results = []
    while url:
        response = requests.get(url, headers=headers)
        if handle_rate_limit(response):
            continue
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            break
        results.extend(response.json())
        url = None
        if "Link" in response.headers:
            links = response.headers["Link"].split(",")
            for link in links:
                if 'rel="next"' in link:
                    url = link.split(";")[0].strip("<> ")
                    break
    return results

def get_followers(username, headers):
    url = f"{GITHUB_API_URL}/users/{username}/followers"
    return github_get_paginated(url, headers)

def get_following(username, headers):
    url = f"{GITHUB_API_URL}/users/{username}/following"
    return github_get_paginated(url, headers)

def unfollow_user(username, headers):
    url = f"{GITHUB_API_URL}/user/following/{username}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return True
    if response.status_code == 404:
        return False
    if handle_rate_limit(response):
        return unfollow_user(username, headers)
    return False

def load_previous_followers(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

def save_current_followers(filepath, followers):
    with open(filepath, "w") as f:
        json.dump(followers, f, indent=2)

def track_unfollowers(current_followers, config):
    followers_file = config["followers_file"]
    previous = load_previous_followers(followers_file)
    current_logins = {f["login"] for f in current_followers}
    previous_logins = {f["login"] for f in previous}

    unfollowers = previous_logins - current_logins
    new_followers = current_logins - previous_logins

    if unfollowers:
        print("Users who unfollowed you:")
        for user in unfollowers:
            print(f"  - {user}")
    else:
        print("No one unfollowed you since last check.")

    if new_followers:
        print("New followers:")
        for user in new_followers:
            print(f"  + {user}")

    save_current_followers(followers_file, current_followers)
    return unfollowers, new_followers

def unfollow_non_followers(username, headers, interactive=True):
    followers = {f["login"] for f in get_followers(username, headers)}
    following = get_following(username, headers)
    non_mutual = [user for user in following if user["login"] not in followers]

    if not non_mutual:
        print("All followed users follow you back.")
        return

    print(f"Found {len(non_mutual)} users you follow who don't follow you back:")
    for user in non_mutual:
        print(f"  - {user['login']}")

    if interactive:
        answer = input("Do you want to unfollow them? (y/N): ").strip().lower()
        if answer != 'y':
            print("Unfollow cancelled.")
            return

    for user in non_mutual:
        success = unfollow_user(user["login"], headers)
        status = "unfollowed" if success else "failed"
        print(f"  {user['login']}: {status}")

def daemon_loop(config):
    username = config["username"]
    token = config["token"]
    headers = make_github_headers(token)
    interval = config["check_interval_hours"] * 3600
    auto_unfollow = config["auto_unfollow_non_followers"]

    print(f"Daemon started. Checking every {config['check_interval_hours']} hour(s).")
    while True:
        print(f"\n--- Check at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        current_followers = get_followers(username, headers)
        track_unfollowers(current_followers, config)
        if auto_unfollow:
            unfollow_non_followers(username, headers, interactive=False)
        else:
            print("Auto-unfollow is disabled. Skipping unfollow step.")
        time.sleep(interval)

# Main Function

def main():
    parser = argparse.ArgumentParser(description="GitHub Follow Manager")
    parser.add_argument("--unfollow", action="store_true", help="Unfollow users who don't follow you back (interactive)")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background")
    args = parser.parse_args()

    config = load_config()
    username = config["username"]
    token = config["token"]
    headers = make_github_headers(token)

    if args.daemon:
        daemon_loop(config)
        return

    print(f"Checking followers and following for {username}...\n")
    current_followers = get_followers(username, headers)
    track_unfollowers(current_followers, config)

    if args.unfollow:
        unfollow_non_followers(username, headers, interactive=True)
    else:
        print("\nTo also unfollow non-mutual users, run with --unfollow flag.")

if __name__ == "__main__":
    main()
