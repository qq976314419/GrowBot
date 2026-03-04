# requires: psutil
# module_name: memory_usage

import psutil

def get_memory_usage():
    """
    获取当前电脑内存的使用情况
    
    Returns:
        dict: 包含以下键的字典:
            - total: 总内存大小 (单位: GB, 保留两位小数)
            - used: 已用内存大小 (单位: GB, 保留两位小数)
            - available: 可用内存大小 (单位: GB, 保留两位小数)
            - percent: 内存使用百分比 (单位: %, 保留两位小数)
    """
    try:
        # 获取内存使用信息
        memory_info = psutil.virtual_memory()
        
        # 将字节转换为GB (1GB = 1024^3 字节)
        total_gb = memory_info.total / (1024 ** 3)
        available_gb = memory_info.available / (1024 ** 3)
        used_gb = total_gb - available_gb
        
        # 计算使用百分比
        percent = memory_info.percent
        
        # 返回格式化后的结果
        return {
            'total': round(total_gb, 2),
            'used': round(used_gb, 2),
            'available': round(available_gb, 2),
            'percent': round(percent, 2)
        }
        
    except Exception as e:
        print(f"获取内存使用信息时出错: {e}")
        return None

def main():
    """
    主函数：获取并显示内存使用情况
    """
    print("正在获取内存使用情况...")
    
    memory_data = get_memory_usage()
    
    if memory_data:
        print("\n内存使用情况:")
        print(f"总内存: {memory_data['total']} GB")
        print(f"已用内存: {memory_data['used']} GB")
        print(f"可用内存: {memory_data['available']} GB")
        print(f"内存使用率: {memory_data['percent']}%")
        
        # 添加简单的使用建议
        if memory_data['percent'] > 90:
            print("\n警告: 内存使用率过高，建议关闭一些程序释放内存！")
        elif memory_data['percent'] > 70:
            print("\n提示: 内存使用率较高，请注意内存使用情况。")
        else:
            print("\n提示: 内存使用情况正常。")
    else:
        print("无法获取内存使用信息。")
