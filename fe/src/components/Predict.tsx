import { useState, ChangeEvent } from 'react';
import { SensorData } from '../types/water';
import { predictWater } from '../services/api';

interface PredictResult {
    contamination_risk: {
        risk_level: number;
        status: string;
    };
    forecast_24h: {
        confidence_score: number;
        model_used: string;
        predicted_wqi_range: [number, number];
        trend: string;
    };
    wqi: {
        label: string;
        max: number;
        score: number;
    };
}

function Predict() {
    const [data, setData] = useState<SensorData>({
        Temp: 0,
        Turbidity: 0,
        DO: 0,
        BOD: 0,
        CO2: 0,
        pH: 0,
        Alkalinity: 0,
        Hardness: 0,
        Calcium: 0,
        Ammonia: 0,
        Nitrite: 0,
        Phosphorus: 0,
        H2S: 0,
        Plankton: 0,
    });

    const [result, setResult] = useState<PredictResult | null>(null);

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        setData({
            ...data,
            [e.target.name]: Number(e.target.value),
        });
    };

    const predict = async () => {
        try {
            const res = await predictWater(data);
            setResult(res);
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div style={{ padding: '40px' }}>
            <h1>AI Water Monitoring System</h1>

            <h3>Sensor Input</h3>

            {Object.keys(data).map((key) => (
                <div key={key}>
                    <label>{key}: </label>

                    <input
                        type="number"
                        name={key}
                        value={data[key as keyof SensorData]}
                        onChange={handleChange}
                    />
                </div>
            ))}

            <br />

            <button className="border border-gray-200" onClick={predict}>
                Predict Water Quality
            </button>

            {result && (
                <div style={{ marginTop: '30px' }}>
                    <h2>Prediction Result</h2>

                    <p>
                        WQI: <strong>{result.wqi.label}</strong> (score:{' '}
                        {result.wqi.score}/{result.wqi.max})
                    </p>

                    <p>
                        Contamination risk:{' '}
                        <strong>{result.contamination_risk.status}</strong>
                        (level: {result.contamination_risk.risk_level})
                    </p>

                    <p>Forecast trend: {result.forecast_24h.trend}</p>
                    <p>Model used: {result.forecast_24h.model_used}</p>
                    <p>Confidence: {result.forecast_24h.confidence_score}%</p>
                    <p>
                        Predicted WQI range:{' '}
                        {result.forecast_24h.predicted_wqi_range[0]} -{' '}
                        {result.forecast_24h.predicted_wqi_range[1]}
                    </p>
                </div>
            )}
        </div>
    );
}

export default Predict;
