# Security model

- Secrets are environment variables only.
- Telegram actions are restricted to TELEGRAM_ADMIN_ID.
- Auto-apply is disabled by default.
- Sensitive recruiter/client topics require approval.
- No credential, cookie, CAPTCHA or 2FA bypass is implemented.
- LinkedIn/Upwork scraping is intentionally not implemented.
- Do not place `.env`, OAuth tokens, Telegram tokens or database files in Git.
- Rotate the Telegram bot token because it was previously exposed in chat.
