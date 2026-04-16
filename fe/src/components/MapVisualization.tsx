import { useEffect, useState } from 'react';
import { MapPin, Activity } from 'lucide-react';
import { sensorService } from '../services/api'; // Giả sử đường dẫn tới api.ts của bạn

// Interface định nghĩa cấu trúc dữ liệu từ API dựa trên sensor_station_serializers.py
interface SensorStation {
  _id?: string;
  sensorName: string;
  location: {
    longitude: number;
    latitude: number;
  };
  status: 'ONLINE' | 'OFFLINE';
  isDeleted: boolean;
}

export function MapVisualization() {
  const [sensors, setSensors] = useState<SensorStation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const response = await sensorService.getStations(1, 50);
        // data đến từ serialize_sensor_station_list_response trong backend
        setSensors(response.data|| []);
      } catch (error) {
        console.error("Failed to fetch sensors:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSensors();
  }, []);

  // Hàm helper để map status và màu sắc
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return { label: 'healthy', color: 'bg-green-500' };
      case 'OFFLINE':
        return { label: 'critical', color: 'bg-red-500' };
      default:
        return { label: 'warning', color: 'bg-yellow-500' };
    }
  };

  // Hàm helper để tự động căn chỉnh sensor trên bản đồ
  const lats = sensors.map(s => s.location.latitude);
  const lngs = sensors.map(s => s.location.longitude);
  
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  const getPosition = (val: number, min: number, max: number) => {
    if (max === min) return 50; // Nếu chỉ có 1 điểm hoặc tọa độ trùng nhau, cho ra giữa
    const percentage = ((val - min) / (max - min)) * 80 + 10;
    return percentage;
  };

  const activeNodesCount = sensors.filter(s => s.status === 'ONLINE').length;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-gray-900 font-medium">Sensor Network Map</h2>
        <div className="flex items-center gap-2 text-gray-600">
          <Activity className="w-4 h-4" />
          <span className="text-sm">{activeNodesCount} Active Nodes</span>
        </div>
      </div>
      
      {/* Map Container */}
      <div className="relative bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl h-96 border-2 border-blue-100 overflow-hidden">
        {/* Map Grid Lines */}
        <svg className="absolute inset-0 w-full h-full opacity-20">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3b82f6" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Water Flow Lines */}
        <svg className="absolute inset-0 w-full h-full opacity-10">
          <path d="M 0 50 Q 150 30, 300 50 T 600 50" stroke="#06b6d4" strokeWidth="2" fill="none" />
          <path d="M 0 150 Q 200 130, 400 150 T 800 150" stroke="#0ea5e9" strokeWidth="2" fill="none" />
          <path d="M 0 250 Q 180 230, 360 250 T 720 250" stroke="#06b6d4" strokeWidth="2" fill="none" />
        </svg>

        {/* Sensor Markers từ API */}
        {!loading && sensors.map((sensor, index) => {
          const config = getStatusConfig(sensor.status);
          const topPos = getPosition(sensor.location.latitude, minLat, maxLat);
          const leftPos = getPosition(sensor.location.longitude, minLng, maxLng);
          const jitter = index * 2; // Mỗi sensor sau sẽ lệch 2% so với sensor trước

          return (
            <div
              key={sensor._id}
              className="absolute group cursor-pointer"
              style={{ 
                // Latitude tăng thì thường nằm ở trên (top thấp), nên ta lấy 100 - % 
                top: `${100 - topPos}%`, 
                left: `${leftPos}%`
              }}
            >
              {/* Pulsing Ring */}
              <div className={`absolute -top-4 -left-4 w-8 h-8 ${config.color} rounded-full opacity-20 animate-ping`}></div>
              
              {/* Marker */}
              <div className={`relative ${config.color} rounded-full p-2 shadow-lg border-2 border-white`}>
                <MapPin className="w-4 h-4 text-white" />
              </div>

              {/* Tooltip */}
              <div className={`absolute left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none z-10
                ${(100 - topPos) < 20 ? 'top-full mt-2' : 'bottom-full mb-2'} 
              `}>
                <div className="text-center bg-gray-900 text-white text-xs rounded-lg px-3 py-2 space-y-0.5 whitespace-nowrap"
                >
                  <div className="font-medium">{sensor.sensorName}</div>
                  <div className="text-gray-300">Status: {config.label}</div>
                  <div className="text-[10px] text-gray-400">Lat: {sensor.location.latitude} - Lng: {sensor.location.longitude}</div>
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading State */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50">
            <span className="text-sm text-blue-600 animate-pulse">Loading sensors...</span>
          </div>
        )}

        {/* Contamination Hotspot*/}
        {/* <div className="absolute" style={{ top: '35%', left: '72%' }}>
          <div className="relative">
            <div className="absolute w-16 h-16 bg-red-500 rounded-full opacity-20 animate-pulse"></div>
            <div className="absolute w-12 h-12 bg-red-500 rounded-full opacity-30 top-2 left-2"></div>
            <div className="absolute w-8 h-8 bg-red-600 rounded-full opacity-50 top-4 left-4"></div>
          </div>
        </div> */}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-6 pt-6 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm text-gray-600">Online (Healthy)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-sm text-gray-600">Offline (Critical)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded-full opacity-30"></div>
          <span className="text-sm text-gray-600">Contamination Zone</span>
        </div>
      </div>
    </div>
  );
}