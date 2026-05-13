export interface SensorData {
    "Nhiệt độ": number;
    pH: number;
    DO: number;
    "Độ dẫn": number;
    "Độ kiềm": number;
    "N-NO2": number;
    "N-NH4": number;
    "P-PO4": number;
    H2S: number;
    TSS: number;
    COD: number;
    "Aeromonas tổng số": number;
    Coliform: number;
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
    "Nhiệt độ"?: number;
    DO?: number;
    pH?: number;
    "Độ dẫn"?: number;
    "Độ kiềm"?: number;
    "N-NO2"?: number;
    "N-NH4"?: number;
    "P-PO4"?: number;
    H2S?: number;
    TSS?: number;
    COD?: number;
    "Aeromonas tổng số"?: number;
    Coliform?: number;
    prediction?: Prediction;
}
