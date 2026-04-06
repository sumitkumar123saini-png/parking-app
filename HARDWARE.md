# Hardware ↔ app (full demo path)

Arduino Uno has **no Wi‑Fi**. The **complete** integration is:

**Arduino (USB)** → **laptop script** → **HTTPS** → **Railway app** → **phone browser** shows the same slot.

## 1. Deploy the web app

Set on Railway:

- `SECRET_KEY` — random long string  
- `DATABASE_URL` — from Postgres plugin  
- `OCCUPANCY_API_TOKEN` — choose a secret (or use `demo-nicmar-2026` for class demo)

## 2. Create a lot and pick `spot_id`

1. Login as admin → **Create** a lot (add **latitude/longitude** for NICMAR on the map).  
2. Note **one spot** in the grid (e.g. top-left = `spot_id` **1**).  
3. That ID must match `BRIDGE_SPOT_ID` in the bridge.

## 3. Upload firmware

Open `firmware/smart_parking_slot/smart_parking_slot.ino` in **Arduino IDE**, select **Arduino Uno**, upload.

Wiring (same as your report): HC‑SR04 **Trig→9**, **Echo→10**, **Red LED→7**, **Green→6**, common GND, 220 Ω on LEDs.

## 4. Run the bridge on the laptop

```bash
pip install -r requirements-hardware.txt
copy bridge.env.sample bridge.env
# Edit bridge.env: BASE_URL, SPOT_ID, TOKEN, COM port
python scripts/serial_bridge.py
```

Keep the USB cable connected. When the sensor sees a car (distance &lt; 15 cm), the app marks that **spot occupied**; when clear, **empty**.

## 5. Phone

Open your Railway URL, login as a **normal user** — the lot grid should match the sensor (unless someone has **booked** that spot: then API returns 409 and the bridge logs it; that is correct).

## Later: Wi‑Fi without a laptop

Replace Uno with **ESP8266/ESP32** and `POST` the same JSON to `/api/spot/<id>/status` from the chip — same token header.
