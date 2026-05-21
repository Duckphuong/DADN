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
        issues_context = "\n".join([f"🔸 {issue}" for issue in lagging_issues]) if lagging_issues else "✅ Các thông số hóa lý đều nằm trong ngưỡng an toàn."

        weather_text = "Dữ liệu khí tượng không khả dụng."
        if weather_data:
            weather_text = f"🌦️ Lượng mưa: {'Có mưa' if weather_data.get('has_rain') else 'Không mưa'} ({weather_data.get('total_precipitation_mm', 0)} mm)\n"
            weather_text += f"🌡️ Nhiệt độ: {weather_data.get('avg_temperature_c', 28)} °C\n"
            weather_text += f"☁️ Độ phủ mây: {weather_data.get('avg_cloud_cover_pct', 50)}%\n"
            weather_text += f"💨 Tốc độ gió: {weather_data.get('max_wind_speed_kmh', 10)} km/h\n"
            weather_text += f"💧 Độ ẩm: {weather_data.get('avg_humidity_pct', 70)}%\n"
            weather_text += f"☀️ Chỉ số bức xạ UV: {weather_data.get('max_uv_index', 5)}"

        # ---------------------------------------------------------
        # 1. SYSTEM PROMPT: Định nghĩa Template cứng
        # ---------------------------------------------------------
        system_template = """Bạn là Giáo sư Khoa học Môi trường Thủy sản.
Nhiệm vụ của bạn là điền nội dung phân tích chuyên sâu vào MẪU BÁO CÁO dưới đây. 
LUẬT LỆ TỐI CAO:
1. Bắt đầu ngay lập tức bằng "🎯 1. TỔNG QUAN TRẠNG THÁI". KHÔNG có lời chào mở đầu, KHÔNG có câu kết luận dư thừa.
2. Giữ NGUYÊN SI từng chữ, từng icon của các TIÊU ĐỀ.
3. Chỉ viết phần phân tích của bạn vào thay thế cho các phần nằm trong ngoặc vuông [...].

MẪU BÁO CÁO BẮT BUỘC:
🎯 1. TỔNG QUAN TRẠNG THÁI
[Viết 1-2 câu nhận định chuyên môn học thuật về sức khỏe hệ sinh thái]
- Chỉ số WQI hiện tại: {wqi_score}/100 ({wqi_label})
- Độ tin cậy dự báo: {confidence}% 
- Dao động dự báo 24h: {wqi_range_0} - {wqi_range_1}
- Xu hướng sinh thái: {trend}

🔬 2. PHÂN TÍCH TƯƠNG QUAN LÝ-HÓA-SINH
[Dựa vào Dữ Liệu Đầu Vào, phân tích nguyên nhân cốt lõi gây ra các biến động (nếu có). Liên kết tác động chéo giữa các thông số. Dùng list gạch đầu dòng để trình bày rành mạch]

⚙️ 3. CHIẾN LƯỢC CAN THIỆP
⚡ Can thiệp cấp bách:
- [Biện pháp 1 cần làm ngay]
- [Biện pháp 2 cần làm ngay]

🛡️ Quản lý hệ đệm (Dài hạn):
- [Biện pháp duy trì hệ vi sinh/khoáng 1]
- [Biện pháp duy trì hệ vi sinh/khoáng 2]

🌤️ Tác động khí tượng:
- [Đánh giá thời tiết 24h tới sẽ làm trầm trọng thêm hay giúp cải thiện tình hình, và hướng phòng tránh]
"""
        
        # Tiêm dữ liệu thực tế vào phần cứng của System Template
        formatted_system = system_template.format(
            wqi_score=f"{wqi_score:.1f}",
            wqi_label=wqi_label,
            confidence=f"{confidence:.1f}",
            wqi_range_0=f"{wqi_range[0]:.1f}",
            wqi_range_1=f"{wqi_range[1]:.1f}",
            trend=trend
        )

        # ---------------------------------------------------------
        # 2. USER PROMPT: Chỉ đưa dữ liệu thô
        # ---------------------------------------------------------
        user_prompt = f"""### DỮ LIỆU ĐẦU VÀO ĐỂ PHÂN TÍCH ###
* Các cảnh báo thông số:
{issues_context}

* Khí tượng 24h tới:
{weather_text}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": formatted_system},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model_name,
                temperature=0.1,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Lỗi phần Solution AI (Groq): {e}")
            return "⚠️ **Cảnh báo:** Không thể kết nối với hệ thống AI Tư vấn. Đề nghị người vận hành kiểm tra các thông số khẩn cấp theo quy trình thủ công."