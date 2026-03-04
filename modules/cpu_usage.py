# requires: psutil
# module_name: cpu_usage

import psutil

def get_cpu_usage():
    """
    获取当前电脑的CPU使用率
    
    Returns:
        float: CPU使用率百分比
    """
    try:
        # 获取CPU使用率，interval参数表示采样间隔（秒）
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent
    except Exception as e:
        print(f"获取CPU使用率时出错: {e}")
        return None

def main():
    """
    主函数：获取并显示CPU使用率
    """
    print("正在获取CPU使用率...")
    cpu_usage = get_cpu_usage()
    
    if cpu_usage is not None:
        print(f"当前CPU使用率: {cpu_usage}%")
    else:
        print("无法获取CPU使用率")
