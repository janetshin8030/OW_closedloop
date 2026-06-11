import time
from pylsl import StreamInfo, StreamOutlet
import keyboard   # pip install keyboard

def main():
    # Configure marker outlet
    info = StreamInfo(
        name='SlicerTestTrigger',
        type='Markers',
        channel_count=1,
        nominal_srate=0,
        channel_format='string',
        source_id='slicer_sim_99'
    )
    outlet = StreamOutlet(info)

    print("LSL Marker Stream live on the network.")
    print("Waiting 3 seconds for Slicer to discover the stream...")
    time.sleep(3)

    trigger_phrase = "START_SONICATION"
    print("\nPress UP ARROW to send a sonication trigger.\nPress ESC to quit.\n")

    try:
        while True:
            # If UP ARROW is pressed → send trigger
            if keyboard.is_pressed("up"):
                print(f"Sending marker: '{trigger_phrase}'")
                outlet.push_sample([trigger_phrase])
                time.sleep(0.2)  # debounce so holding the key doesn't spam

            # Exit cleanly
            if keyboard.is_pressed("esc"):
                print("Exiting...")
                break

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Interrupted by user.")

if __name__ == "__main__":
    main()
