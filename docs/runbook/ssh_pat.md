# SSH key and GitHub PAT setup (Windows PowerShell)

This document shows recommended, minimal steps to configure SSH and/or a Personal Access Token (PAT) for pushing to GitHub from Windows PowerShell.

1) Generate an SSH key (recommended)

Open PowerShell and run:

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept the default path when prompted (typically C:\Users\YOU\.ssh\id_ed25519)
# Optionally set a passphrase (recommended) or leave empty for no passphrase.
```

Add the SSH key to the ssh-agent (start agent if not running):

```powershell
Start-Service ssh-agent
Get-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

Copy the public key and add it to GitHub (Settings → SSH and GPG keys → New SSH key):

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | clip
```

Paste into the GitHub web UI and save.

Test SSH connectivity:

```powershell
ssh -T git@github.com
```

2) Create a Personal Access Token (PAT) for HTTPS pushes (alternative to SSH)

- Go to https://github.com/settings/tokens → "Generate new token" → choose expiration and at least the `repo` scope.
- Copy the token and store it securely (e.g., Windows Credential Manager or a password manager).

Use the token for HTTPS operations when prompted for a password, or configure a credential helper:

```powershell
# Cache credentials in Windows Credential Manager
git config --global credential.helper manager-core
# Then on first push, use your GitHub username and PAT as the password.
```

3) If you prefer to switch an existing remote from HTTPS to SSH:

```powershell
# Show remotes
git remote -v
# Replace origin URL
git remote set-url origin git@github.com:Meisam84/proj2.git
```

Notes
- Use SSH if you push frequently and prefer key-based auth. Use PAT if you can't add SSH keys to your account.
- If your organization requires SSO, check GitHub settings for SSO PAT requirements.
