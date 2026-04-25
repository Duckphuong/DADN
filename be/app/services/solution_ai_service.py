import json
import google.generativeai as genai
from app.config import Config

class SolutionAIService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.profile_path = 'app/modelsAI/good_water_profile.json'

    def _find_lagging_parameters(self, current_sensor_data: dict) -> tuple[list, bool]:
        """
        Trả về 2 giá trị:
        - list: Danh sách các lỗi thọt (nếu có)
        - bool: Cờ (Flag) xác nhận xem file profile chuẩn đã tồn tại hay chưa
        """
        lagging_issues = []
        try:
            with open(self.profile_path, 'r') as f:
                good_profile = json.load(f)
                
            for param, value in current_sensor_data.items():
                if param in good_profile:
                    if value < good_profile[param]["min_safe"]:
                        lagging_issues.append(f"{param} đang thấp: {value} (Chuẩn nội bộ: >{good_profile[param]['min_safe']})")
                    elif value > good_profile[param]["max_safe"]:
                        lagging_issues.append(f"{param} đang cao: {value} (Chuẩn nội bộ: <{good_profile[param]['max_safe']})")
            
            # Đọc file thành công, có baseline
            return lagging_issues, True 
            
        except (FileNotFoundError, json.JSONDecodeError):
            # EDGE CASE: File chưa được tạo ra (Chưa train model bao giờ)
            return [], False

    def generate_advanced_solution(self, sensor_data: dict, ai_prediction_result: dict, weather_data: dict) -> str:
        # Lấy các chỉ số từ model để tăng tính khách quan
        ensemble = ai_prediction_result.get('ensemble', {})
        wqi = ensemble.get('wqi', {})
        forecast = ensemble.get('forecast_24h', {})
        
        confidence = ensemble.get('confidence', 0)
        wqi_range = forecast.get('predicted_wqi_range', [0, 0])
        trend = forecast.get('trend', 'Stable')

        # =========================================================
        # XỬ LÝ EDGE CASE: PHÂN NHÁNH NGỮ CẢNH (CONTEXT BRANCHING)
        # =========================================================
        lagging_issues, has_profile = self._find_lagging_parameters(sensor_data)
        
        if has_profile:
            # Kịch bản 1: Đã có chuẩn riêng của Model
            if lagging_issues:
                issues_context = "Các thông số đang bị lệch so với dữ liệu chuẩn CỦA HỒ (Thọt):\n" + "\n".join([f"- {i}" for i in lagging_issues])
            else:
                issues_context = "Các thông số cảm biến hiện tại đều nằm trong ngưỡng an toàn tuyệt đối của hồ."
        else:
            # Kịch bản 2: Edge Case - Chưa có chuẩn
            issues_context = f"""
            [LƯU Ý HỆ THỐNG]: Hiện tại AI nội bộ chưa học được Dữ liệu Chuẩn của hồ này.
            Bạn hãy TỰ ĐÁNH GIÁ các thông số cảm biến dưới đây dựa trên TIÊU CHUẨN THỦY SẢN CHUNG, tìm ra thông số nào đang nguy hiểm và đưa vào giải pháp:
            {json.dumps(sensor_data, indent=2)}
            """
        # =========================================================

        # Xây dựng Prompt tổng hợp
        prompt = f"""
        Bạn là chuyên gia tư vấn thủy sản. Hãy phân tích dựa trên dữ liệu định lượng sau:

        1. KẾT QUẢ DỰ BÁO TỪ MACHINE LEARNING:
        - Điểm WQI hiện tại: {wqi.get('score', 0):.1f} ({wqi.get('label', 'Unknown')})
        - Độ tin cậy của mô hình: {confidence:.1f}% 
        - Dải WQI dự báo (24h tới): từ {wqi_range[0]:.1f} đến {wqi_range[1]:.1f}
        - Xu hướng hệ thống: {trend}

        2. CHI TIẾT CẢM BIẾN & PHÂN TÍCH:
        {issues_context}

        3. DỰ BÁO THỜI TIẾT NGOẠI CẢNH (24H TỚI):
        - Tình trạng mưa: {"Sắp có mưa/Mưa to" if weather_data.get('has_rain') else "Không mưa"} ({weather_data.get('total_precipitation_mm', 0)} mm)
        - Nhiệt độ trung bình: {weather_data.get('avg_temperature_c', 28)} °C
        - Mây che phủ: {weather_data.get('avg_cloud_cover_pct', 50)}% (Lưu ý: Mây nhiều > 70% sẽ cản trở quang hợp sinh oxy)
        - Sức gió tối đa: {weather_data.get('max_wind_speed_kmh', 10)} km/h (Lưu ý: Gió mạnh > 25km/h dễ làm đục nước)
        - Chỉ số tia UV: {weather_data.get('max_uv_index', 5)} (Lưu ý: UV > 8 sẽ gây stress cho thủy sản tầng mặt)

        YÊU CẦU:
        - Nếu "Độ tin cậy" thấp (<70%), hãy đưa ra lời khuyên cần kiểm tra lại độ chính xác của cảm biến.
        - Nếu "Dải WQI dự báo" có mức thấp nhất dưới 50, hãy cảnh báo rủi ro biến động mạnh.
        - Đưa ra 3-4 hành động khắc phục cụ thể, tập trung xử lý các lỗi ở mục 2 và đề phòng yếu tố thời tiết ở mục 3.
        - Trả về kết quả bằng Markdown gạch đầu dòng ngắn gọn.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Hệ thống LLM đang gián đoạn hoặc quá tải. ({str(e)})"