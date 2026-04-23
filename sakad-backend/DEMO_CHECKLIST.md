# Sakkad Demo Checklist

## Night Before
- [ ] Charge Mac fully
- [ ] Confirm VPN is installed and working (`ExpressVPN`, `NordVPN`, etc.)
- [ ] Test VPN + ngrok from home: `curl -s https://<ngrok-url>/api/health -H "ngrok-skip-browser-warning: true"`
- [ ] Confirm Gabe has latest frontend pointing to a placeholder URL (he just needs to swap one string)
- [ ] Clean git — remove agent briefs, AI prompt artifacts, commit `chore: remove dev artifacts`
- [ ] Know your USC wifi login credentials (no CUJO on campus = no VPN needed)

---

## Demo Day — Before You Leave Home
- [ ] Mac charged
- [ ] VPN ready (only needed if presenting from home)
- [ ] Know where `sakad-backend/` lives: `~/Desktop/XR_Fashion/sakkad/sakad-backend`

---

## Demo Day — On Location (30 min before)

### 1. Start the backend
```bash
cd ~/Desktop/XR_Fashion/sakkad/sakad-backend
uvicorn main:app --reload
```
> Keep this terminal open the entire demo.

### 2. Start ngrok (new terminal)
```bash
ngrok http 8000
```
> Copy the `https://` URL from the output.

### OR — run both automatically:
```bash
cd ~/Desktop/XR_Fashion/sakkad/sakad-backend
bash demo_start.sh
```

### 3. Send Gabe the URL immediately
```
https://<your-ngrok-url>
Header: ngrok-skip-browser-warning: true
```

### 4. Warm up the model (do this yourself first)
```bash
cd ~/Desktop/XR_Fashion/sakkad/sakad-backend
curl -s -X POST http://localhost:8000/api/capture \
  -F "file=@test-images/western.jpg" | python3 -m json.tool
```
> First call takes 30–60s. After that it's fast. Do NOT let the first live capture be Gabe's.

### 5. Verify ngrok end-to-end
```bash
curl -s https://<ngrok-url>/api/health \
  -H "ngrok-skip-browser-warning: true" | python3 -m json.tool
```
> Expect `"status": "ok"` and `"model_loaded": true` after warmup.

### 6. Test reflection (sanity check)
```bash
curl -s https://<ngrok-url>/api/sessions/05339b8a-7aaa-4fcd-97ca-f6ce45e0ae42/reflection \
  -H "ngrok-skip-browser-warning: true" | python3 -m json.tool
```
> Should return the abstract session reflection with designer names.

### 7. Confirm with Gabe
- [ ] Gabe has swapped the URL into Lens Studio
- [ ] Gabe does a test capture from Spectacles → confirm it hits your uvicorn logs
- [ ] Reflection text renders in frontend after spatial gallery

---

## During Demo
- [ ] Both terminals stay open (uvicorn + ngrok)
- [ ] If ngrok URL dies → restart ngrok, get new URL, reshare with Gabe immediately
- [ ] If model is slow on first live capture → expected, just narrate it loading
- [ ] If Gemini 503s → retry once, they self-resolve

---

## Strong Demo Moments to Hit
| Capture | Expected Result |
|---|---|
| `western.jpg` | Cowboy Core 0.9673, Ralph Lauren reference |
| `leaf.jpg` | Botanical Organic 0.8498 |
| Abstract session reflection | Rick Owens, Margiela, Iris van Herpen |
| Fashion session reflection | Helmut Lang, Raf Simons |

---

## Emergency Fallbacks
| Problem | Fix |
|---|---|
| ngrok blocked (CUJO) | Connect Mac to phone hotspot OR use USC wifi |
| Model won't load | Restart uvicorn, hit `/api/capture` locally first |
| Gemini 503 | Wait 10s, retry — transient rate limit |
| ngrok URL changed | Grab new URL from `http://127.0.0.1:4040`, reshare |
| Frontend not rendering | Check Gabe has `taxonomy_matches` as `Record<string, number>` not array |
