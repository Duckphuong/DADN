import { useState, useEffect } from 'react';
import { getHistory } from '../services/api';
import { Header } from '../components/Header';
import { SensorCard } from '../components/SensorCard';
import { WaterClassificationPanel } from '../components/WaterClassificationPanel';
import { AIPredictionPanel } from '../components/AIPredictionPanel';
import { TrendCharts } from '../components/TrendCharts';
import { MapVisualization } from '../components/MapVisualization';
import { AlertsPanel } from '../components/AlertsPanel';
import { SystemArchitecture } from '../components/SystemArchitecture';
import { Footer } from '../components/Footer';
import {
    Droplet,
    Thermometer,
    Eye,
    Wind,
    Waves,
    Biohazard,
} from 'lucide-react';
import { HistoryData } from '../types/water';

const formatValue = (value: any, decimalPlaces: number = 1): string => {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    return Number(value).toFixed(decimalPlaces);
};

// Main Page (Dashboard)
export function Dashboard() {
    const [sensorData, setSensorData] = useState<any>(null);
    const [latestPrediction, setLatestPrediction] =
        useState<HistoryData | null>(null);
    const [loading, setLoading] = useState(true);

    const buildSensorSnapshot = (historyItem: HistoryData) => ({
        sensor_data: {
            'Nhiệt độ': historyItem['Nhiệt độ'],
            pH: historyItem.pH,
            DO: historyItem.DO,
            'Độ dẫn': historyItem['Độ dẫn'],
            'Độ kiềm': historyItem['Độ kiềm'],
            'N-NO2': historyItem['N-NO2'],
            'N-NH4': historyItem['N-NH4'],
            'P-PO4': historyItem['P-PO4'],
            H2S: historyItem.H2S,
            TSS: historyItem.TSS,
            COD: historyItem.COD,
            'Aeromonas tổng số': historyItem['Aeromonas tổng số'],
            Coliform: historyItem.Coliform,
        },
        prediction: historyItem.prediction,
        created_at: historyItem.created_at,
        id: historyItem.id,
        idSensor: historyItem.idSensor,
    });

    const fetchLatestData = async () => {
        try {
            setLoading(true);
            const history = await getHistory();
            const latestHistory = history?.[0];
            if (latestHistory) {
                setLatestPrediction(latestHistory);
                setSensorData(buildSensorSnapshot(latestHistory));
            } else {
                setLatestPrediction(null);
                setSensorData(null);
            }
        } catch (error) {
            console.error('Error fetching prediction history:', error);
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
        <div className="min-h-screen bg-linear-to-br from-cyan-50 via-blue-50 to-blue-100">
            <Header />

            <main className="max-w-400 mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
                {loading && !sensorData ? (
                    /* Trạng thái đang tải */
                    <div className="flex items-center justify-center py-20">
                        <div className="text-lg text-slate-500 animate-pulse">
                            Loading sensor data...
                        </div>
                    </div>
                ) : !sensorData ? (
                    /* Trạng thái không có dữ liệu */
                    <div className="flex flex-col items-center justify-center py-20 bg-white/50 rounded-2xl border border-dashed border-slate-300">
                        <div className="text-lg text-slate-400 italic">
                            No sensor data available.
                        </div>
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
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <SensorCard
                                    icon={<Droplet className="w-8 h-8" />}
                                    title="pH Value"
                                    value={formatValue(
                                        sensorData.sensor_data.pH,
                                        1,
                                    )}
                                    unit=""
                                    range="0–14"
                                    status={
                                        sensorData.sensor_data.pH >= 6.5 &&
                                        sensorData.sensor_data.pH <= 8.5
                                            ? 'Neutral'
                                            : sensorData.sensor_data.pH < 6.5
                                              ? 'Acidic'
                                              : 'Alkaline'
                                    }
                                    statusColor={
                                        sensorData.sensor_data.pH >= 6.5 &&
                                        sensorData.sensor_data.pH <= 8.5
                                            ? 'text-green-500'
                                            : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data.pH >= 6.5 &&
                                        sensorData.sensor_data.pH <= 8.5
                                            ? 'bg-green-50'
                                            : 'bg-red-50'
                                    }
                                    iconColor="text-blue-500"
                                />
                                <SensorCard
                                    icon={<Thermometer className="w-8 h-8" />}
                                    title="Nhiệt độ"
                                    value={formatValue(
                                        sensorData.sensor_data['Nhiệt độ'],
                                        1,
                                    )}
                                    unit="°C"
                                    range="0–50"
                                    status={
                                        sensorData.sensor_data['Nhiệt độ'] >=
                                            25 &&
                                        sensorData.sensor_data['Nhiệt độ'] <= 30
                                            ? 'Optimal'
                                            : (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] >= 20 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] < 25) ||
                                                (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] > 30 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] <= 32)
                                              ? 'Suboptimal'
                                              : 'Thermal Shock'
                                    }
                                    statusColor={
                                        sensorData.sensor_data['Nhiệt độ'] >=
                                            25 &&
                                        sensorData.sensor_data['Nhiệt độ'] <= 30
                                            ? 'text-green-500'
                                            : (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] >= 20 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] < 25) ||
                                                (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] > 30 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] <= 32)
                                              ? 'text-yellow-500'
                                              : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data['Nhiệt độ'] >=
                                            25 &&
                                        sensorData.sensor_data['Nhiệt độ'] <= 30
                                            ? 'bg-green-50'
                                            : (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] >= 20 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] < 25) ||
                                                (sensorData.sensor_data[
                                                    'Nhiệt độ'
                                                ] > 30 &&
                                                    sensorData.sensor_data[
                                                        'Nhiệt độ'
                                                    ] <= 32)
                                              ? 'bg-yellow-50'
                                              : 'bg-red-50'
                                    }
                                    iconColor="text-orange-500"
                                />
                                <SensorCard
                                    icon={<Biohazard className="w-8 h-8" />}
                                    title="N-NH4"
                                    value={formatValue(
                                        sensorData.sensor_data['N-NH4'],
                                        2,
                                    )}
                                    unit="mg/L"
                                    range="0–5"
                                    status={
                                        sensorData.sensor_data['N-NH4'] <= 0.1
                                            ? 'Safe'
                                            : sensorData.sensor_data['N-NH4'] <=
                                                1.0
                                              ? 'Warning'
                                              : 'Toxic'
                                    }
                                    statusColor={
                                        sensorData.sensor_data['N-NH4'] <= 0.1
                                            ? 'text-green-500'
                                            : sensorData.sensor_data['N-NH4'] <=
                                                1.0
                                              ? 'text-yellow-500'
                                              : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data['N-NH4'] <= 0.1
                                            ? 'bg-green-50'
                                            : sensorData.sensor_data['N-NH4'] <=
                                                1.0
                                              ? 'bg-yellow-50'
                                              : 'bg-red-50'
                                    }
                                    iconColor="text-purple-500"
                                />
                                <SensorCard
                                    icon={<Eye className="w-8 h-8" />}
                                    title="TSS"
                                    value={formatValue(
                                        sensorData.sensor_data.TSS,
                                        1,
                                    )}
                                    unit="mg/L"
                                    range="0–10"
                                    status={
                                        sensorData.sensor_data.TSS <= 5
                                            ? 'Clear'
                                            : sensorData.sensor_data.TSS <= 10
                                              ? 'Cloudy'
                                              : 'Turbid'
                                    }
                                    statusColor={
                                        sensorData.sensor_data.TSS <= 5
                                            ? 'text-green-500'
                                            : sensorData.sensor_data.TSS <= 10
                                              ? 'text-yellow-500'
                                              : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data.TSS <= 5
                                            ? 'bg-green-50'
                                            : sensorData.sensor_data.TSS <= 10
                                              ? 'bg-yellow-50'
                                              : 'bg-red-50'
                                    }
                                    iconColor="text-gray-500"
                                />
                                <SensorCard
                                    icon={<Wind className="w-8 h-8" />}
                                    title="Dissolved Oxygen"
                                    value={formatValue(
                                        sensorData.sensor_data.DO,
                                        1,
                                    )}
                                    unit="mg/L"
                                    range="0–15"
                                    status={
                                        sensorData.sensor_data.DO >= 5.0
                                            ? 'Oxygen Rich'
                                            : sensorData.sensor_data.DO >= 3.0
                                              ? 'Low Oxygen'
                                              : 'Hypoxia (Danger)'
                                    }
                                    statusColor={
                                        sensorData.sensor_data.DO >= 5.0
                                            ? 'text-green-500'
                                            : sensorData.sensor_data.DO >= 3.0
                                              ? 'text-yellow-500'
                                              : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data.DO >= 5.0
                                            ? 'bg-green-50'
                                            : sensorData.sensor_data.DO >= 3.0
                                              ? 'bg-yellow-50'
                                              : 'bg-red-50'
                                    }
                                    iconColor="text-cyan-500"
                                />
                                <SensorCard
                                    icon={<Waves className="w-8 h-8" />}
                                    title="Độ kiềm"
                                    value={formatValue(
                                        sensorData.sensor_data['Độ kiềm'],
                                        1,
                                    )}
                                    unit="mg/L"
                                    range="0–1000"
                                    status={
                                        sensorData.sensor_data['Độ kiềm'] >=
                                            0 &&
                                        sensorData.sensor_data['Độ kiềm'] <= 75
                                            ? 'Low'
                                            : sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] > 75 &&
                                                sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] <= 150
                                              ? 'Moderate'
                                              : 'High'
                                    }
                                    statusColor={
                                        sensorData.sensor_data['Độ kiềm'] >=
                                            0 &&
                                        sensorData.sensor_data['Độ kiềm'] <= 75
                                            ? 'text-green-500'
                                            : sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] > 75 &&
                                                sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] <= 150
                                              ? 'text-yellow-500'
                                              : 'text-red-500'
                                    }
                                    bgColor={
                                        sensorData.sensor_data['Độ kiềm'] >=
                                            0 &&
                                        sensorData.sensor_data['Độ kiềm'] <= 75
                                            ? 'bg-green-50'
                                            : sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] > 75 &&
                                                sensorData.sensor_data[
                                                    'Độ kiềm'
                                                ] <= 150
                                              ? 'bg-yellow-50'
                                              : 'bg-red-50'
                                    }
                                    iconColor="text-indigo-500"
                                />
                            </div>
                        </section>

                        <div className="grid md:grid-cols-1 lg:grid-cols-2 gap-6">
                            <WaterClassificationPanel
                                sensorId={latestPrediction?.idSensor}
                            />
                            <AIPredictionPanel historyItem={latestPrediction} />
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
