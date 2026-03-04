# module_name: system_monitor
# requires: psutil

import psutil

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    mem = psutil.virtual_memory()
    return mem.percent

def main(args=None):
    cpu = get_cpu_usage()
    mem = get_memory_usage()
    result = {"cpu_usage": cpu, "memory_usage": mem}
    print(result)
    return result