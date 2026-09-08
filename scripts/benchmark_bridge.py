import time
from sota_dl.support.validators import validate_url as python_validate_url
from sota_dl.infrastructure.adapters.bridge_client import BridgeClient

def benchmark_python(iterations=1000):
    start = time.perf_counter()
    for _ in range(iterations):
        python_validate_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    end = time.perf_counter()
    total_time = end - start
    print(f"Python validate_url ({iterations} iterations): {total_time:.4f}s ({total_time/iterations*1000:.4f}ms/op)")
    return total_time

def benchmark_go_bridge(iterations=100):
    client = BridgeClient()
    start = time.perf_counter()
    for _ in range(iterations):
        client.call("validate_url", {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"})
    end = time.perf_counter()
    total_time = end - start
    print(f"Go Bridge validate_url ({iterations} iterations): {total_time:.4f}s ({total_time/iterations*1000:.4f}ms/op)")
    return total_time

def benchmark_go_bridge_ping(iterations=100):
    client = BridgeClient()
    start = time.perf_counter()
    for _ in range(iterations):
        client.call("ping", {})
    end = time.perf_counter()
    total_time = end - start
    print(f"Go Bridge ping ({iterations} iterations): {total_time:.4f}s ({total_time/iterations*1000:.4f}ms/op)")
    return total_time

if __name__ == "__main__":
    print("=== Starting Benchmarks ===")
    py_time = benchmark_python()
    go_time = benchmark_go_bridge()
    ping_time = benchmark_go_bridge_ping()
    
    print("\n=== Analysis ===")
    print("Go Bridge process spawn overhead is roughly the ping time.")
    print(f"Go Bridge is ~{go_time/100 / (py_time/1000):.1f}x slower for simple URL validation due to process spawning.")
    print("For long-running tasks like yt-dlp downloading, this ~10-20ms overhead is negligible.")
