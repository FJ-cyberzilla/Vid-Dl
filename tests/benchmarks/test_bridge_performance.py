import time
import asyncio
import os
from pathlib import Path
from sota_dl.infrastructure.adapters.yt_dlp import YtDlpAdapter
from sota_dl.core.models import DownloadOptions

async def benchmark_bridge():
    adapter = YtDlpAdapter()
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    options = DownloadOptions(output_dir=Path("./benchmark_downloads").resolve())
    
    # Ensure directory exists
    os.makedirs(options.output_dir, exist_ok=True)
    
    start_time = time.perf_counter()
    
    # We call the adapter's download method. 
    # Since it uses the bridge client to trigger the Go binary,
    # this will measure the full round-trip of the IPC bridge.
    result = adapter.download(
        target=url,
        options=options,
        progress_hook=lambda d: None
    )
    
    end_time = time.perf_counter()
    
    print(f"Benchmark completed.")
    print(f"Status: {result.status}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(benchmark_bridge())
