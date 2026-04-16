import React, { useEffect, useState } from 'react';
import { Brain, TrendingUp, AlertTriangle, Loader2 } from 'lucide-react';
import { getHistory } from '../services/api';
import { HistoryData } from '../types/water'; 

export function AIPredictionPanel() {
	const [predictionData, setPredictionData] = useState<HistoryData | null>(null);
	const [loading, setLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		const fetchLatestPrediction = async () => {
			try {
				setLoading(true);
				const history = await getHistory();
				if (history && history.length > 0) {
					setPredictionData(history[0]);
				}
			} catch (err) {
				console.error("Failed to fetch AI data:", err);
				setError("Could not load prediction data");
			} finally {
				setLoading(false);
			}
		};

		fetchLatestPrediction();
	}, []);

	if (loading) {
		return (
			<div className="flex items-center justify-center p-12 bg-white rounded-2xl shadow-lg border border-indigo-100">
				<Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
				<span className="ml-3 text-gray-500">Loading AI Analysis...</span>
			</div>
		);
	}

	if (error || !predictionData) {
		return (
			<div className="p-6 bg-red-50 rounded-2xl border border-red-100 text-red-600">
				{error || "No prediction data available."}
			</div>
		);
	}

	// --- GIẢI THÍCH: Trích xuất dữ liệu từ 'summary' của model tốt nhất ---
	// Vì backend lưu kết quả của AIModelService.predict() vào field 'prediction'
	// Chúng ta cần truy cập vào .summary để lấy thông tin khớp với giao diện
	const aiRawResult = predictionData.prediction as any;
	const summary = aiRawResult?.summary;

	const wqi = summary?.wqi || { score: 10, label: 'N/A' };
	
	// Ánh xạ 'risk' (backend) sang cấu trúc của PredictionRisk (frontend)
	const risk = {
		status: summary?.risk?.status || 'Unknown',
		risk_level: summary?.risk?.level ?? 0 // Backend dùng 'level', Frontend dùng 'risk_level'
	};

	const forecast = summary?.forecast_24h || { 
		trend: 'Stable', 
		predicted_wqi_range: [0, 0], 
		confidence_score: 0, 
		model_used: 'N/A' 
	};

	// Lấy confidence chung của model
	const confidence = summary?.confidence || 0;
	const accuracy = aiRawResult?.models[0].accuracy || 0;

	return (
		<div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl shadow-lg p-6 border border-indigo-100">
			<div className="flex items-center justify-between mb-6">
				<div className="flex items-center gap-3">
					<div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-3 shadow-md">
						<Brain className="w-6 h-6 text-white" />
					</div>
					<h2 className="text-gray-900 font-medium">AI Prediction Module</h2>
				</div>
				<span className="text-[10px] text-gray-400">
					Last update: {predictionData.created_at ? new Date(predictionData.created_at).toLocaleString() : 'N/A'}
				</span>
			</div>

			<div className="space-y-6">
				{/* Water Quality Index */}
				<div className="bg-white rounded-xl p-5 shadow-sm">
					<div className="flex items-center justify-between mb-3">
						<span className="text-gray-900 font-medium">Water Quality Index (WQI)</span>
						<div className={`px-3 py-1 rounded-full text-xs ${
							wqi.score >= 90 ? 'bg-green-100 text-green-700' : 
							wqi.score >= 70 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
						}`}>
							{wqi.label}
						</div>
					</div>
					<div className="flex items-baseline gap-2 mb-4">
						<span className="text-indigo-600 text-5xl font-bold">{Math.round(wqi.score)}</span>
						<span className="text-gray-500">/100</span>
					</div>
					<div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
						<div 
							className="absolute inset-y-0 left-0 bg-gradient-to-r from-green-400 via-blue-400 to-indigo-500 rounded-full transition-all duration-1000"
							style={{ width: `${Math.min(100, Math.max(0, wqi.score))}%` }}
						></div>
					</div>
					<div className="flex justify-between mt-2 text-[10px] text-gray-400">
						<span>Unsafe</span>
						<span>Poor</span>
						<span>Moderate</span>
						<span>Good</span>
						<span>Excellent</span>
					</div>
				</div>

				{/* AI Contamination Alert */}
				<div className="bg-white rounded-xl p-5 shadow-sm">
					<div className="flex items-center gap-2 mb-3">
						<AlertTriangle className={`w-5 h-5 ${risk.status === 'Low Risk' ? 'text-green-500' : 'text-yellow-500'}`} />
						<span className="text-gray-900 font-medium">Contamination Risk</span>
					</div>
					<div className="flex items-center justify-between">
						<span className="text-gray-600 text-sm">Current Status</span>
						<span className={risk.status === 'Low Risk' ? 'text-green-600' : 'text-red-600'}>
							{risk.status}
						</span>
					</div>
					<div className="mt-3 flex gap-2">
						{/* Hiển thị thanh tiến trình dựa trên risk_level (0, 1, 2) */}
						<div className={`flex-1 h-2 rounded-full ${risk.risk_level >= 0 ? 'bg-green-400' : 'bg-gray-200'}`}></div>
						<div className={`flex-1 h-2 rounded-full ${risk.risk_level >= 1 ? 'bg-yellow-400' : 'bg-gray-200'}`}></div>
						<div className={`flex-1 h-2 rounded-full ${risk.risk_level >= 2 ? 'bg-red-400' : 'bg-gray-200'}`}></div>
					</div>
				</div>

				{/* 24h Forecast */}
				<div className="bg-white rounded-xl p-5 shadow-sm">
					<div className="flex items-center gap-2 mb-4">
						<TrendingUp className="w-5 h-5 text-indigo-500" />
						<span className="text-gray-900 font-medium">24h Forecast</span>
					</div>
					<div className="space-y-3">
						<div className="flex items-center justify-between">
							<span className="text-gray-600 text-sm">Quality Trend</span>
							<span className={`${forecast.trend === 'Stable' ? 'text-green-600' : 'text-yellow-600'} text-sm flex items-center gap-1`}>
								<TrendingUp className={`w-4 h-4 ${forecast.trend !== 'Stable' ? 'animate-pulse' : ''}`} />
								{forecast.trend}
							</span>
						</div>
						<div className="flex items-center justify-between">
							<span className="text-gray-600 text-sm">Predicted WQI Range</span>
							<span className="text-indigo-600 font-semibold">
								{Math.round(forecast.predicted_wqi_range[0])} - {Math.round(forecast.predicted_wqi_range[1])}
							</span>
						</div>
						<div className="flex items-center justify-between">
							<span className="text-gray-600 text-sm">Confidence</span>
							<span className="text-gray-900">{confidence.toFixed(1)}%</span>
						</div>
					</div>
				</div>

				{/* ML Model Info */}
				<div className="bg-indigo-100 rounded-xl p-4 border border-indigo-200">
					<div className="flex items-center justify-between text-sm">
						<span className="text-indigo-700 font-medium">Model: {forecast.model_used}</span>
						<span className="text-indigo-600">
							Accuracy: {(accuracy * 100).toFixed(1)}%
						</span>
					</div>
				</div>
			</div>
		</div>
	);
}