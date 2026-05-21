import json
import os
from groq import Groq
from app.config import Config


class SolutionAIService:

    def __init__(self):
        self.client = Groq(
            api_key=Config.GROQ_API_KEY
        )

        self.model_name = "llama-3.3-70b-versatile"

        root_dir = os.getcwd()

        self.profile_path = os.path.join(
            root_dir,
            "modelsAI",
            "good_water_profile.json"
        )

    # =========================================================
    # Detect abnormal parameters
    # =========================================================
    def _find_lagging_parameters(
        self,
        current_sensor_data: dict
    ) -> tuple[list, bool]:

        lagging_issues = []

        try:

            if not os.path.exists(self.profile_path):

                print(
                    f"[ERROR] Missing profile file: "
                    f"{self.profile_path}"
                )

                return (
                    ["Không tìm thấy hồ sơ chuẩn."],
                    False
                )

            with open(
                self.profile_path,
                "r",
                encoding="utf-8"
            ) as f:

                good_profile = json.load(f)

            for param, value in current_sensor_data.items():

                if param not in good_profile:
                    continue

                try:
                    safe_val = float(value)
                except:
                    continue

                min_safe = good_profile[param].get(
                    "min_safe"
                )

                max_safe = good_profile[param].get(
                    "max_safe"
                )

                if (
                    min_safe is not None
                    and safe_val < min_safe
                ):

                    lagging_issues.append(
                        f"🔻 {param} thấp ({safe_val}) "
                        f"- ngưỡng an toàn > {min_safe}"
                    )

                elif (
                    max_safe is not None
                    and safe_val > max_safe
                ):

                    lagging_issues.append(
                        f"🔺 {param} cao ({safe_val}) "
                        f"- ngưỡng an toàn < {max_safe}"
                    )

            return lagging_issues, True

        except Exception as e:

            print(f"[PROFILE ERROR] {e}")

            return [], False

    # =========================================================
    # Weather text formatter
    # =========================================================
    def _build_weather_text(
        self,
        weather_data: dict
    ) -> str:

        if not weather_data:
            return "Không có dữ liệu khí tượng."

        return f"""
- 🌧️ Mưa: {"Có mưa" if weather_data.get("has_rain") else "Không mưa"} ({weather_data.get("total_precipitation_mm", 0)} mm)
- 🌡️ Nhiệt độ: {weather_data.get("avg_temperature_c", 28)} °C
- ☁️ Mây che phủ: {weather_data.get("avg_cloud_cover_pct", 50)}%
- 💨 Gió cực đại: {weather_data.get("max_wind_speed_kmh", 10)} km/h
- 💧 Độ ẩm: {weather_data.get("avg_humidity_pct", 70)}%
- ☀️ UV cực đại: {weather_data.get("max_uv_index", 5)}
        """.strip()

    # =========================================================
    # Main AI Report
    # =========================================================
    def generate_advanced_solution(
        self,
        sensor_data: dict,
        ai_prediction_result: dict,
        weather_data: dict
    ) -> str:

        summary = ai_prediction_result.get(
            "summary",
            {}
        )

        wqi_info = summary.get(
            "wqi",
            {}
        )

        forecast = summary.get(
            "forecast_24h",
            {}
        )

        wqi_score = wqi_info.get(
            "score",
            0
        )

        wqi_label = wqi_info.get(
            "label",
            "Unknown"
        )

        trend = forecast.get(
            "trend",
            "Unknown"
        )

        wqi_range = forecast.get(
            "predicted_wqi_range",
            [0, 0]
        )

        confidence = forecast.get(
            "confidence_score",
            0
        )

        lagging_issues, _ = (
            self._find_lagging_parameters(
                sensor_data
            )
        )

        issues_context = (
            "\n".join(lagging_issues)
            if lagging_issues
            else "✅ Không phát hiện thông số vượt ngưỡng."
        )

        weather_text = self._build_weather_text(
            weather_data
        )

        # =====================================================
        # SYSTEM PROMPT
        # =====================================================

        system_prompt = f"""
Bạn là chuyên gia AI phân tích chất lượng nước.

NHIỆM VỤ:
Tạo báo cáo markdown chuyên nghiệp cho dashboard AI.

QUY TẮC BẮT BUỘC:
- Chỉ trả về markdown
- Không giải thích
- Không chào hỏi
- Không kết luận dư thừa
- Không dùng văn phong sáo rỗng
- Viết ngắn gọn, kỹ thuật, thực tế

FORMAT BẮT BUỘC:

## 🎯 1. Tổng Quan Chất Lượng Nước

[Phân tích ngắn gọn]

- **WQI hiện tại:** {wqi_score:.1f}/100 ({wqi_label})
- **Độ tin cậy AI:** {confidence:.1f}%
- **Dự báo 24h:** {wqi_range[0]:.1f} → {wqi_range[1]:.1f}
- **Xu hướng:** {trend}

## 🌦️ 2. Ảnh Hưởng Môi Trường

[Phân tích tác động thời tiết]

## ⚠️ 3. Nguyên Nhân Tiềm Năng

[Dùng bullet points]

## ⚙️ 4. Khuyến Nghị Can Thiệp

### **Hành động ngắn hạn**
- ...

### **Hành động dài hạn**
- ...

QUAN TRỌNG:
- PHẢI dùng markdown heading ## và ###
- PHẢI dùng **bold**
- PHẢI có bullet points
- Không được phá vỡ format
"""

        # =====================================================
        # USER PROMPT
        # =====================================================

        user_prompt = f"""
## Dữ liệu cảm biến bất thường

{issues_context}

## Dữ liệu khí tượng

{weather_text}
"""

        try:

            response = self.client.chat.completions.create(

                model=self.model_name,

                temperature=0.15,

                max_tokens=1200,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            return response.choices[0].message.content

        except Exception as e:

            print(f"[SOLUTION AI ERROR] {e}")

            return """
# 💡 Solution & Recommendation

## ⚠️ System Error

Không thể tạo báo cáo AI tại thời điểm hiện tại.
Vui lòng thử lại sau.
            """.strip()