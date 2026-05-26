from pylsl import StreamInlet, resolve_byprop

print("Looking for LIFUEvents...")
streams = resolve_byprop('name', 'LIFUEvents', timeout=5)
if not streams:
    print("No LIFUEvents stream found.")
    exit()

inlet = StreamInlet(streams[0])
print("Connected. Listening...")

while True:
    sample, ts = inlet.pull_sample(timeout=1.0)
    if sample:
        print("RECEIVED:", sample[0], "at", ts)
