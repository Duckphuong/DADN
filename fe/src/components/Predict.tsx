import { useState, ChangeEvent } from 'react';
import ReactMarkdown from 'react-markdown';

import { SensorData } from '../types/water';
import { predictWater } from '../services/api';

interface PredictResult {
    best_model: string;
    models: any[];
    ensemble: any;
    summary: {
        wqi: {
            prediction: number;
            score: number;
            label: string;
        };
        risk: {
            status: string;
            level: number;
        };
        accuracy: number;
        metrics: any;
        forecast_24h: {
            trend: string;
            predicted_wqi_range: [number, number];
            model_used: string;
            confidence_score: number;
        };
        confidence: number;
        solution: string;
        weather: any;
        abnormal_parameters: {
            parameter: string;
            message: string;
        }[];
    };
}

function Predict() {
    const [data, setData] = useState<Record<string, string>>({
        'Nhiệt độ': '',
        pH: '',
        DO: '',
        'Độ dẫn': '',
        'Độ kiềm': '',
        'N-NO2': '',
        'N-NH4': '',
        'P-PO4': '',
        H2S: '',
        TSS: '',
        COD: '',
        'Aeromonas tổng số': '',
        Coliform: '',
    });

    const [result, setResult] = useState<PredictResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const fieldLabels: Array<keyof SensorData> = [
        'Nhiệt độ',
        'pH',
        'DO',
        'Độ dẫn',
        'Độ kiềm',
        'N-NO2',
        'N-NH4',
        'P-PO4',
        'H2S',
        'TSS',
        'COD',
        'Aeromonas tổng số',
        'Coliform',
    ];

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        setData({
            ...data,
            [e.target.name]: e.target.value,
        });
    };

    const predict = async () => {
        try {
            setLoading(true);
            setError(null);

            const formattedData = Object.fromEntries(
                Object.entries(data).map(([key, value]) => [
                    key,
                    value === '' ? 0 : Number(value),
                ]),
            );

            const res = await predictWater({
                idSensor: '69ea674c5d325453fddc1733',
                ...formattedData,
            });

            if (res.error) {
                setError(res.error);
                setResult(null);
            } else {
                setResult(res);
            }
        } catch (err: any) {
            const errorMsg =
                err.response?.data?.error ||
                err.message ||
                'Unknown error occurred';

            setError(errorMsg);
            setResult(null);

            console.error('Prediction error:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (label: string) => {
        switch (label) {
            case 'Excellent':
                return 'text-green-600 bg-green-100';
            case 'Good':
                return 'text-yellow-700 bg-yellow-100';
            case 'Poor':
                return 'text-red-600 bg-red-100';
            default:
                return 'text-gray-700 bg-gray-100';
        }
    };

    return (
        <div id="predict-section" className="min-h-screen bg-slate-100 p-8">
            <div className="mx-auto max-w-7xl">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-slate-800">
                        AI Water Monitoring System
                    </h1>

                    <p className="mt-2 text-slate-500">
                        Predict water quality using AI regression models
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* INPUT */}
                    <div className="rounded-2xl bg-white p-6 shadow-lg">
                        <h2 className="mb-6 text-2xl font-semibold text-slate-800">
                            Sensor Input
                        </h2>

                        <div className="grid grid-cols-3 gap-4 md:grid-cols-3">
                            {fieldLabels.map((key) => (
                                <div key={key} className="min-w-0">
                                    <label className="mb-2 block text-sm font-medium text-slate-700 truncate">
                                        {key}
                                    </label>

                                    <input
                                        type="number"
                                        step="any"
                                        name={key}
                                        value={data[key]}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                                    />
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={predict}
                            disabled={loading}
                            className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-4 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading
                                ? 'Predicting...'
                                : 'Predict Water Quality'}
                        </button>

                        {error && (
                            <div className="mt-6 rounded-xl border border-red-300 bg-red-100 p-4 text-red-700">
                                <h3 className="mb-1 font-semibold">Error</h3>
                                <p>{error}</p>
                            </div>
                        )}
                    </div>

                    {/* RESULT */}
                    <div className="rounded-2xl bg-white p-6 shadow-lg">
                        <h2 className="mb-6 text-2xl font-semibold text-slate-800">
                            Prediction Result
                        </h2>

                        {!result && (
                            <div className="flex h-125 items-center justify-center text-slate-400">
                                No prediction yet
                            </div>
                        )}

                        {result && (
                            <div className="space-y-5">
                                {/* WQI */}
                                <div className="rounded-2xl bg-slate-50 p-5">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm text-slate-500">
                                                Water Quality
                                            </p>

                                            <h3 className="mt-1 text-3xl font-bold text-slate-800">
                                                {result.summary.wqi.score.toFixed(
                                                    1,
                                                )}
                                                /100
                                            </h3>
                                        </div>

                                        <div
                                            className={`rounded-full px-4 py-2 text-sm font-semibold ${getStatusColor(
                                                result.summary.wqi.label,
                                            )}`}
                                        >
                                            {result.summary.wqi.label}
                                        </div>
                                    </div>
                                </div>

                                {/* RISK */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="rounded-xl bg-slate-50 p-4">
                                        <p className="text-sm text-slate-500">
                                            Risk Status
                                        </p>

                                        <h3 className="mt-2 text-xl font-bold text-slate-800">
                                            {result.summary.risk.status}
                                        </h3>
                                    </div>

                                    <div className="rounded-xl bg-slate-50 p-4">
                                        <p className="text-sm text-slate-500">
                                            Confidence
                                        </p>

                                        <h3 className="mt-2 text-xl font-bold text-slate-800">
                                            {result.summary.forecast_24h.confidence_score.toFixed(
                                                1,
                                            )}
                                            %
                                        </h3>
                                    </div>
                                </div>

                                {result.summary.abnormal_parameters?.length >
                                    0 && (
                                    <div className="col-span-2 mt-4">
                                        <p className="text-xs text-slate-500 mb-3">
                                            {
                                                result.summary
                                                    .abnormal_parameters.length
                                            }{' '}
                                            tham số vượt ngưỡng
                                        </p>

                                        <div className="space-y-2">
                                            {result.summary.abnormal_parameters.map(
                                                (item: any, index: number) => (
                                                    <div
                                                        key={index}
                                                        className={`rounded-xl border p-3 ${
                                                            item.status ===
                                                            'above_safe'
                                                                ? 'bg-red-50 border-red-200'
                                                                : 'bg-yellow-50 border-yellow-200'
                                                        }`}
                                                    >
                                                        <div className="flex items-start justify-between gap-3">
                                                            <div>
                                                                <p className="font-medium text-slate-800">
                                                                    {
                                                                        item.parameter
                                                                    }
                                                                </p>

                                                                <p className="text-sm text-slate-600 mt-1">
                                                                    {
                                                                        item.message
                                                                    }
                                                                </p>
                                                            </div>

                                                            <span
                                                                className={`text-xs px-2 py-1 rounded-full font-medium ${
                                                                    item.status ===
                                                                    'above_safe'
                                                                        ? 'bg-red-100 text-red-700'
                                                                        : 'bg-yellow-100 text-yellow-700'
                                                                }`}
                                                            >
                                                                {item.status ===
                                                                'above_safe'
                                                                    ? 'Vượt ngưỡng'
                                                                    : 'Dưới ngưỡng'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ),
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* FORECAST */}
                                <div className="rounded-xl bg-slate-50 p-5">
                                    <h3 className="mb-4 text-lg font-semibold text-slate-800">
                                        24h Forecast
                                    </h3>

                                    <div className="space-y-2 text-slate-700">
                                        <p>
                                            <strong>Trend:</strong>{' '}
                                            {result.summary.forecast_24h.trend}
                                        </p>

                                        <p>
                                            <strong>Model:</strong>{' '}
                                            {
                                                result.summary.forecast_24h
                                                    .model_used
                                            }
                                        </p>

                                        <p>
                                            <strong>WQI Range:</strong>{' '}
                                            {result.summary.forecast_24h.predicted_wqi_range[0].toFixed(
                                                1,
                                            )}{' '}
                                            -
                                            {result.summary.forecast_24h.predicted_wqi_range[1].toFixed(
                                                1,
                                            )}
                                        </p>
                                    </div>
                                </div>

                                {/* SOLUTION */}
                                {result.summary.solution && (
                                    <div className="rounded-xl bg-blue-50 p-5">
                                        <h3 className="mb-3 text-lg font-semibold text-blue-800">
                                            Solution & Recommendation
                                        </h3>

                                        <div className="max-w-none">
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <h1
                                                            className="text-3xl font-extrabold mb-5 text-slate-900"
                                                            {...props}
                                                        />
                                                    ),

                                                    h2: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <h2
                                                            className="
                                                                                                                        text-2xl
                                                                                                                        font-extrabold
                                                                                                                        mt-8
                                                                                                                        mb-4
                                                                                                                        text-slate-800
                                                                                                                        border-l-4
                                                                                                                        border-cyan-500
                                                                                                                        pl-4
                                                                                                                    "
                                                            {...props}
                                                        />
                                                    ),

                                                    h3: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <h3
                                                            className="
                                                                                                                        text-xl
                                                                                                                        font-bold
                                                                                                                        mt-5
                                                                                                                        mb-3
                                                                                                                        text-slate-700
                                                                                                                    "
                                                            {...props}
                                                        />
                                                    ),

                                                    p: ({ node, ...props }) => (
                                                        <p
                                                            className="
                                                                                                                        text-base
                                                                                                                        leading-7
                                                                                                                        mb-3
                                                                                                                        text-slate-700
                                                                                                                    "
                                                            {...props}
                                                        />
                                                    ),

                                                    ul: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <ul
                                                            className="
                                                                                                                        list-disc
                                                                                                                        pl-6
                                                                                                                        mb-4
                                                                                                                        space-y-2
                                                                                                                    "
                                                            {...props}
                                                        />
                                                    ),

                                                    li: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <li
                                                            className="
                                                                                                                        text-base
                                                                                                                        text-slate-700
                                                                                                                    "
                                                            {...props}
                                                        />
                                                    ),

                                                    strong: ({
                                                        node,
                                                        ...props
                                                    }) => (
                                                        <strong
                                                            className="font-bold text-slate-900"
                                                            {...props}
                                                        />
                                                    ),
                                                }}
                                            >
                                                {result.summary.solution}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                )}

                                {/* WEATHER */}
                                {result.summary.weather && (
                                    <div className="rounded-xl bg-green-50 p-5">
                                        <h3 className="mb-3 text-lg font-semibold text-green-800">
                                            Weather Information
                                        </h3>

                                        <div className="grid grid-cols-2 gap-4 text-slate-700">
                                            <div>
                                                <p className="text-sm text-slate-500">
                                                    Temperature
                                                </p>

                                                <p className="font-semibold">
                                                    {
                                                        result.summary.weather
                                                            .avg_temperature_c
                                                    }
                                                    °C
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm text-slate-500">
                                                    Humidity
                                                </p>

                                                <p className="font-semibold">
                                                    {
                                                        result.summary.weather
                                                            .avg_humidity_pct
                                                    }
                                                    %
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm text-slate-500">
                                                    Rainfall
                                                </p>

                                                <p className="font-semibold">
                                                    {
                                                        result.summary.weather
                                                            .total_precipitation_mm
                                                    }
                                                    mm
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm text-slate-500">
                                                    Wind Speed
                                                </p>

                                                <p className="font-semibold">
                                                    {
                                                        result.summary.weather
                                                            .max_wind_speed_kmh
                                                    }{' '}
                                                    km/h
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Predict;
