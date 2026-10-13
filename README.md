# Quiet Analytics

**Count your visitors without cookies, without a third party, and without ever writing down who
they were.** Your web server already logs every request. This changes *what* it logs, so the record
was never sensitive in the first place, and summarises it once a night.

No JavaScript. No cookies. No database. No daemon. No vendor. No account. Nothing to pay for.

---

## Why this exists

Site owners who do not want trackers have three poor options: pay a vendor and still send visitor
data off your server; self-host an analytics application and maintain it forever; or measure
nothing. There is a fourth, and it needs about forty lines of nginx configuration.

The useful part is **where the masking happens**. Most privacy-respecting tools anonymise after
collection — the full address is written, then cleaned up later. Here nginx replaces the address
*before serialization*. There is no moment at which the full address exists in a log file, so
there is no window, no stray copy, and no cleanup step to get wrong.

## What is written down

| Kept | Not kept |
|---|---|
| Network group — IPv4 masked to /24, IPv6 to /48 | The visitor's actual address |
| The page, chosen from a list you write | Any path you did not list (becomes `/other`) |
| Referring **domain**, e.g. `https://example.org/` | The referrer's path or query string |
| Method, protocol, time, status, bytes | Query strings, user agents, usernames, cookies |

A path you have not listed cannot enter the log, so a URL that happens to carry a name, a token or
a search term is grouped away as `/other` rather than recorded.

## What it does not do

It is not a dashboard, a service, or a product anyone hosts for you. There is no live view, no
real-time counter, no hosted component, and no URL where the report is served. The report is a
static HTML file written nightly to a root-only directory; copy it to your own machine to read it.

Nothing here is sent to us. We cannot see your site, your logs, or your report, and we do not know
you are using this.

## Install

Needs nginx and `goaccess` (Ubuntu/Debian: `apt install goaccess`).

```sh
git clone https://github.com/OhanaCodes/quiet-analytics.git
cd quiet-analytics
sudo bin/install.sh
```

Then two edits that are deliberately yours to make:

1. **List your pages** — `/etc/nginx/conf.d/00-quiet-analytics.conf`, section 3.
2. **Point your site at the format** — add the two lines from `nginx/server-block.example.conf`
   inside your `server { }` block.

```sh
sudo nginx -t && sudo systemctl reload nginx
python3 tests/test-masking.py      # prove the masking before trusting it
```

The nightly report lands at `/var/lib/quiet-analytics/report.html` (mode 0600 in a 0700 directory).
Read it by copying it to your own machine:

```sh
scp root@YOUR-SERVER:/var/lib/quiet-analytics/report.html ~/Downloads/report.html
```

`bin/install.sh` installs files only. It does not edit your `server { }` block, because a script
that rewrites a stranger's nginx configuration is a worse idea than two lines of copy-paste.

## The test is the point

Anyone can claim their analytics is private. `tests/test-masking.py` starts an isolated nginx on
loopback using this repository's own map file, drives 109 synthetic addresses through it —
compressed IPv6, expanded IPv6, IPv4-mapped IPv6, plain IPv4, 100 random addresses — and asserts
that what would be logged is the masked network, that an unlisted path is grouped away, and that a
referrer is reduced to its domain. Run it after you edit the configuration, not just before.

## Caveats, stated plainly

- **"Masked", not "anonymous".** A /24 or /48 network group is much weaker evidence than a full
  address, but it is still data about a visit. `PRIVACY-SNIPPET.md` has wording that does not
  overclaim.
- **nginx error logs cannot use a custom format.** The example sends this site's error output to
  `/dev/null` so it cannot record full addresses; HTTP status counts remain in the access log. Keep
  the errors instead if you would rather have the diagnostics — but then the promise is narrower.
- **Behind a CDN or proxy**, `$remote_addr` is the proxy. Configure nginx's real_ip module so the
  masking applies to the true peer; the maps deliberately never read a client-supplied header.
- **GoAccess reads a COMBINED-shaped line.** The format mimics it so ordinary tools work, but the
  fields have already been replaced.
- One shared log per server block. Two sites, two blocks, two logs.

## Where it came from

Written for [Living Life Data](https://livinglifedata.org), a public record of everyday movement
that promises no third-party code on any page. It has been running since September 2026. Published
because the problem is common and the answer turned out to be small.

MIT licensed. Issues and pull requests welcome; no promises about response time.
