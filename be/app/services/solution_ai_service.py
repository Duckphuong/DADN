import json
import os
from groq import Groq
from app.config import Config

class SolutionAIService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        
        self.model_name = "llama-3.3-70b-versatile" 
        root_dir = os.getcwd()
        self.profile_path = os.path.join(root_dir, 'modelsAI', 'good_water_profile.json')

    def _find_lagging_parameters(self, current_sensor_data: dict) -> tuple[list, bool]:
        lagging_issues = []
        try:
            if not os.path.exists(self.profile_path):
                print(f"[LỖI NGHIÊM TRỌNG] Không tìm thấy file tại đường dẫn: {self.profile_path}")
                return ["[LỖI HỆ THỐNG] Không tìm thấy hồ sơ chuẩn để đối chiếu."], False
            
            with open(self.profile_path, 'r') as f:
                good_profile = json.load(f)
                
            for param, value in current_sensor_data.items():
                if param in good_profile:
                    safe_val = float(value)
                    if safe_val < good_profile[param]["min_safe"]:
                        lagging_issues.append(f"{param} đang thấp: {safe_val} (Chuẩn nội bộ: >{good_profile[param]['min_safe']})")
                    elif safe_val > good_profile[param]["max_safe"]:
                        lagging_issues.append(f"{param} đang cao: {safe_val} (Chuẩn nội bộ: <{good_profile[param]['max_safe']})")
            return lagging_issues, True
        except (FileNotFoundError, ValueError):
            return [], False

    def generate_advanced_solution(self, sensor_data: dict, ai_prediction_result: dict, weather_data: dict) -> str:
        summary = ai_prediction_result.get("summary", {})
        wqi_info = summary.get("wqi", {})
        forecast = summary.get("forecast_24h", {})

        wqi_score = wqi_info.get("score", 0)
        wqi_label = wqi_info.get("label", "Unknown")
        trend = forecast.get("trend", "Unknown")
        wqi_range = forecast.get("predicted_wqi_range", [0, 0])
        confidence = forecast.get("confidence_score", 0)

        lagging_issues, has_profile = self._find_lagging_parameters(sensor_data)
        issues_context = "\n".join([f"- {issue}" for issue in lagging_issues]) if lagging_issues else "- Các thông số đều ở mức an toàn."

        weather_text = "Không có dữ liệu thời tiết"
        if weather_data:
            weather_text = f"- Mưa: {'Có mưa' if weather_data.get('has_rain') else 'Không mưa'} ({weather_data.get('total_precipitation_mm', 0)} mm)\n"
            weather_text += f"- Nhiệt độ: {weather_data.get('avg_temperature_c', 28)} °C\n"
            weather_text += f"- Mây che phủ: {weather_data.get('avg_cloud_cover_pct', 50)}%"
            weather_text += f"\n- Gió: {weather_data.get('max_wind_speed_kmh', 10)} km/h"
            weather_text += f"\n- Độ ẩm: {weather_data.get('avg_humidity_pct', 70)}%"
            weather_text += f"\n- Chỉ số UV: {weather_data.get('max_uv_index', 5)}"

        prompt = f"""
        Bạn là một chuyên gia tư vấn nuôi trồng thủy sản. Dựa vào dữ liệu dưới đây, hãy đưa ra phân tích và giải pháp khắc phục ngắn gọn, rõ ràng (Format bằng Markdown).

        1. TRẠNG THÁI HỆ THỐNG:
        - Điểm WQI hiện tại: {wqi_score:.1f}/100 ({wqi_label})
        - Độ tin cậy của AI: {confidence:.1f}% 
        - Dải WQI dự báo (24h tới): từ {wqi_range[0]:.1f} đến {wqi_range[1]:.1f}
        - Xu hướng: {trend}

        2. CHI TIẾT CẢM BIẾN & LỖI:
        {issues_context}

        3. THỜI TIẾT 24H TỚI:
        {weather_text}

        YÊU CẦU: Trả lời đi thẳng vào nguyên nhân và các bước hành động cụ thể để cứu hồ nước.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia tư vấn chất lượng nước. Luôn trả lời bằng Tiếng Việt, định dạng Markdown rõ ràng, chuyên nghiệp."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                temperature=0.3,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Lỗi phần Solution AI (Groq): {e}")
            return "Cần hành động ngay (Hệ thống AI tư vấn đang bận)."