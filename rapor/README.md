# Cuma Günü Koli Performans Raporu

Excel toplama verisinden **karşılaştırmasız** görsel rapor ve WhatsApp özet metni üretir.

## Kullanım

```bash
# Excel dosyasını rapor/ klasörüne koyun (veya generate script içindeki yolu güncelleyin)
python3 rapor/generate_cuma_rapor.py
```

Çıktılar:

- `rapor/CUMA_GUNU_KOLİ_PERFORMANS_RAPORU.png` — görsel rapor
- `rapor/whatsapp_mesaji.txt` — WhatsApp metni
- `rapor/cuma_rapor.html` — ara HTML

## Not

Bu koşuda yalnızca Cuma verisi olduğu için önceki gün kıyası (fark / artış / düşüş) rapor ve mesaja **dahil edilmemiştir**.
