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
                        <th>Quality</th>
                        <th>Status</th>
                        <th>Temp</th>
                        <th>Turbidity</th>
                        <th>DO</th>
                        <th>BOD</th>
                        <th>CO2</th>
                        <th>pH</th>
                        <th>Alkalinity</th>
                        <th>Hardness</th>
                        <th>Calcium</th>
                        <th>Ammonia</th>
                        <th>Nitrite</th>
                        <th>Phosphorus</th>
                        <th>H2S</th>
                        <th>Plankton</th>
                    </tr>
                </thead>

                <tbody>
                    {data
                        .filter((d) => d.sensor_data)
                        .map((d) => (
                            <tr key={d._id}>
                                <td>{d.quality_label}</td>
                                <td
                                    style={{
                                        color:
                                            d.quality_name === 'Good'
                                                ? 'green'
                                                : d.quality_name === 'Moderate'
                                                  ? 'orange'
                                                  : 'red',
                                        fontWeight: 'bold',
                                    }}
                                >
                                    {d.quality_name}
                                </td>

                                <td>{d.sensor_data?.Temp}</td>
                                <td>{d.sensor_data?.Turbidity}</td>
                                <td>{d.sensor_data?.DO}</td>
                                <td>{d.sensor_data?.BOD}</td>
                                <td>{d.sensor_data?.CO2}</td>
                                <td>{d.sensor_data?.pH}</td>
                                <td>{d.sensor_data?.Alkalinity}</td>
                                <td>{d.sensor_data?.Hardness}</td>
                                <td>{d.sensor_data?.Calcium}</td>
                                <td>{d.sensor_data?.Ammonia}</td>
                                <td>{d.sensor_data?.Nitrite}</td>
                                <td>{d.sensor_data?.Phosphorus}</td>
                                <td>{d.sensor_data?.H2S}</td>
                                <td>{d.sensor_data?.Plankton}</td>
                            </tr>
                        ))}
                </tbody>
            </table>
        </div>
    );
}
