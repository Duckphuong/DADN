import { useState, useEffect} from 'react';
import { sensorService } from '../services/api';
import { Header } from '../components/Header';
import { SensorCard } from '../components/SensorCard';
import { WaterClassificationPanel } from '../components/WaterClassificationPanel';
import { AIPredictionPanel } from '../components/AIPredictionPanel';
import { TrendCharts } from '../components/TrendCharts';
import { MapVisualization } from '../components/MapVisualization';
import { AlertsPanel } from '../components/AlertsPanel';
import { SystemArchitecture } from '../components/SystemArchitecture';
import { Footer } from '../components/Footer';
import { Droplet, Thermometer, Eye, Wind, Waves, Biohazard } from 'lucide-react';

// Main Page (Dashboard)
export function Dashboard(){
	const [sensorData, setSensorData] = useState<any>(null);
	const [loading, setLoading] = useState(true);

	const fetchLatestData = async () => {
		try {
			setLoading(true);
			const response = await sensorService.getLatestData();
			setSensorData(response); 
		} catch (error) {
			console.error("Error fetching sensor data:", error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchLatestData();
		// tự động cập nhật mỗi 30s
		const interval = setInterval(fetchLatestData, 30000); 
		return () => clearInterval(interval);
	}, []);

	// if (loading && !sensorData) {
	// 	return <div className="p-6">Loading sensor data...</div>;
	// }

	// if (!sensorData) {
	// 	return <div className="p-6">No sensor data available.</div>;
	// }

	return (
		<div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-blue-100">
			<Header />
			<main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
				{loading && !sensorData ? (
						/* Trạng thái đang tải */
						<div className="flex items-center justify-center py-20">
							<div className="text-lg text-slate-500 animate-pulse">Loading sensor data...</div>
						</div>
				) : !sensorData ? (
					/* Trạng thái không có dữ liệu */
					<div className="flex flex-col items-center justify-center py-20 bg-white/50 rounded-2xl border border-dashed border-slate-300">
						<div className="text-lg text-slate-400 italic">No sensor data available.</div>
						<button 
							onClick={fetchLatestData}
							className="mt-4 text-sm text-blue-600 underline"
						>
							Try again
						</button>
					</div>
				) : (
					<>
						<section>
							<h2 className="text-cyan-900 mb-6 font-medium text-xl">
								Real-Time Sensor Readings
							</h2>
								{/* <PredictTable /> */}
								{/* <Predict /> */}
								<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
									<SensorCard
										icon={<Droplet className="w-8 h-8" />}
										title="pH Value"
										value={sensorData.sensor_data.pH.toFixed(1)}
										unit=""
										range="0–14"
										status={
											sensorData.sensor_data.pH >= 6.5 && sensorData.sensor_data.pH <= 8.5 ? "Neutral" : 
											sensorData.sensor_data.pH < 6.5 ? "Acidic" : "Alkaline"
										}
										statusColor={
												sensorData.sensor_data.pH >= 6.5 && sensorData.sensor_data.pH <= 8.5 ? "text-green-500" : "text-red-500"
											}
										bgColor={
											sensorData.sensor_data.pH >= 6.5 && sensorData.sensor_data.pH <= 8.5 ? "bg-green-50" : "bg-red-50"
										}
										iconColor="text-blue-500"
									/>
									<SensorCard
										icon={<Thermometer className="w-8 h-8" />}
										title="Temperature"
										value={sensorData.sensor_data.Temp.toFixed(1)}
										unit="°C"
										range="0–50"
										status={
											sensorData.sensor_data.Temp >= 25 && sensorData.sensor_data.Temp <= 30 ? "Optimal" : 
											(sensorData.sensor_data.Temp >= 20 && sensorData.sensor_data.Temp < 25) || (sensorData.sensor_data.Temp > 30 && sensorData.sensor_data.Temp <= 32) ? "Suboptimal" : "Thermal Shock"
										}
										statusColor={
											sensorData.sensor_data.Temp >= 25 && sensorData.sensor_data.Temp <= 30 ? "text-green-500" : 
											(sensorData.sensor_data.Temp >= 20 && sensorData.sensor_data.Temp < 25) || (sensorData.sensor_data.Temp > 30 && sensorData.sensor_data.Temp <= 32) ? "text-yellow-500" : "text-red-500"
										}
										bgColor={
											sensorData.sensor_data.Temp >= 25 && sensorData.sensor_data.Temp <= 30 ? "bg-green-50" : 
											(sensorData.sensor_data.Temp >= 20 && sensorData.sensor_data.Temp < 25) || (sensorData.sensor_data.Temp > 30 && sensorData.sensor_data.Temp <= 32) ? "bg-yellow-50" : "bg-red-50"
										}
										iconColor="text-orange-500"
									/>
									<SensorCard
										icon={<Biohazard className="w-8 h-8" />}
										title="Ammonia"
										value={sensorData.sensor_data.Ammonia.toFixed(2)}
										unit="mg/L"
										range="0–5"
										status={
											sensorData.sensor_data.Ammonia <= 0.1 ? "Safe" : 
											sensorData.sensor_data.Ammonia <= 1.0 ? "Warning" : "Toxic"
										}
										statusColor={
											sensorData.sensor_data.Ammonia <= 0.1 ? "text-green-500" : 
											sensorData.sensor_data.Ammonia <= 1.0 ? "text-yellow-500" : "text-red-500"
										}
										bgColor={
											sensorData.sensor_data.Ammonia <= 0.1 ? "bg-green-50" : 
											sensorData.sensor_data.Ammonia <= 1.0 ? "bg-yellow-50" : "bg-red-50"
										}
										iconColor="text-purple-500"
									/>
									<SensorCard
										icon={<Eye className="w-8 h-8" />}
										title="Turbidity"
										value={sensorData.sensor_data.Turbidity.toFixed(1)}
										unit="NTU"
										range="0–10"
										status={
											sensorData.sensor_data.Turbidity <= 5 ? "Clear" : 
											sensorData.sensor_data.Turbidity <= 10 ? "Cloudy" : "Turbid"
										}
										statusColor={
											sensorData.sensor_data.Turbidity <= 5 ? "text-green-500" : 
											sensorData.sensor_data.Turbidity <= 10 ? "text-yellow-500" : "text-red-500"
										}
										bgColor={
											sensorData.sensor_data.Turbidity <= 5 ? "bg-green-50" : 
											sensorData.sensor_data.Turbidity <= 10 ? "bg-yellow-50" : "bg-red-50"
										}
										iconColor="text-gray-500"
									/>
									<SensorCard
										icon={<Wind className="w-8 h-8" />}
										title="Dissolved Oxygen"
										value={sensorData.sensor_data.DO.toFixed(1)}
										unit="mg/L"
										range="0–15"
										status={
											sensorData.sensor_data.DO >= 5.0 ? "Oxygen Rich" : 
											sensorData.sensor_data.DO >= 3.0 ? "Low Oxygen" : "Hypoxia (Danger)"
										}
										statusColor={
											sensorData.sensor_data.DO >= 5.0 ? "text-green-500" : 
											sensorData.sensor_data.DO >= 3.0 ? "text-yellow-500" : "text-red-500"
										}
										bgColor={
											sensorData.sensor_data.DO >= 5.0 ? "bg-green-50" : 
											sensorData.sensor_data.DO >= 3.0 ? "bg-yellow-50" : "bg-red-50"
										}
										iconColor="text-cyan-500"
									/>
									<SensorCard
										icon={<Waves className="w-8 h-8" />}
										title="Water Hardness"
										value={sensorData.sensor_data.Hardness.toFixed(1)}
										unit="mg L⁻¹"
										range="0–1000"
										status={
											sensorData.sensor_data.Hardness >= 0 && sensorData.sensor_data.Hardness <= 75 ? "Soft" : 
											sensorData.sensor_data.Hardness > 75 && sensorData.sensor_data.Hardness <= 150 ? "Moderately Hard" : "Hard"
										}
										statusColor={
											sensorData.sensor_data.Hardness >= 0 && sensorData.sensor_data.Hardness <= 75 ? "text-green-500" : 
											sensorData.sensor_data.Hardness > 75 && sensorData.sensor_data.Hardness <= 150 ? "text-yellow-500" : "text-red-500"
										}
										bgColor={
											sensorData.sensor_data.Hardness >= 0 && sensorData.sensor_data.Hardness <= 75 ? "bg-green-50" : 
											sensorData.sensor_data.Hardness > 75 && sensorData.sensor_data.Hardness <= 150 ? "bg-yellow-50" : "bg-red-50"
										}
										iconColor="text-indigo-500"
									/>
								</div>
						</section>

						<div className="grid md:grid-cols-1 lg:grid-cols-2 gap-6">
							<WaterClassificationPanel />
							<AIPredictionPanel />
						</div>
						
						<TrendCharts />
						<div className="grid md:grid-cols-1 lg:grid-cols-3 gap-6">
							<div className="lg:col-span-2">
								<MapVisualization />
							</div>
							<div>
								<AlertsPanel />
							</div>
						</div>
						<SystemArchitecture />
					</>
				)}
			</main>
			<Footer />
		</div>
	);
}