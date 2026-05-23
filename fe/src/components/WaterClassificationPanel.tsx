// import { useEffect, useState } from 'react';
// import { Filter, Loader2 } from 'lucide-react';
// import { getHistory } from '../services/api';
// import { HistoryData } from '../types/water';

// interface WaterClassificationPanelProps {
//     historyItem?: HistoryData | null;
// }

// export function WaterClassificationPanel({
//     historyItem,
// }: WaterClassificationPanelProps) {
//     const [data, setData] = useState<HistoryData | null>(null);
//     const [loading, setLoading] = useState(true);
//     const [error, setError] = useState<string | null>(null);

//     useEffect(() => {
//         if (historyItem) {
//             setData(historyItem);
//             setLoading(false);
//             setError(null);
//             return;
//         }

//         const fetchLatestData = async () => {
//             try {
//                 setLoading(true);

//                 const history = await getHistory();

//                 if (history && history.length > 0) {
//                     setData(history[0]);
//                 }
//             } catch (err) {
//                 console.error('Error fetching sensor data:', err);
//                 setError('Could not load water classification data');
//             } finally {
//                 setLoading(false);
//             }
//         };

//         fetchLatestData();
//     }, [historyItem]);

//     if (loading) {
//         return (
//             <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 flex items-center justify-center min-h-[400px]">
//                 <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
//                 <span className="ml-3 text-gray-500">
//                     Loading water classification...
//                 </span>
//             </div>
//         );
//     }

//     if (error || !data) {
//         return (
//             <div className="bg-red-50 rounded-2xl border border-red-100 p-6 text-red-600">
//                 {error || 'No sensor data available.'}
//             </div>
//         );
//     }

//     // =========================
//     // SENSOR VALUES
//     // =========================
//     const ph = Number(data.pH || 0);
//     const doValue = Number(data.DO || 0);
//     const temperature = Number(data['Nhiệt độ'] || 0);
//     const alkalinity = Number(data['Độ kiềm'] || 0);

//     // =========================
//     // WATER HARDNESS
//     // =========================
//     const hardnessCategory =
//         alkalinity >= 180
//             ? 'Hard Water'
//             : alkalinity >= 80
//               ? 'Moderate Water'
//               : 'Soft Water';

//     // =========================
//     // TEMPERATURE STATUS
//     // =========================
//     const temperatureStatus =
//         temperature < 20 ? 'Cold' : temperature <= 32 ? 'Safe' : 'Hot';

//     // =========================
//     // ALKALINITY LEVEL
//     // =========================
//     const alkalinityLevel =
//         alkalinity < 80 ? 'Low' : alkalinity <= 180 ? 'Moderate' : 'High';

//     // =========================
//     // HELPERS
//     // =========================
//     const getWidthPercent = (level: string, options: string[]): string => {
//         const index = options.indexOf(level);

//         if (index === 0) return '33%';
//         if (index === 1) return '66%';
//         if (index === 2) return '100%';

//         return '0%';
//     };

//     return (
//         <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
//             {/* HEADER */}
//             <div className="flex items-center justify-between mb-6">
//                 <div className="flex items-center gap-3">
//                     <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-3 shadow-md">
//                         <Filter className="w-6 h-6 text-white" />
//                     </div>

//                     <h2 className="text-gray-900 font-medium">
//                         Water Classification
//                     </h2>
//                 </div>

//                 <span className="text-[10px] text-gray-400">
//                     Last update:{' '}
//                     {data.created_at
//                         ? new Date(data.created_at).toLocaleString()
//                         : 'N/A'}
//                 </span>
//             </div>

//             <div className="space-y-8">
//                 {/* WATER TYPE */}
//                 <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
//                     <div className="flex items-center justify-between mb-4">
//                         <span className="text-gray-900 font-medium">
//                             Water Type
//                         </span>

//                         <span
//                             className={`font-medium ${
//                                 hardnessCategory === 'Hard Water'
//                                     ? 'text-blue-600'
//                                     : hardnessCategory === 'Soft Water'
//                                       ? 'text-cyan-600'
//                                       : 'text-yellow-600'
//                             }`}
//                         >
//                             {hardnessCategory}
//                         </span>
//                     </div>

//                     <div className="grid grid-cols-2 gap-4">
//                         <div
//                             className={`rounded-xl p-4 text-center transition-all ${
//                                 hardnessCategory === 'Hard Water'
//                                     ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
//                                     : 'bg-gray-100 text-gray-400'
//                             }`}
//                         >
//                             <div className="text-sm mb-1">Hard Water</div>

//                             <div className="text-2xl font-semibold">
//                                 {hardnessCategory === 'Hard Water'
//                                     ? `${alkalinity.toFixed(1)} mg/L`
//                                     : '--'}
//                             </div>
//                         </div>

//                         <div
//                             className={`rounded-xl p-4 text-center transition-all ${
//                                 hardnessCategory === 'Soft Water'
//                                     ? 'bg-gradient-to-r from-green-400 to-cyan-500 text-white'
//                                     : 'bg-gray-100 text-gray-400'
//                             }`}
//                         >
//                             <div className="text-sm mb-1">Soft Water</div>

//                             <div className="text-2xl font-semibold">
//                                 {hardnessCategory === 'Soft Water'
//                                     ? `${alkalinity.toFixed(1)} mg/L`
//                                     : '--'}
//                             </div>
//                         </div>
//                     </div>
//                 </div>

//                 {/* ALKALINITY */}
//                 <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
//                     <div className="flex items-center justify-between mb-3">
//                         <span className="text-gray-900 font-medium">
//                             Alkalinity Level
//                         </span>

//                         <span className="text-indigo-600 font-medium">
//                             {alkalinityLevel}
//                         </span>
//                     </div>

//                     <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
//                         <div
//                             className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 rounded-full transition-all duration-700"
//                             style={{
//                                 width: getWidthPercent(alkalinityLevel, [
//                                     'Low',
//                                     'Moderate',
//                                     'High',
//                                 ]),
//                             }}
//                         />

//                         <div className="absolute inset-0 flex items-center justify-center">
//                             <span className="text-xs text-gray-700 z-10 font-medium">
//                                 {alkalinity.toFixed(1)} mg/L
//                             </span>
//                         </div>
//                     </div>

//                     <div className="flex justify-between text-xs text-gray-400 mt-2">
//                         <span>Low</span>
//                         <span>Moderate</span>
//                         <span>High</span>
//                     </div>
//                 </div>

//                 {/* TEMPERATURE */}
//                 <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
//                     <div className="flex items-center justify-between mb-3">
//                         <span className="text-gray-900 font-medium">
//                             Temperature Level
//                         </span>

//                         <span
//                             className={`font-medium ${
//                                 temperatureStatus === 'Safe'
//                                     ? 'text-green-600'
//                                     : temperatureStatus === 'Hot'
//                                       ? 'text-red-600'
//                                       : 'text-blue-600'
//                             }`}
//                         >
//                             {temperatureStatus}
//                         </span>
//                     </div>

//                     <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
//                         <div
//                             className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-400 via-green-400 to-orange-400 rounded-full transition-all duration-700"
//                             style={{
//                                 width: getWidthPercent(temperatureStatus, [
//                                     'Cold',
//                                     'Safe',
//                                     'Hot',
//                                 ]),
//                             }}
//                         />

//                         <div className="absolute inset-0 flex items-center justify-center">
//                             <span className="text-xs text-gray-700 z-10 font-medium">
//                                 {temperature.toFixed(1)} °C
//                             </span>
//                         </div>
//                     </div>

//                     <div className="flex justify-between text-xs text-gray-400 mt-2">
//                         <span>Cold</span>
//                         <span>Safe</span>
//                         <span>Hot</span>
//                     </div>
//                 </div>

//                 {/* PH + DO */}
//                 <div className="grid grid-cols-2 gap-4">
//                     {/* PH */}
//                     <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 text-center">
//                         <div className="relative w-28 h-28 mx-auto mb-3">
//                             <svg className="w-full h-full transform -rotate-90">
//                                 <circle
//                                     cx="56"
//                                     cy="56"
//                                     r="46"
//                                     stroke="#e5e7eb"
//                                     strokeWidth="10"
//                                     fill="none"
//                                 />

//                                 <circle
//                                     cx="56"
//                                     cy="56"
//                                     r="46"
//                                     stroke="url(#gradientPH)"
//                                     strokeWidth="10"
//                                     fill="none"
//                                     strokeDasharray={`${(ph / 14) * 289} 289`}
//                                     strokeLinecap="round"
//                                     className="transition-all duration-1000"
//                                 />

//                                 <defs>
//                                     <linearGradient
//                                         id="gradientPH"
//                                         x1="0%"
//                                         y1="0%"
//                                         x2="100%"
//                                         y2="0%"
//                                     >
//                                         <stop offset="0%" stopColor="#06b6d4" />
//                                         <stop
//                                             offset="100%"
//                                             stopColor="#3b82f6"
//                                         />
//                                     </linearGradient>
//                                 </defs>
//                             </svg>

//                             <div className="absolute inset-0 flex items-center justify-center">
//                                 <span className="text-2xl font-bold text-gray-800">
//                                     {ph.toFixed(1)}
//                                 </span>
//                             </div>
//                         </div>

//                         <span className="text-gray-600 text-sm font-medium">
//                             pH Level
//                         </span>
//                     </div>

//                     {/* DO */}
//                     <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 text-center">
//                         <div className="relative w-28 h-28 mx-auto mb-3">
//                             <svg className="w-full h-full transform -rotate-90">
//                                 <circle
//                                     cx="56"
//                                     cy="56"
//                                     r="46"
//                                     stroke="#e5e7eb"
//                                     strokeWidth="10"
//                                     fill="none"
//                                 />

//                                 <circle
//                                     cx="56"
//                                     cy="56"
//                                     r="46"
//                                     stroke="url(#gradientDO)"
//                                     strokeWidth="10"
//                                     fill="none"
//                                     strokeDasharray={`${
//                                         (doValue / 15) * 289
//                                     } 289`}
//                                     strokeLinecap="round"
//                                     className="transition-all duration-1000"
//                                 />

//                                 <defs>
//                                     <linearGradient
//                                         id="gradientDO"
//                                         x1="0%"
//                                         y1="0%"
//                                         x2="100%"
//                                         y2="0%"
//                                     >
//                                         <stop offset="0%" stopColor="#10b981" />
//                                         <stop
//                                             offset="100%"
//                                             stopColor="#06b6d4"
//                                         />
//                                     </linearGradient>
//                                 </defs>
//                             </svg>

//                             <div className="absolute inset-0 flex items-center justify-center">
//                                 <span className="text-2xl font-bold text-gray-800">
//                                     {doValue.toFixed(1)}
//                                 </span>
//                             </div>
//                         </div>

//                         <span className="text-gray-600 text-sm font-medium">
//                             DO Level
//                         </span>
//                     </div>
//                 </div>
//             </div>
//         </div>
//     );
// }

import { useEffect, useState } from 'react';
import {
    Filter,
    Loader2,
    ShieldCheck,
    Waves,
    Biohazard,
    FlaskConical,
} from 'lucide-react';

import { getHistory } from '../services/api';
import { HistoryData } from '../types/water';

interface WaterClassificationPanelProps {
    historyItem?: HistoryData | null;
}

export function WaterClassificationPanel({
    historyItem,
}: WaterClassificationPanelProps) {
    const [data, setData] = useState<HistoryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (historyItem) {
            setData(historyItem);
            setLoading(false);
            setError(null);
            return;
        }

        const fetchLatestData = async () => {
            try {
                setLoading(true);

                const history = await getHistory();

                if (history && history.length > 0) {
                    setData(history[0]);
                }
            } catch (err) {
                console.error('Error fetching sensor data:', err);
                setError('Could not load water classification data');
            } finally {
                setLoading(false);
            }
        };

        fetchLatestData();
    }, [historyItem]);

    if (loading) {
        return (
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 flex items-center justify-center min-h-[400px]">
                <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
                <span className="ml-3 text-gray-500">
                    Loading water classification...
                </span>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-red-50 rounded-2xl border border-red-100 p-6 text-red-600">
                {error || 'No sensor data available.'}
            </div>
        );
    }

    // =========================================
    // SENSOR VALUES
    // =========================================
    const ph = Number(data.pH || 0);
    const doValue = Number(data.DO || 0);
    const temperature = Number(data['Nhiệt độ'] || 0);

    const nh4 = Number(data['N-NH4'] || 0);
    const no2 = Number(data['N-NO2'] || 0);
    const po4 = Number(data['P-PO4'] || 0);

    const cod = Number(data.COD || 0);
    const tss = Number(data.TSS || 0);

    const h2s = Number(data.H2S || 0);

    const coliform = Number(data.Coliform || 0);
    const aeromonas = Number(data['Aeromonas tổng số'] || 0);

    // =========================================
    // WATER TYPE
    // =========================================
    let waterType = 'Balanced Water';

    if (tss > 50 || cod > 30) {
        waterType = 'Polluted Water';
    } else if (ph < 6.5 || ph > 8.5) {
        waterType = 'Unstable Water';
    }

    // =========================================
    // BIOLOGICAL SAFETY
    // =========================================
    let bioStatus = 'Safe';
    let bioColor = 'text-green-600';
    let bioBg = 'bg-green-50';

    if (coliform > 5000 || aeromonas > 1000) {
        bioStatus = 'Dangerous';
        bioColor = 'text-red-600';
        bioBg = 'bg-red-50';
    } else if (coliform > 1000 || aeromonas > 300) {
        bioStatus = 'Warning';
        bioColor = 'text-yellow-600';
        bioBg = 'bg-yellow-50';
    }

    // =========================================
    // NUTRIENT POLLUTION
    // =========================================
    const nutrientScore = nh4 + no2 + po4;

    let nutrientLevel = 'Low';
    let nutrientColor = 'text-green-600';
    let nutrientBg = 'bg-green-50';

    if (nutrientScore > 5) {
        nutrientLevel = 'High';
        nutrientColor = 'text-red-600';
        nutrientBg = 'bg-red-50';
    } else if (nutrientScore > 2) {
        nutrientLevel = 'Moderate';
        nutrientColor = 'text-yellow-600';
        nutrientBg = 'bg-yellow-50';
    }

    // =========================================
    // ORGANIC POLLUTION
    // =========================================
    let organicLevel = 'Clean';
    let organicColor = 'text-green-600';
    let organicBg = 'bg-green-50';

    if (cod > 30 || tss > 100) {
        organicLevel = 'Polluted';
        organicColor = 'text-red-600';
        organicBg = 'bg-red-50';
    } else if (cod > 15 || tss > 50) {
        organicLevel = 'Moderate';
        organicColor = 'text-yellow-600';
        organicBg = 'bg-yellow-50';
    }

    // =========================================
    // AQUACULTURE SUITABILITY
    // =========================================
    let suitability = 100;

    if (ph < 6.5 || ph > 8.5) suitability -= 20;
    if (doValue < 5) suitability -= 25;
    if (temperature < 20 || temperature > 32) suitability -= 15;
    if (nh4 > 1) suitability -= 20;
    if (h2s > 0.05) suitability -= 20;

    suitability = Math.max(0, suitability);

    return (
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            {/* HEADER */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-3 shadow-md">
                        <Filter className="w-6 h-6 text-white" />
                    </div>

                    <h2 className="text-gray-900 font-medium">
                        Water Classification
                    </h2>
                </div>

                <span className="text-[10px] text-gray-400">
                    Last update:{' '}
                    {data.created_at
                        ? new Date(data.created_at).toLocaleString()
                        : 'N/A'}
                </span>
            </div>

            <div className="space-y-5">
                {/* WATER TYPE */}
                <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-100 p-3 rounded-xl">
                                <Waves className="w-5 h-5 text-blue-600" />
                            </div>

                            <div>
                                <h3 className="font-medium text-gray-900">
                                    Water Type
                                </h3>

                                <p className="text-sm text-gray-500">
                                    Overall water condition
                                </p>
                            </div>
                        </div>

                        <span className="text-blue-600 font-semibold">
                            {waterType}
                        </span>
                    </div>
                </div>

                {/* BIOLOGICAL SAFETY */}
                <div
                    className={`rounded-xl p-5 border border-gray-200 shadow-sm ${bioBg}`}
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-white p-3 rounded-xl">
                                <Biohazard className={`w-5 h-5 ${bioColor}`} />
                            </div>

                            <div>
                                <h3 className="font-medium text-gray-900">
                                    Biological Safety
                                </h3>

                                <p className="text-sm text-gray-500">
                                    Coliform & Aeromonas analysis
                                </p>
                            </div>
                        </div>

                        <span className={`font-semibold ${bioColor}`}>
                            {bioStatus}
                        </span>
                    </div>
                </div>

                {/* NUTRIENT POLLUTION */}
                <div
                    className={`rounded-xl p-5 border border-gray-200 shadow-sm ${nutrientBg}`}
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-white p-3 rounded-xl">
                                <FlaskConical
                                    className={`w-5 h-5 ${nutrientColor}`}
                                />
                            </div>

                            <div>
                                <h3 className="font-medium text-gray-900">
                                    Nutrient Pollution
                                </h3>

                                <p className="text-sm text-gray-500">
                                    NH4, NO2 & PO4 concentration
                                </p>
                            </div>
                        </div>

                        <span className={`font-semibold ${nutrientColor}`}>
                            {nutrientLevel}
                        </span>
                    </div>
                </div>

                {/* ORGANIC POLLUTION */}
                <div
                    className={`rounded-xl p-5 border border-gray-200 shadow-sm ${organicBg}`}
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-white p-3 rounded-xl">
                                <Filter className={`w-5 h-5 ${organicColor}`} />
                            </div>

                            <div>
                                <h3 className="font-medium text-gray-900">
                                    Organic Pollution
                                </h3>

                                <p className="text-sm text-gray-500">
                                    COD & suspended solids analysis
                                </p>
                            </div>
                        </div>

                        <span className={`font-semibold ${organicColor}`}>
                            {organicLevel}
                        </span>
                    </div>
                </div>

                {/* AQUACULTURE SUITABILITY */}
                <div className="bg-indigo-50 rounded-xl p-5 border border-indigo-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="bg-white p-3 rounded-xl">
                                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                            </div>

                            <div>
                                <h3 className="font-medium text-gray-900">
                                    Aquaculture Suitability
                                </h3>

                                <p className="text-sm text-gray-500">
                                    AI-based environmental assessment
                                </p>
                            </div>
                        </div>

                        <span className="text-2xl font-bold text-indigo-600">
                            {suitability}%
                        </span>
                    </div>

                    <div className="relative h-3 bg-indigo-100 rounded-full overflow-hidden">
                        <div
                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 rounded-full transition-all duration-1000"
                            style={{
                                width: `${suitability}%`,
                            }}
                        />
                    </div>

                    <div className="flex justify-between mt-2 text-xs text-gray-400">
                        <span>Poor</span>
                        <span>Moderate</span>
                        <span>Excellent</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
