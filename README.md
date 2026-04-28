# GitHub Unfollower Checker

This script helps you identify users who have unfollowed you on GitHub since your last check. It works by comparing your current followers list with a saved snapshot of your followers from a previous run.

## Features

- **Flexible Credential Management**  
  Provide your GitHub credentials via environment variables (`GITHUB_USERNAME` / `GITHUB_TOKEN`) or a YAML configuration file (`metadata.yaml`). Environment variables take precedence if both are available.

- **Snapshot‑Based Unfollower Detection**  
  Compares your current followers against a previously saved snapshot to show who stopped following you since the last check. Each run updates the snapshot automatically.

- **Graceful First Run**  
  On the first execution no snapshot exists yet. The script saves the initial follower list and informs you that future runs will be able to detect changes.

- **Mutual Follow Check & Unfollow**  
  Shows all users you follow who do **not** follow you back.  
  With the `--unfollow` flag you can interactively confirm and unfollow them.  
  In daemon mode, you can enable **automatic unfollowing** without any prompts.

- **Daemon Mode** (`--daemon`)  
  Run the script continuously in the background. It checks at a configurable interval (default: 6 hours) and automatically tracks unfollowers. Combine with `auto_unfollow_non_followers` to silently remove non‑mutual follows.

- **Configurable Settings**  
  Through the `metadata.yaml` file you can adjust:
  - Check interval (hours)
  - Snapshot file name
  - Automatic unfollow behavior

- **Rate Limit Handling**  
  Detects GitHub API rate‑limit exhaustion (HTTP 403) and pauses until the limit resets, preventing crashes and respecting GitHub’s thresholds.

- **Resilient Error Messages**  
  Missing dependencies or incorrect credentials produce clear, actionable messages instead of cryptic stack traces.

- **Single‑File & Lightweight**  
  Everything is contained in one Python script – easy to review, modify, and run.

## Prerequisites

- **Python 3.6+**  
  Verify with:
  ```bash
  python3 --version
  ```

- **`requests` library** (mandatory)  
  ```bash
  pip install requests
  ```

- **`pyyaml` library** (optional – only if using a YAML config file)  
  ```bash
  pip install pyyaml
  ```

- **GitHub Personal Access Token**  
  Create a token at [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens).  
  Required scope: `read:user` (for followers/following). If you plan to unfollow users automatically, also add `user:follow`.  
  **Keep your token secret!**

## Setup

Choose **one** of the following methods to provide your credentials.

### Method A: Environment Variables

```bash
# Linux / macOS
export GITHUB_USERNAME="your_username"
export GITHUB_TOKEN="ghp_your_token_here"
```

```cmd
REM Windows Command Prompt
set GITHUB_USERNAME=your_username
set GITHUB_TOKEN=ghp_your_token_here
```

These are detected automatically when the script runs.

### Method B: YAML Configuration File

1. Install `pyyaml` if you haven’t:
   ```bash
   pip install pyyaml
   ```
2. Create a file named `metadata.yaml` in the same folder as the script with the following structure:

   ```yaml
   github:
     username: YOUR_USERNAME
     token: ghp_YOUR_TOKEN

   settings:                          # optional – defaults shown below
     check_interval_hours: 6          # how often the daemon checks
     followers_file: followers.json   # where to store the snapshot
     auto_unfollow_non_followers: false  # set to true for automatic unfollow in daemon
   ```

> **Note:** If both environment variables and the YAML file exist, environment variables are used first.

## Usage

Run the script from the terminal:

```bash
python3 GithubFollowUnfollow.py [OPTIONS]
```

### Available Options

| Flag           | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| (no flag)      | Check for unfollowers and save a new snapshot. Show new followers.          |
| `--unfollow`   | After the check, interactively ask to unfollow users who don’t follow back. |
| `--daemon`     | Run continuously, checking every X hours (configured in settings).          |
| `--help`       | Display the help message and exit.                                          |

### Examples

1. **One‑time check**  
   ```bash
   python3 GithubFollowTools.py
   ```

2. **Check and interactively unfollow non‑mutual users**  
   ```bash
   python3 GithubFollowTools.py --unfollow
   ```

3. **Start daemon with 6‑hour checks (default)**  
   ```bash
   python3 GithubFollowTools.py --daemon
   ```
   The daemon will output a line each time it runs a check. Stop it with `Ctrl+C`.

4. **Daemon with automatic unfollow**  
   First set `auto_unfollow_non_followers: true` in your `metadata.yaml`, then:
   ```bash
   python3 GithubFollowTools.py --daemon
   ```
   Non‑mutual follows will be unfollowed automatically without any prompts.

## Configuration Reference (`metadata.yaml`)

```yaml
github:
  username: "your_github_username"   # string, required if not in env
  token: "ghp_xxxxxxxxxxxx"          # string, required if not in env

settings:
  check_interval_hours: 6            # positive number, default 6
  followers_file: "followers.json"   # file path, default "followers.json"
  auto_unfollow_non_followers: false # boolean, default false
```

- `github.username` / `github.token` – GitHub credentials.  
- `check_interval_hours` – how many hours the daemon waits between checks.  
- `followers_file` – name (or path) of the JSON file used to store the follower snapshot.  
- `auto_unfollow_non_followers` – if `true`, the daemon will unfollow anyone who doesn’t follow you back without asking. Only applies in daemon mode.

## Important Notes

- **Token Security**: Never commit your `metadata.yaml` file (or any file containing your token) to a public repository. Add it to your `.gitignore` file.
- **Rate Limits**: GitHub imposes API rate limits. The script pauses automatically when limits are reached.
- **First Run**: No snapshot exists initially, so no unfollowers will be reported. The snapshot is created after the first run.
- **Permissions**: To unfollow users, your token needs the `user:follow` scope. Without it, the unfollow operation will fail with a permission error.

## Breakdown

-   **Script contains 2 main files:**
-   -> `GithubFollowUnfollow.py`
-   -> `GithubUnfollowNotify.py`

### GithubFollowUnfollow.py:

- This script focuses on checking who you follow and checks if they're following back or not
- If they're not, a prompt will appear asking you about your opinion in unfollowing them.
- If you say yes, it will automatically unfollow them.
- If you say no, the operation will get canceled.

### GithubUnfollowNotify.py:

- This is more professional
- In the first run, it retrieves your followers and saves them to a file called `Followers.json`
- If the file exists already, or you run it again at another time, it compares the list with your current GitHub followers.
- Then if anyone from the local list was missing in current GitHub follower list, a prompt will appear
- It asks your opinion on unfollowing those who have unfollowed you, if you were following them, and say yes, it will automatically unfollow them.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue if you have any suggestions or find any bugs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
