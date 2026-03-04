# requires: requests

# module_name: weather_info

import requests
import json

def get_weather(city_name):
    """
    获取指定城市的实时天气信息
    
    Args:
        city_name (str): 城市名称
    
    Returns:
        dict: 包含温度、天气状况等信息的字典，如果获取失败则返回None
    """
    # 使用和风天气API（免费版）
    api_key = "YOUR_API_KEY"  # 请替换为你的实际API密钥
    base_url = "https://devapi.qweather.com/v7/weather/now"
    
    # 首先获取城市的location ID
    geo_url = "https://geoapi.qweather.com/v2/city/lookup"
    geo_params = {
        "location": city_name,
        "key": api_key,
        "lang": "zh"
    }
    
    try:
        # 获取城市位置信息
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        geo_data = geo_response.json()
        
        if geo_data["code"] != "200":
            print(f"错误: 无法找到城市 '{city_name}'")
            return None
        
        # 获取第一个匹配城市的location ID
        location_id = geo_data["location"][0]["id"]
        city = geo_data["location"][0]["name"]
        
        # 获取天气信息
        weather_params = {
            "location": location_id,
            "key": api_key,
            "lang": "zh"
        }
        
        weather_response = requests.get(base_url, params=weather_params, timeout=10)
        weather_data = weather_response.json()
        
        if weather_data["code"] != "200":
            print(f"错误: 无法获取天气信息")
            return None
        
        # 提取所需信息
        now_data = weather_data["now"]
        weather_info = {
            "city": city,
            "temperature": now_data["temp"],
            "feels_like": now_data["feelsLike"],
            "weather": now_data["text"],
            "wind_direction": now_data["windDir"],
            "wind_scale": now_data["windScale"],
            "humidity": now_data["humidity"],
            "pressure": now_data["pressure"],
            "visibility": now_data["vis"],
            "update_time": weather_data["updateTime"]
        }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"数据解析错误: {e}")
        return None
    except KeyError as e:
        print(f"数据格式错误: {e}")
        return None

def display_weather(weather_info):
    """
    格式化显示天气信息
    
    Args:
        weather_info (dict): 天气信息字典
    """
    if not weather_info:
        return
    
    print("\n" + "="*50)
    print(f"城市: {weather_info['city']}")
    print(f"更新时间: {weather_info['update_time']}")
    print("-"*50)
    print(f"当前天气: {weather_info['weather']}")
    print(f"温度: {weather_info['temperature']}°C")
    print(f"体感温度: {weather_info['feels_like']}°C")
    print(f"湿度: {weather_info['humidity']}%")
    print(f"风向: {weather_info['wind_direction']}")
    print(f"风力等级: {weather_info['wind_scale']}级")
    print(f"气压: {weather_info['pressure']} hPa")
    print(f"能见度: {weather_info['visibility']} 公里")
    print("="*50)

def main(*args):
    """
    主函数：获取用户输入的城市名并显示天气信息
    
    Args:
        *args: 可变参数，用于兼容不同的调用方式
    """
    print("天气查询系统")
    print("-"*30)
    
    # 如果通过参数传递了城市名，则直接查询
    if args and len(args) > 0 and args[0]:
        city_name = args[0]
        print(f"\n正在查询 {city_name} 的天气信息...")
        weather_info = get_weather(city_name)
        
        if weather_info:
            display_weather(weather_info)
        else:
            print(f"无法获取 {city_name} 的天气信息，请检查城市名是否正确")
        return weather_info
    
    # 否则进入交互模式
    while True:
        city_name = input("\n请输入城市名（输入'quit'退出）: ").strip()
        
        if city_name.lower() == 'quit':
            print("感谢使用天气查询系统！")
            break
        
        if not city_name:
            print("请输入有效的城市名！")
            continue
        
        print(f"\n正在查询 {city_name} 的天气信息...")
        weather_info = get_weather(city_name)
        
        if weather_info:
            display_weather(weather_info)
        else:
            print(f"无法获取 {city_name} 的天气信息，请检查城市名是否正确")
