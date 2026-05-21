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
        Dựa trên hệ dữ liệu thực nghiệm dưới đây, hãy lập Báo cáo Phân tích Chất lượng Nước.

        ### DỮ LIỆU ĐẦU VÀO
        1. Trạng thái Sinh thái (WQI):
        - Hiện tại: {wqi_score:.1f}/100 ({wqi_label})
        - Độ tin cậy dự báo: {confidence:.1f}% 
        - Dự báo 24h: {wqi_range[0]:.1f} - {wqi_range[1]:.1f}
        - Xu hướng: {trend}

        2. Sai lệch Hóa lý & Vi sinh:
        {issues_context}

        3. Khí tượng 24h tới:
        {weather_text}

        ### YÊU CẦU CẤU TRÚC BẮT BUỘC
        Bắt đầu ngay lập tức bằng "🎯 1. TỔNG QUAN TRẠNG THÁI". Bố cục gồm 3 phần chính:
        🎯 1. TỔNG QUAN TRẠNG THÁI (Đánh giá sức khỏe hệ sinh thái).
        🔬 2. PHÂN TÍCH TƯƠNG QUAN LÝ-HÓA-SINH (Giải thích cơ chế gây rủi ro).
        ⚙️ 3. CHIẾN LƯỢC CAN THIỆP (Bao gồm Can thiệp cấp bách và Quản lý hệ đệm).
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là Giáo sư Khoa học Môi trường Thủy sản. Chỉ trả về ĐÚNG nội dung báo cáo theo chuẩn Markdown. TUYỆT ĐỐI KHÔNG lặp lại prompt, KHÔNG giải thích yêu cầu, KHÔNG chèn lời chào hỏi hay câu kết luận thừa."
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