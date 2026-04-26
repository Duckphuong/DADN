import React, { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { analyticsService } from '../services/api';
import { Loader2 } from 'lucide-react';

// const phData = [
//   { time: '00:00', value: 7.1 },
//   { time: '04:00', value: 7.0 },
//   { time: '08:00', value: 7.2 },
//   { time: '12:00', value: 7.3 },
//   { time: '16:00', value: 7.2 },
//   { time: '20:00', value: 7.1 },
//   { time: '24:00', value: 7.2 }
// ];

// const temperatureData = [
//   { time: '00:00', value: 22.5 },
//   { time: '04:00', value: 21.8 },
//   { time: '08:00', value: 23.2 },
//   { time: '12:00', value: 25.1 },
//   { time: '16:00', value: 24.5 },
//   { time: '20:00', value: 23.8 },
//   { time: '24:00', value: 22.9 }
// ];

// const conductivityData = [
//   { time: '00:00', value: 440 },
//   { time: '04:00', value: 435 },
//   { time: '08:00', value: 445 },
//   { time: '12:00', value: 455 },
//   { time: '16:00', value: 450 },
//   { time: '20:00', value: 448 },
//   { time: '24:00', value: 442 }
// ];

// const turbidityData = [
//   { location: 'Site A', value: 2.5 },
//   { location: 'Site B', value: 3.2 },
//   { location: 'Site C', value: 1.8 },
//   { location: 'Site D', value: 4.1 },
//   { location: 'Site E', value: 2.9 }
// ];

// const doData = [
//   { time: '00:00', value: 7.5 },
//   { time: '04:00', value: 7.7 },
//   { time: '08:00', value: 7.9 },
//   { time: '12:00', value: 8.1 },
//   { time: '16:00', value: 7.8 },
//   { time: '20:00', value: 7.6 },
//   { time: '24:00', value: 7.8 }
// ];

export function TrendCharts() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        setLoading(true);
        const trends = await analyticsService.getTrends();
        setData(trends);
      } catch (error) {
        console.error("Failed to fetch analytics trends:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrends();
  }, []);

  if (loading) {
    return (
      <div className="lg:col-span-3 flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!data) return null;

  // Trích xuất dữ liệu từ API response
  // Dựa trên serialize_analytics_trends trong backend
  const phData = data.ph_trend || [];
  const temperatureData = data.temperature_trend || [];
  const conductivityData = data.conductivity_trend || [];
  const doData = data.do_trend || [];
  const turbidityData = data?.turbidity_comparison || [];

  return (
    <section>
      <h2 className="text-cyan-900 mb-6">Trend Analysis</h2>
      
      <div className="grid md:grid-cols-1 lg:grid-cols-2 gap-6">
        {/* pH vs Time */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-gray-900 mb-4">pH vs Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={phData}>
              <defs>
                <linearGradient id="colorPh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" stroke="#6b7280" />
              <YAxis domain={[6.5, 7.5]} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Temperature Trend */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-gray-900 mb-4">Temperature Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={temperatureData}>
              <defs>
                <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" stroke="#6b7280" />
              <YAxis domain={[20, 26]} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Conductivity Trend */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-gray-900 mb-4">Conductivity Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={conductivityData}>
              <defs>
                <linearGradient id="colorCond" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" stroke="#6b7280" />
              <YAxis domain={[430, 460]} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Area type="monotone" dataKey="value" stroke="#eab308" fill="url(#colorCond)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Turbidity Comparison */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-gray-900 mb-4">Turbidity Comparison</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={turbidityData}>
              <defs>
                <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="location" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="value" fill="url(#colorBar)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Dissolved Oxygen Variation - Full Width */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 lg:col-span-2">
          <h3 className="text-gray-900 mb-4">Dissolved Oxygen Variation</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={doData}>
              <defs>
                <linearGradient id="colorDO" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" stroke="#6b7280" />
              <YAxis domain={[7, 8.5]} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#06b6d4" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
