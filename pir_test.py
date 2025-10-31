from gpiozero import MotionSensor
from time import sleep, time

pir = MotionSensor(17, queue_len=1, sample_rate=50, threshold=0.5)  # raw-ish
last = pir.value
print("Warming up…")
sleep(2)
print("Ready. Move ACROSS the sensor's view, ~2–4m away.")
while True:
    v = pir.value  # 0.0 or 1.0 for HC-SR501-type PIRs
    if v != last:
        print(f"{time():.0f}: state -> {int(v)}")
        last = v
    sleep(0.05)
