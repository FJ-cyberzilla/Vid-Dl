
import asyncio
import signal

async def main():
    loop = asyncio.get_running_loop()
    
    def handler():
        print("Signal received")
        
    loop.add_signal_handler(signal.SIGINT, handler)
    
    print("Blocking...")
    # This will block the event loop
    input("Press Enter...")
    print("Unblocked")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught in main")
