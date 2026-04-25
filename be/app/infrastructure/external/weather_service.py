import requests

def get_weather_data(lat: float, lon: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,cloud_cover,wind_speed_10m,relative_humidity_2m",
        "daily": "uv_index_max",
        "forecast_days": 1,
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            hourly = res_data['hourly']
            
            precip = sum(hourly['precipitation'])
            avg_temp = sum(hourly['temperature_2m']) / len(hourly['temperature_2m'])
            avg_cloud = sum(hourly['cloud_cover']) / len(hourly['cloud_cover'])
            max_wind = max(hourly['wind_speed_10m'])
            avg_humidity = sum(hourly['relative_humidity_2m']) / len(hourly['relative_humidity_2m'])
            
            # Lấy max UV index từ dự báo daily
            uv_index = res_data.get('daily', {}).get('uv_index_max', [0])[0]

            return {
                "has_rain": precip > 0.1,
                "total_precipitation_mm": round(precip, 2),
                "avg_temperature_c": round(avg_temp, 2),
                "avg_cloud_cover_pct": round(avg_cloud, 1), # % mây che phủ
                "max_wind_speed_kmh": round(max_wind, 1),   # Gió giật tối đa (km/h)
                "avg_humidity_pct": round(avg_humidity, 1), # Độ ẩm trung bình (%)
                "max_uv_index": round(uv_index, 1)          # Chỉ số tia UV
            }
    except Exception as e:
        print(f"Weather API Error: {e}")
    
    return {
        "has_rain": False, "total_precipitation_mm": 0, "avg_temperature_c": 28.0,
        "avg_cloud_cover_pct": 50.0, "max_wind_speed_kmh": 10.0, 
        "avg_humidity_pct": 70.0, "max_uv_index": 5.0
    }