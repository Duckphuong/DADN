export interface SensorData {
    Temp: number;
    Turbidity: number;
    DO: number;
    BOD: number;
    CO2: number;
    pH: number;
    Alkalinity: number;
    Hardness: number;
    Calcium: number;
    Ammonia: number;
    Nitrite: number;
    Phosphorus: number;
    H2S: number;
    Plankton: number;
}

export interface PredictionRisk {
    risk_level: number;
    status: string;
}

export interface Forecast24h {
    confidence_score: number;
    model_used: string;
    predicted_wqi_range: [number, number];
    trend: string;
}

export interface Wqi {
    label: string;
    max: number;
    score: number;
}

export interface Prediction {
    contamination_risk: PredictionRisk;
    forecast_24h: Forecast24h;
    wqi: Wqi;
}

export interface HistoryData {
    id: string;
    created_at?: string;
    Temp?: number;
    Turbidity?: number;
    DO?: number;
    BOD?: number;
    CO2?: number;
    pH?: number;
    Alkalinity?: number;
    Hardness?: number;
    Calcium?: number;
    Ammonia?: number;
    Nitrite?: number;
    Phosphorus?: number;
    H2S?: number;
    Plankton?: number;
    prediction?: Prediction;
}
