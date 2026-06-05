import time
from pylsl import StreamInfo, StreamOutlet

def main():
    # Configure marker outlet matching Slicer parameters
    info = StreamInfo(name='SlicerTestTrigger', type='Markers', channel_count=1, 
                      nominal_srate=0, channel_format='string', source_id='slicer_sim_99')
    outlet = StreamOutlet(info)
    
    print("LSL Marker Stream live on the network.")
    print("Waiting 3 seconds for Slicer's async loop to discover and bond...")
    time.sleep(3)
    
    trigger_phrase = "START_SONICATION"
    print("\nEntering continuous execution loop. Press Ctrl+C to terminate script.\n")
    
    try:
        while True:
            print(f"Sending marker message: -> '{trigger_phrase}'")
            outlet.push_sample([trigger_phrase])
            print("Sample pushed successfully. Verify the Slicer application response.")
            
            # 10-second countdown visualization in terminal
            print("Next marker in: ", end="", flush=True)
            for remaining in range(10, 0, -1):
                print(f"{remaining}... ", end="", flush=True)
                time.sleep(1)
            print("\n" + "-"*40)
            
    except KeyboardInterrupt:
        print("\nLoop terminated by user. Exiting LSL broadcast tool cleanly.")

if __name__ == '__main__':
    main()