# SSH key and Personal Access Token (PAT) setup (Windows PowerShell)

This short guide shows recommended commands to set up SSH keys and/or a GitHub Personal Access Token (PAT) for HTTPS pushes on Windows PowerShell.

1) Generate an SSH keypair (recommended)

Open PowerShell and run:

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com" -f $env:USERPROFILE\.ssh\id_ed25519
# Press Enter to accept defaults; optionally use a passphrase for the private key.
```

Then add the public key to your GitHub account:

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | clip
# Now open https://github.com/settings/keys and paste (Title: your machine name)
```

Test the SSH connection:

```powershell
ssh -T git@github.com
```

If you see "Hi <username>! You've successfully authenticated..." then SSH is working.

2) Create a Personal Access Token (PAT) (alternative to SSH)

- Visit https://github.com/settings/tokens
- Click "Generate new token" → give it a name, expiration, and select scopes (`repo` for full repo access; `workflow` if you need to interact with Actions).
- Copy the token once and store it securely (password manager).

Use a PAT with HTTPS pushes by specifying it as the password when Git prompts, or store it in the Windows credential manager:

```powershell
# Example: set remote to use HTTPS (if not already)
git remote set-url origin https://github.com/<owner>/<repo>.git
# On next push you'll be prompted for username (use your GitHub username) and password (use the PAT)
```

3) Helpful tips
- Use `ssh-agent` to cache your passphrase:

```powershell
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

- To avoid being prompted repeatedly with HTTPS, use the Windows Credential Manager or the Git Credential Manager (recommended).

If you want, I can automatically create a small checklist file in the repo or attempt to generate keys here (but adding the public key to GitHub requires you to paste it into your account settings).
