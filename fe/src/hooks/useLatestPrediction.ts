import { useCallback, useEffect, useState } from 'react';
import { getHistory } from '../services/api';
import { HistoryData } from '../types/water';

interface UseLatestPredictionResult {
    latestPrediction: HistoryData | null;
    loading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
}

export function useLatestPrediction(
    sensorId?: string,
): UseLatestPredictionResult {
    const [latestPrediction, setLatestPrediction] =
        useState<HistoryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const history = await getHistory(sensorId);
            setLatestPrediction(history?.[0] || null);
        } catch (err) {
            console.error('Failed to fetch latest prediction history:', err);
            setError('Could not load prediction history');
            setLatestPrediction(null);
        } finally {
            setLoading(false);
        }
    }, [sensorId]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return {
        latestPrediction,
        loading,
        error,
        refresh,
    };
}
