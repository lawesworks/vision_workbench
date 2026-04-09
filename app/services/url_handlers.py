import httpx
import imghdr
from urllib.parse import urlparse
from pathlib import Path


# -- Local Imports --



def download_image(url: str, dest_dir: Path, uid: str, max_bytes: int = 15 * 1024 * 1024) -> Path:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    parsed = urlparse(url)
    headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

    tmp_path = dest_dir / f"{uid}.download"

    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            total = 0
            with tmp_path.open("wb") as f:
                for chunk in r.iter_bytes():
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError(f"File too large (> {max_bytes} bytes).")
                    f.write(chunk)

    # detect image type by bytes (sniff the file)
    head = tmp_path.read_bytes()[:4096]
    kind = imghdr.what(None, h=head)
    if kind is None:
        tmp_path.unlink(missing_ok=True)
        raise ValueError("URL did not return a recognizable image.")

    final_path = dest_dir / f"{uid}.{kind}"
    tmp_path.rename(final_path)
    return final_path
