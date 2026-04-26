# GitHub Unfollower Checker

This script helps you identify users who have unfollowed you on GitHub since your last check. It works by comparing your current followers list with a saved snapshot of your followers from a previous run.

## Features

-   **Detects Unfollowers**: Identifies users who have stopped following you.
-   **Snapshot Management**: Automatically saves and loads a snapshot of your followers list to ensure accurate comparisons over time.
-   **Handles First Run**: Gracefully handles the initial run by saving the current followers as the first snapshot.
-   **Rate Limit Awareness**: Includes basic handling for GitHub API rate limiting by pausing execution.

## Prerequisites

-   **Python 3**: Ensure you have Python 3 installed on your system.
-   **`requests` library**: Install it using pip:
    ```bash
    pip install requests
    ```
-   **GitHub Personal Access Token**: You need a GitHub Personal Access Token with the `read:user` scope. You can generate one here: [GitHub Personal Access Tokens](https://github.com/settings/tokens)
-   **Environment Variables**: Set the following environment variables before running the script:
    -   `GITHUB_USERNAME`: Your GitHub username.
    -   `GITHUB_TOKEN`: Your GitHub Personal Access Token.


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
## How to Use

1.  **Clone the repository** (if applicable) or save the script as a Python file.
2.  **Set environment variables**:
    *   **Linux/macOS**:
        ```bash
        export GITHUB_USERNAME="your_github_username"
        export GITHUB_TOKEN="your_github_personal_access_token"
        ```
    *   **Windows (Command Prompt)**:
        ```cmd
        set GITHUB_USERNAME=your_github_username
        set GITHUB_TOKEN=your_github_personal_access_token
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        $env:GITHUB_USERNAME="your_github_username"
        $env:GITHUB_TOKEN="your_github_personal_access_token"
        ```
3.  **Run the script**:
    ```bash
    python GithubFollowUnfollow.py
    python GithubUnfollowNotify.py
    ```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue if you have any suggestions or find any bugs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
