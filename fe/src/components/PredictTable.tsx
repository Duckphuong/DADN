import { useEffect, useState } from 'react';
import { getHistory } from '../services/api';
import { HistoryData } from '../types/water';

export default function PredictTable() {
    const [data, setData] = useState<HistoryData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const res = await getHistory();
            setData(res);
            setLoading(false);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <h2>Loading sensor data...</h2>;

    return (
        <div>
            <table border={1} cellPadding={8}>
                <thead>
                    <tr>
                        <th>Created At</th>
                        <th>pH</th>
                        <th>Temp</th>
                        <th>Turbidity</th>
                        <th>DO</th>
                        <th>BOD</th>
                        <th>CO2</th>
                        <th>Alkalinity</th>
                        <th>Hardness</th>
                        <th>Calcium</th>
                        <th>Ammonia</th>
                        <th>Nitrite</th>
                        <th>Phosphorus</th>
                        <th>H2S</th>
                        <th>Plankton</th>
                        <th>WQI</th>
                        <th>Risk</th>
                        <th>Forecast</th>
                    </tr>
                </thead>

                <tbody>
                    {data.map((d) => (
                        <tr key={d.id || d.created_at || Math.random()}>
                            <td>
                                {d.created_at
                                    ? new Date(d.created_at).toLocaleString()
                                    : ''}
                            </td>
                            <td>{d.pH}</td>
                            <td>{d.Temp}</td>
                            <td>{d.Turbidity}</td>
                            <td>{d.DO}</td>
                            <td>{d.BOD}</td>
                            <td>{d.CO2}</td>
                            <td>{d.Alkalinity}</td>
                            <td>{d.Hardness}</td>
                            <td>{d.Calcium}</td>
                            <td>{d.Ammonia}</td>
                            <td>{d.Nitrite}</td>
                            <td>{d.Phosphorus}</td>
                            <td>{d.H2S}</td>
                            <td>{d.Plankton}</td>
                            <td>{d.prediction.summary?.wqi?.label ?? '-'}</td>
                            <td>
                                {d.prediction.summary?.contamination_risk
                                    ?.status ?? '-'}
                            </td>
                            <td>
                                {d.prediction.summary?.forecast_24h
                                    ? `${d.prediction.summary.forecast_24h.trend} (${d.prediction.summary.forecast_24h.model_used}, ${d.prediction.summary.forecast_24h.confidence_score}%` +
                                      `, range ${d.prediction.summary.forecast_24h.predicted_wqi_range[0]}-${d.prediction.summary.forecast_24h.predicted_wqi_range[1]})`
                                    : '-'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
