from abc import ABC, abstractmethod
from typing import Optional


class SensorDataRepository(ABC):

    @abstractmethod
    def get_latest(self, sensor_id: Optional[str] = None) -> Optional[dict]:
        """
        Trả về document mới nhất từ collection inputSensor.
        dict thô từ Mongo — use case sẽ tự xử lý.
        """
        ...