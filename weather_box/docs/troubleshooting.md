# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No `/dev/cu.usbmodem*` port | The board is in deep sleep, and USB is off while it sleeps | Hold B, tap R, then release B for download mode. The buttons are tiny, at the USB-C end of the XIAO; press them with a fingernail or a wooden toothpick, never metal |
| Board gets a 404 and sleeps 60 min | Old firmware still points at the deleted Worker URL | Re-flash. **Re-flash every XIAO after the Worker URL changes**; the spare XIAO may still need it |
| The log looks fine (data fetched, `Sleeping`) but the screen doesn't change | The **ribbon cable has come loose**. It fails silently, with no error | Run `hello_4in26` to confirm. Then, with USB unplugged, flip the latch up, reseat the ribbon straight and fully, press the latch down, and press the XIAO firmly into its socket |
| The port is present but there's no log and the board never sleeps | The board hung partway through a cycle | Tap R |
| Values seem stale | The Worker's KV cache lasts 30 min | Wait, or check the endpoint with curl |
