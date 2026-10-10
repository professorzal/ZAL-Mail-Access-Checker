<div align="center">

# ZAL Mail Access Checker + Inboxer

**IMAP credential checker with service detection**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![No Deps](https://img.shields.io/badge/dependencies-none-green.svg)]()

<br>

<a href="https://t.me/mr_crkz">
  <img src="https://img.shields.io/badge/owner-%40mr__crkz-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="owner">
</a>
<a href="https://t.me/professor_zal_projects">
  <img src="https://img.shields.io/badge/channel-professor__zal__projects-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="channel">
</a>

</div>

---

## overview

Multi-threaded IMAP checker. Logs into mailboxes with email:password combos,
detects which online services the mailbox is registered to by scanning
inbox bodies for service fingerprints, and sorts the output.

Written in pure Python — no external dependencies.

---

## features

- **IMAP login check** — SSL, port 993, per-provider host detection
- **Auto host detection** — `imap.<domain>` → `mail.<domain>` → `imap-mail.<domain>` → `<domain>`
- **Service detection** — 60+ services fingerprinted (Steam, Netflix, PayPal, Discord, Spotify, crypto exchanges, VPNs, games, social, and more)
- **Search word filter** — scan only for messages containing a keyword, or scan the whole inbox
- **Live console** — service hit counter, progress bar, ETA, throughput
- **Two output files** — `Hits.txt` (login-only) and `Good.txt` (login + detected service)
- **Configurable threads** — 1 to whatever your machine can handle

---

## detected services

| category | services |
|----------|----------|
| gaming | PlayStation, Steam, Xbox, Nintendo, EpicGames, Riot, Roblox, Ubisoft, EA, BattleNet, GOG |
| streaming | Netflix, Spotify, Disney+, Hulu, HBO, Prime Video, Crunchyroll |
| social | Discord, Instagram, Facebook, TikTok, Twitter, Snapchat, Reddit, Pinterest, LinkedIn, Telegram |
| shopping | Amazon, eBay, AliExpress, Etsy, Walmart |
| finance | PayPal, Wise, Revolut |
| crypto | Binance, Coinbase, MetaMask, TrustWallet, Kraken, KuCoin, OKX |
| VPN | NordVPN, ExpressVPN, Surfshark |
| cloud / dev | Cloudflare, Namecheap, GoDaddy, DigitalOcean |
| mail / ID | Yahoo, Outlook, ProtonMail, Zoho, Apple, Google |

---

## install

```bash
git clone https://github.com/professorzal/zal-mail-checker.git
cd zal-mail-checker
```

no dependencies. python 3.8+.

---

## usage

```bash
python checker.py
```

interactive prompts:

```
  txt file path: combo.txt
  search word (empty = all): netflix
  threads: 100
```

### combo file format

one `email:password` per line. lines without `:` are skipped.

```
MIX MAILs
leticia@alyarte.es:Bergantin33
w.escobar@markadistribuidora.com:Wescobar123!
ortizgutierrez.jorge@cogitiar.es:Apolo1313
encarnacion@mercadodelaencarnacion.es:8h5LL9fN1
manuel@drbrandfactory.es:Manuel159753
lagigantadigital@lagigantadigital.es:gig@nt@2017
llevatelacamisetadevacaciones@jaenrugby.es:ahvuxVXk9SaiT9_
```

---

## output

everything is written to `Results/`.

**`Results/Hits.txt`** — mailbox opened, no service matched
```
user@example.com:password
```

**`Results/Good.txt`** — mailbox opened + one or more services detected
```
user@example.com:password | service:Netflix
user@example.com:password | service:Spotify
```

---

## how it works

1. **host detection** — for each combo, resolve the domain against `imap.<domain>`, `mail.<domain>`, `imap-mail.<domain>`, then bare `<domain>`. first one that resolves wins. cached per-domain.
2. **login** — `IMAP4_SSL` on port 993, timeout 15s.
3. **select inbox** — if `SELECT INBOX` fails, marked bad.
4. **search** — if a search word is set, `SEARCH BODY "<word>"`. otherwise `SEARCH ALL`.
5. **scan** — for each message id, fetch `RFC822`, decode, and run `match_service()` to score against the fingerprint table. highest-scoring service is recorded.
6. **write** — every successful login appends to `Hits.txt`. every detected service appends a line to `Good.txt`.

---

## notes

- some providers (Gmail with 2FA, Microsoft with modern auth) reject plain IMAP passwords. those accounts need app-specific passwords.
- detection is body-text based — it catches what's actually in the inbox, not what's on the account page. so a mailbox that only receives promotional mail from Netflix will detect as Netflix.
- threads are unlimited by default. on `gmail.com` and `outlook.com` keep it under 20-30 or you'll hit rate limits.

---

## license

MIT — see [LICENSE](LICENSE)
