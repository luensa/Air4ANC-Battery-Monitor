#!/usr/bin/env python3
"""Cuma günü koli performans raporu — karşılaştırmasız görsel + WhatsApp metni."""

from __future__ import annotations

import html
import subprocess
from pathlib import Path

import pandas as pd

EXCEL = Path(__file__).parent / "Kullanici_toplama_perf_rapor__1_-1_e7c6.xlsx"
OUT_DIR = Path(__file__).parent
ARTIFACTS = Path("/opt/cursor/artifacts")
HTML_PATH = OUT_DIR / "cuma_rapor.html"
PNG_PATH = OUT_DIR / "CUMA_GUNU_KOLİ_PERFORMANS_RAPORU.png"
WP_PATH = OUT_DIR / "whatsapp_mesaji.txt"

DEPO = "36103"
GUN_ADI = "Cuma"
GUN_TITLE = "CUMA"
MERKEZ = "ŞANLIURFA DAĞITIM MERKEZİ"

CARD_COLORS = ["#f7e8a0", "#dfe3e8", "#f5c9a0", "#c8dff0", "#d8c8e8"]


def tr_int(n: float | int) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def tr_float(n: float, digits: int = 1) -> str:
    return f"{n:.{digits}f}".replace(".", ",")


def title_name(name: str) -> str:
    # Turkish-aware simple title case for ALL CAPS names
    parts = []
    for word in name.strip().split():
        lower = word.lower()
        # Keep short connectors lowercase after first word? No — names stay title.
        parts.append(lower[:1].upper() + lower[1:] if lower else word)
    # Fix common Turkish ı/İ from uppercased source
    fixed = []
    for p in parts:
        # Source is already Turkish uppercase; pandas/openpyxl keeps İ correctly.
        # Re-title from original preserving special chars via casefold-like map
        fixed.append(p)
    # Better: use a Turkish title map from the original uppercase string
    return turkish_title(name)


def turkish_title(s: str) -> str:
    """Title-case Turkish uppercase names."""
    tr_lower = str.maketrans(
        {
            "I": "ı",
            "İ": "i",
            "Ş": "ş",
            "Ğ": "ğ",
            "Ü": "ü",
            "Ö": "ö",
            "Ç": "ç",
        }
    )
    words = []
    for w in s.strip().split():
        low = w.translate(tr_lower).lower()
        # Capitalize first letter with Turkish İ
        first = low[0]
        if first == "i":
            first = "İ"
        else:
            first = first.upper()
        words.append(first + low[1:])
    return " ".join(words)


def load_personnel() -> pd.DataFrame:
    df = pd.read_excel(EXCEL)
    df = df[df["Personel Adı"].notna()].copy()
    agg = (
        df.groupby("Personel Adı", as_index=False)
        .agg({"Toplanan Koli": "sum", "Toplama Süresi (saat)": "sum"})
        .rename(columns={"Toplanan Koli": "koli", "Toplama Süresi (saat)": "saat"})
    )
    agg["saatte"] = (agg["koli"] / agg["saat"]).round(1)
    agg = agg.sort_values("koli", ascending=False).reset_index(drop=True)
    agg["sira"] = agg.index + 1
    agg["ad"] = agg["Personel Adı"].map(turkish_title)
    return agg


def build_html(agg: pd.DataFrame) -> str:
    n = len(agg)
    toplam_koli = agg["koli"].sum()
    toplam_saat = agg["saat"].sum()
    genel_ort = toplam_koli / toplam_saat
    top5 = agg.head(5)
    rest = agg.iloc[5:]

    cards = []
    for i, row in top5.iterrows():
        bg = CARD_COLORS[int(row["sira"]) - 1]
        cards.append(
            f"""
            <div class="person-card" style="background:{bg}">
              <div class="rank-circle">{int(row['sira'])}</div>
              <div class="pname">{html.escape(row['ad'])}</div>
              <div class="pkoli">{tr_int(row['koli'])} KOLİ</div>
              <div class="psaat">SAATTE {tr_float(row['saatte'])}</div>
            </div>
            """
        )

    rows_html = []
    for idx, row in rest.iterrows():
        zebra = "even" if int(row["sira"]) % 2 == 0 else "odd"
        rows_html.append(
            f"""
            <tr class="{zebra}">
              <td class="c-sira">{int(row['sira'])}</td>
              <td class="c-ad">{html.escape(row['ad'])}</td>
              <td class="c-koli">{tr_int(row['koli'])}</td>
              <td class="c-ort">{tr_float(row['saatte'])}</td>
            </tr>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<style>
  @font-face {{
    font-family: 'NotoSans';
    src: url('file:///usr/share/fonts/truetype/noto/NotoSans-Regular.ttf') format('truetype');
    font-weight: 400;
  }}
  @font-face {{
    font-family: 'NotoSans';
    src: url('file:///usr/share/fonts/truetype/noto/NotoSans-Bold.ttf') format('truetype');
    font-weight: 700;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'NotoSans', 'DejaVu Sans', sans-serif;
    background: #e8eef5;
    color: #1a2b4b;
    width: 1100px;
  }}
  .page {{
    width: 1100px;
    background: #e8eef5;
    padding-bottom: 28px;
  }}
  .header {{
    background: #1a2b4b;
    padding: 28px 36px 32px;
    position: relative;
  }}
  .depo {{
    display: inline-block;
    background: #d61f26;
    color: #fff;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;
    padding: 6px 14px;
    border-radius: 4px;
    margin-bottom: 14px;
  }}
  .header h1 {{
    color: #fff;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 0.5px;
    line-height: 1.25;
  }}
  .header h1 .sub {{
    display: block;
    font-size: 22px;
    font-weight: 700;
    margin-top: 4px;
    opacity: 0.95;
  }}
  .kpis {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 22px;
  }}
  .kpi {{
    background: #fff;
    border-radius: 12px;
    padding: 18px 16px;
    text-align: center;
  }}
  .kpi .val {{
    font-size: 32px;
    font-weight: 700;
    color: #1a2b4b;
    line-height: 1.1;
  }}
  .kpi .lbl {{
    margin-top: 6px;
    font-size: 13px;
    font-weight: 700;
    color: #5a6a7a;
    letter-spacing: 0.3px;
  }}
  .section {{
    padding: 28px 36px 0;
  }}
  .section-title {{
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #1a2b4b;
    margin-bottom: 16px;
  }}
  .top5 {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
  }}
  .person-card {{
    border-radius: 14px;
    padding: 18px 12px 20px;
    text-align: center;
    min-height: 168px;
  }}
  .rank-circle {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #fff;
    color: #1a2b4b;
    font-weight: 700;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .pname {{
    font-weight: 700;
    font-size: 14px;
    color: #1a1a1a;
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1.25;
  }}
  .pkoli {{
    margin-top: 10px;
    font-size: 22px;
    font-weight: 700;
    color: #d61f26;
  }}
  .psaat {{
    margin-top: 6px;
    font-size: 12px;
    font-weight: 700;
    color: #6a7585;
    letter-spacing: 0.2px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    border-radius: 10px;
    overflow: hidden;
    background: #fff;
  }}
  thead th {{
    background: #1a2b4b;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.4px;
    padding: 12px 14px;
    text-align: left;
  }}
  thead th.c-sira, td.c-sira {{ text-align: center; width: 70px; }}
  thead th.c-koli, td.c-koli {{ text-align: right; width: 140px; }}
  thead th.c-ort, td.c-ort {{ text-align: right; width: 140px; }}
  tbody td {{
    padding: 11px 14px;
    font-size: 14px;
    border-bottom: 1px solid #e6ebf2;
  }}
  tr.even {{ background: #f3f6fa; }}
  tr.odd {{ background: #fff; }}
  td.c-ad {{ font-weight: 700; color: #1a2b4b; }}
  td.c-koli {{ font-weight: 700; color: #d61f26; }}
  td.c-ort {{ font-weight: 600; color: #3a4a5a; }}
  td.c-sira {{ font-weight: 700; color: #1a2b4b; }}
  .note {{
    margin: 22px 36px 0;
    background: #d7e8f7;
    border-radius: 10px;
    padding: 16px 18px;
    font-size: 13px;
    line-height: 1.55;
    color: #1a2b4b;
  }}
  .note strong {{ font-weight: 700; }}
</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div class="depo">DEPO {DEPO}</div>
      <h1>{MERKEZ}<span class="sub">{GUN_TITLE} GÜNÜ KOLİ PERFORMANS RAPORU</span></h1>
      <div class="kpis">
        <div class="kpi">
          <div class="val">{n}</div>
          <div class="lbl">PERSONEL</div>
        </div>
        <div class="kpi">
          <div class="val">{tr_int(toplam_koli)}</div>
          <div class="lbl">TOPLAM KOLİ</div>
        </div>
        <div class="kpi">
          <div class="val">{tr_float(genel_ort)}</div>
          <div class="lbl">SAATTE ORT. KOLİ</div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">EN YÜKSEK KOLİ TOPLAYAN İLK 5 PERSONEL</div>
      <div class="top5">
        {''.join(cards)}
      </div>
    </div>

    <div class="section" style="padding-top:26px;">
      <div class="section-title">GENEL TOPLAM LİSTESİ</div>
      <table>
        <thead>
          <tr>
            <th class="c-sira">SIRA</th>
            <th class="c-ad">PERSONEL ADI</th>
            <th class="c-koli">CUMA KOLİ</th>
            <th class="c-ort">SAATTE ORT.</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>

    <div class="note">
      <strong>Hesaplama notu:</strong>
      Cuma günü {n} personel toplam {tr_int(toplam_koli)} koli topladı.
      Genel ortalama saatte {tr_float(genel_ort)} koli
      (toplam koli ÷ toplam toplama süresi {tr_float(toplam_saat, 2)} saat).
      Personel saatte ortalama = personelin toplam kolisi ÷ kendi toplama süresi.
      Karşılaştırma verisi bu raporda yer almamaktadır.
    </div>
  </div>
</body>
</html>
"""


def build_whatsapp(agg: pd.DataFrame) -> str:
    n = len(agg)
    toplam_koli = agg["koli"].sum()
    toplam_saat = agg["saat"].sum()
    genel_ort = toplam_koli / toplam_saat
    top5 = agg.head(5)

    lines = [
        "Merhaba Fırat Bey,",
        "",
        "Cuma toplama özeti:",
        "",
        f"📦 {n} personel, toplam {tr_int(toplam_koli)} koli.",
        "",
        f"⏱ Genel ortalama: Saatte {tr_float(genel_ort)} koli.",
        "",
        "🏆 İlk 5:",
        "",
    ]
    for _, row in top5.iterrows():
        lines.append(f"{int(row['sira'])}. {row['ad']} – {tr_int(row['koli'])} koli")

    first = top5.iloc[0]
    second = top5.iloc[1]

    def possessive(name: str) -> str:
        last = name.rstrip()[-1].lower()
        if last in "aeıioöuü":
            return f"{name}'nın"
        return f"{name}'ın"

    lines += [
        "",
        "📝 Genel değerlendirme: "
        f"Cuma günü {n} personelle toplam {tr_int(toplam_koli)} koli toplanmış, "
        f"genel saatlik ortalama {tr_float(genel_ort)} koli olarak gerçekleşmiştir. "
        f"Özellikle {possessive(first['ad'])} {tr_int(first['koli'])} koliyle günün en yüksek "
        f"performansını göstermesi ve {possessive(second['ad'])} "
        f"{tr_int(second['koli'])} koliyle ikinci sırada yer alması öne çıkan sonuçlardır.",
        "",
        "Detaylı görsel rapor ektedir. İyi akşamlar.",
    ]
    return "\n".join(lines)


def crop_whitespace(png_path: Path) -> None:
    from PIL import Image

    rgb = Image.open(png_path).convert("RGB")
    w, h = rgb.size
    pixels = rgb.load()
    bg = (232, 238, 245)
    bottom = h - 1
    for y in range(h - 1, 0, -1):
        row_has = False
        for x in range(0, w, 4):
            p = pixels[x, y]
            if abs(p[0] - bg[0]) > 10 or abs(p[1] - bg[1]) > 10 or abs(p[2] - bg[2]) > 10:
                row_has = True
                break
        if row_has:
            bottom = min(h - 1, y + 60)
            break
    rgb.crop((0, 0, w, bottom)).save(png_path, "PNG", optimize=True)


def render_png(html_path: Path, png_path: Path) -> None:
    import time

    if png_path.exists():
        png_path.unlink()

    cmd = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--virtual-time-budget=8000",
        "--run-all-compositor-stages-before-draw",
        f"--screenshot={png_path}",
        "--window-size=1100,1800",
        "--force-device-scale-factor=2",
        f"file://{html_path}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 45
    last_size = -1
    stable = 0
    try:
        while time.time() < deadline:
            if png_path.exists():
                size = png_path.stat().st_size
                if size > 50_000 and size == last_size:
                    stable += 1
                    if stable >= 3:
                        break
                else:
                    stable = 0
                last_size = size
            time.sleep(0.4)
        else:
            if not png_path.exists() or png_path.stat().st_size < 50_000:
                raise RuntimeError("Chrome screenshot failed to produce PNG in time")
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    crop_whitespace(png_path)


def main() -> None:
    agg = load_personnel()
    HTML_PATH.write_text(build_html(agg), encoding="utf-8")
    wp = build_whatsapp(agg)
    WP_PATH.write_text(wp, encoding="utf-8")
    render_png(HTML_PATH, PNG_PATH)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out_art = ARTIFACTS / PNG_PATH.name
    out_art.write_bytes(PNG_PATH.read_bytes())
    (ARTIFACTS / "whatsapp_mesaji.txt").write_text(wp, encoding="utf-8")
    print("OK")
    print("PNG:", PNG_PATH)
    print("WP:", WP_PATH)
    print("--- WP ---")
    print(wp)


if __name__ == "__main__":
    main()
