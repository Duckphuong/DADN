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
import { Droplet, Thermometer, Zap, Eye, Wind, Waves } from 'lucide-react';

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
			console.error("Lỗi khi lấy dữ liệu cảm biến:", error);
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

	if (loading && !sensorData) {
		return <div className="p-6">Đang tải dữ liệu...</div>;
	}

	if (!sensorData) {
		return <div className="p-6">Không có dữ liệu cảm biến.</div>;
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-blue-100">
			<Header />
			<main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
				<section>
					<h2 className="text-cyan-900 mb-6">
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
								icon={<Zap className="w-8 h-8" />}
								title="Conductivity"
								value={sensorData.conductivity?.value || "0"}
								unit="µS/cm"
								range="0–2000"
								status={
									sensorData.sensor_data.Conductivity <= 1000 ? "Low Salinity" : 
									sensorData.sensor_data.Conductivity <= 1500 ? "Moderate" : "High Mineral"
								}
								statusColor={
									sensorData.sensor_data.Conductivity <= 1000 ? "text-green-500" : 
									sensorData.sensor_data.Conductivity <= 1500 ? "text-yellow-500" : "text-red-500"
								}
								bgColor={
									sensorData.sensor_data.Conductivity <= 1000 ? "bg-green-50" : 
									sensorData.sensor_data.Conductivity <= 1500 ? "bg-yellow-50" : "bg-red-50"
								}
								iconColor="text-yellow-500"
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
									sensorData.sensor_data.Hardness >= 50 && sensorData.sensor_data.Hardness <= 150 ? "Soft Water" : 
									sensorData.sensor_data.Hardness > 150 && sensorData.sensor_data.Hardness <= 300 ? "Hard Water" : "Very Hard"
								}
								statusColor={
									sensorData.sensor_data.Hardness >= 50 && sensorData.sensor_data.Hardness <= 150 ? "text-green-500" : 
									sensorData.sensor_data.Hardness > 150 && sensorData.sensor_data.Hardness <= 300 ? "text-yellow-500" : "text-red-500"
								}
								bgColor={
									sensorData.sensor_data.Hardness >= 50 && sensorData.sensor_data.Hardness <= 150 ? "bg-green-50" : 
									sensorData.sensor_data.Hardness > 150 && sensorData.sensor_data.Hardness <= 300 ? "bg-yellow-50" : "bg-red-50"
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
			</main>
			<Footer />
		</div>
	);
}