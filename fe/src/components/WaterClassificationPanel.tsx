import { useState, useEffect} from 'react';
import { sensorService } from '../services/api';

export function WaterClassificationPanel() {
	const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  // const [error, setError] = useState(null);

	useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Gọi API thực tế
        const res = await sensorService.getAIClassification();
        setData(res);
      } catch (err) {
        console.error("Error fetching sensor data:", err);
        // setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500 animate-pulse">Loading water classification...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 flex items-center justify-center min-h-[400px]">
        <div className="text-red-500 italic">No sensor data available.</div>
      </div>
    );
  }

	// Helper function để tính phần trăm độ rộng của thanh bar
  const getWidthPercent = (level, options) => {
    const index = options.indexOf(level);
    if (index === 0) return '30%';
    if (index === 1) return '60%';
    if (index === 2) return '100%';
    return '0%';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
      <h3 className="text-gray-900 mb-6 font-medium">Water Classification</h3>
      
      <div className="space-y-10">
        {/* Hard Water vs Soft Water */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Water Type</span>
            <span className={`${data.hardness?.category === "Hard Water" ? "text-blue-600" : "text-cyan-600"}`}>
              {data.hardness?.category || "Unknown"}
            </span>
          </div>

          <div className="flex gap-2">
						<div className={`flex-1 rounded-lg p-4 text-center transition-all ${
							data.hardness?.category === "Hard Water" ? 
								"bg-gradient-to-r from-cyan-500 to-blue-500 text-white" : "bg-gray-100 text-gray-400"
						}`}>              
							<div className="text-sm mb-1">Hard Water</div>
              <div className="text-2xl">{data.hardness?.category === "Hard Water" ? `${data.hardness?.value_mgl} mg/L` : "--"}</div>
            </div>

						<div className={`flex-1 rounded-lg p-4 text-center transition-all ${
							data.hardness?.category === "Soft Water" ? 
								"bg-gradient-to-r from-green-400 to-cyan-500 text-white" : "bg-gray-100 text-gray-400"
						}`}>
							<div className="text-sm mb-1">Soft Water</div>
              <div className="text-2xl">{data.hardness?.category === "Soft Water" ? `${data.hardness?.value_mgl} mg/L` : "--"}</div>
            </div>
          </div>
        </div>

        {/* Alkalinity Level Meter */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Alkalinity Level</span>
            <span className="text-blue-600">{data.alkalinity?.level}</span>
          </div>
          <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
            {/* <div className="absolute inset-y-0 left-0 w-[60%] bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 rounded-full"></div> */}
            <div 
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 rounded-full transition-all duration-500"
              style={{ width: getWidthPercent(data.alkalinity?.level, ["Low", "Moderate", "High"]) }}
            ></div>
						<div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs text-gray-700 z-10">{data.alkalinity?.value_mgl} mg/L</span>
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Low</span>
            <span>Moderate</span>
            <span>High</span>
          </div>
        </div>

        {/* Temperature Level Meter */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Temperature Level</span>
            <span className={data.temperature?.status === "Safe" ? "text-green-600" : "text-red-600"}>
              {data.temperature?.status}
            </span>
          </div>
          <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-400 via-green-400 to-orange-400 rounded-full transition-all duration-500"
              style={{ width: getWidthPercent(data.temperature?.status, ["Cold", "Safe", "Hot"]) }}
            ></div>
						<div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs text-gray-700 z-10">{data.temperature?.value_celsius?.toFixed(1)} °C</span>
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Cold</span>
            <span>Safe</span>
            <span>Hot</span>
          </div>
        </div>

        {/* Circular Gauges */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          {/* pH Gauge */}
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-2">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="48" cy="48" r="40" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                <circle
                  cx="48" cy="48" r="40" stroke="url(#gradientPH)" strokeWidth="8" fill="none"
                  strokeDasharray={`${(data.ph / 14) * 251.2} 251.2`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="gradientPH" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="100%" stopColor="#3b82f6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-gray-900 text-xl">{data.ph.toFixed(1)}</span>
              </div>
            </div>
            <span className="text-gray-600 text-sm">pH Level</span>
          </div>
          
          {/* DO Gauge */}
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-2">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="48" cy="48" r="40" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                <circle
                  cx="48" cy="48" r="40" stroke="url(#gradientDO)" strokeWidth="8" fill="none"
                  strokeDasharray={`${(data.do / 15) * 251.2} 251.2`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="gradientDO" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-gray-900 text-xl">{data.do.toFixed(1)}</span>
              </div>
            </div>
            <span className="text-gray-600 text-sm">DO Level</span>
          </div>
        </div>
      </div>
    </div>
  );
}
