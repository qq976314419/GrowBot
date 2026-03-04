# requires: psutil
# module_name: system_monitor

import psutil

def get_cpu_usage():
    # Get current CPU usage percentage.
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    # Get current memory usage information.
    memory = psutil.virtual_memory()
    return {
        'total': memory.total,
        'available': memory.available,
        'percent': memory.percent,
        'used': memory.used,
        'free': memory.free
    }

def get_system_usage():
    # Get both CPU and memory usage information.
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    return {
        'cpu_usage_percent': cpu_usage,
        'memory_usage': memory_usage
    }

def main():
    # Example usage of the functions
    print("CPU Usage:", get_cpu_usage())
    print("Memory Usage:", get_memory_usage())
    print("System Usage:", get_system_usage())
