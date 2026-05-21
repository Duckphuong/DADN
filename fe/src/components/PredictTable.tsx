import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { getHistory } from '../services/api';
import { HistoryData } from '../types/water';
export default function PredictTable() {
    const [data, setData] = useState<HistoryData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedRowId, setSelectedRowId] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const res = await getHistory();
            setData(res);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to load history');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const getWqiColor = (label?: string) => {
        switch (label) {
            case 'Excellent':
                return 'bg-green-100 text-green-700';
            case 'Good':
                return 'bg-yellow-100 text-yellow-700';
            case 'Poor':
                return 'bg-red-100 text-red-700';
            default:
                return 'bg-gray-100 text-gray-700';
        }
    };

    const getScoreColor = (score?: string) => {
        if (score === undefined) return 'bg-gray-100 text-gray-700';

        const s = parseFloat(score);
        if (s >= 80) {
            return 'bg-green-100 text-green-700';
        } else if (s >= 50) {
            return 'bg-yellow-100 text-yellow-700';
        } else {
            return 'bg-red-100 text-red-700';
        }
    };

    if (loading) {
        return (
            <div className="flex h-40 items-center justify-center">
                <div className="text-lg font-semibold text-slate-600">
                    Loading sensor data...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-xl border border-red-300 bg-red-100 p-5 text-red-700">
                <h2 className="mb-2 text-lg font-semibold">
                    Failed to load data
                </h2>

                <p>{error}</p>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="rounded-xl bg-white p-10 text-center shadow">
                <p className="text-slate-500">
                    No prediction history available.
                </p>
            </div>
        );
    }

    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedData = data.slice(startIndex, endIndex);

    return (
        <div
            id="predict-table-section"
            className="min-h-screen bg-slate-100 p-6"
        >
            <div className="mx-auto ">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-slate-800">
                        Prediction History
                    </h1>

                    <p className="mt-1 text-slate-500">
                        Water quality monitoring records
                    </p>
                </div>

                <div className="overflow-x-auto rounded-2xl bg-white shadow-lg">
                    <table className="min-w-full text-sm">
                        <thead className="bg-slate-800 text-white">
                            <tr>
                                <th className="px-4 py-4 text-left whitespace-nowrap">
                                    Thời gian
                                </th>

                                <th className="px-4 py-4">Nhiệt độ</th>
                                <th className="px-4 py-4">pH</th>
                                <th className="px-4 py-4">DO</th>
                                <th className="px-4 py-4">Độ dẫn</th>
                                <th className="px-4 py-4">Độ kiềm</th>
                                <th className="px-4 py-4">N-NO2</th>
                                <th className="px-4 py-4">N-NH4</th>
                                <th className="px-4 py-4">P-PO4</th>
                                <th className="px-4 py-4">H2S</th>
                                <th className="px-4 py-4">TSS</th>
                                <th className="px-4 py-4">COD</th>
                                <th className="px-4 py-4 whitespace-nowrap">
                                    Aeromonas tổng số
                                </th>
                                <th className="px-4 py-4">Coliform</th>
                                <th className="px-4 py-4">Điểm WQI</th>
                                <th className="px-4 py-4">Phân loại</th>
                                <th className="px-4 py-4 min-w-[300px]">
                                    Dự báo
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            {paginatedData.map((d, index) => {
                                const pred = d.prediction as any;
                                const summary = pred?.summary;
                                const rowId =
                                    d.id ||
                                    d.created_at ||
                                    Math.random().toString();
                                const isSelected = selectedRowId === rowId;

                                return (
                                    <>
                                        <tr
                                            key={rowId}
                                            onClick={() =>
                                                setSelectedRowId(
                                                    isSelected ? null : rowId,
                                                )
                                            }
                                            className={`border-b border-slate-200 transition cursor-pointer hover:bg-blue-50 ${
                                                isSelected
                                                    ? 'bg-blue-100'
                                                    : index % 2 === 0
                                                      ? 'bg-white'
                                                      : 'bg-slate-50/50'
                                            }`}
                                        >
                                            <td className="px-4 py-4 whitespace-nowrap font-medium text-slate-700">
                                                {d.created_at
                                                    ? new Date(
                                                          d.created_at,
                                                      ).toLocaleString()
                                                    : '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['Nhiệt độ']?.toFixed(2) ??
                                                    '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.pH?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.DO?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['Độ dẫn']?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['Độ kiềm']?.toFixed(2) ??
                                                    '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['N-NO2']?.toFixed(3) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['N-NH4']?.toFixed(3) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d['P-PO4']?.toFixed(3) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.H2S?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.TSS?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.COD?.toFixed(2) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d[
                                                    'Aeromonas tổng số'
                                                ]?.toFixed(0) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                {d.Coliform?.toFixed(0) ?? '-'}
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                <span
                                                    className={`rounded-full px-3 py-1 text-xs font-semibold ${getScoreColor(
                                                        (summary?.wqi?.score).toFixed(
                                                            1,
                                                        ),
                                                    )}`}
                                                >
                                                    {summary?.wqi?.score?.toFixed(
                                                        1,
                                                    ) ?? '-'}
                                                </span>
                                            </td>

                                            <td className="px-4 py-4 text-center">
                                                <span
                                                    className={`rounded-full px-3 py-1 text-xs font-semibold ${getWqiColor(
                                                        summary?.wqi?.label,
                                                    )}`}
                                                >
                                                    {summary?.wqi?.label ?? '-'}
                                                </span>
                                            </td>

                                            <td className="px-4 py-4 text-slate-700">
                                                {summary?.forecast_24h ? (
                                                    <div className="space-y-1">
                                                        <p>
                                                            <span className="font-semibold">
                                                                Trend:
                                                            </span>{' '}
                                                            {
                                                                summary
                                                                    .forecast_24h
                                                                    .trend
                                                            }
                                                        </p>

                                                        <p>
                                                            <span className="font-semibold">
                                                                Model:
                                                            </span>{' '}
                                                            {
                                                                summary
                                                                    .forecast_24h
                                                                    .model_used
                                                            }
                                                        </p>

                                                        <p>
                                                            <span className="font-semibold">
                                                                Confidence:
                                                            </span>{' '}
                                                            {summary.forecast_24h.confidence_score?.toFixed(
                                                                1,
                                                            )}
                                                            %
                                                        </p>

                                                        <p>
                                                            <span className="font-semibold">
                                                                Range:
                                                            </span>{' '}
                                                            {summary.forecast_24h.predicted_wqi_range[0]?.toFixed(
                                                                1,
                                                            )}{' '}
                                                            -
                                                            {summary.forecast_24h.predicted_wqi_range[1]?.toFixed(
                                                                1,
                                                            )}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    '-'
                                                )}
                                            </td>
                                        </tr>
                                        {isSelected && summary?.solution && (
                                            <tr className="border-b border-slate-200 bg-blue-50">
                                                <td
                                                    colSpan={17}
                                                    className="px-6 py-6"
                                                >
                                                    <div className="rounded-xl bg-white p-6 shadow-md border border-blue-200">
                                                        <h3 className="mb-4 text-2xl font-extrabold text-slate-800">
                                                            💡 Solution &
                                                            Recommendation
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

                                                                    p: ({
                                                                        node,
                                                                        ...props
                                                                    }) => (
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
                                                                {
                                                                    summary.solution
                                                                }
                                                            </ReactMarkdown>
                                                        </div>
                                                        {summary.wqi && (
                                                            <div className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-200 pt-4 md:grid-cols-4">
                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Water
                                                                        Quality
                                                                    </p>
                                                                    <p className="mt-1 text-lg font-bold text-slate-800">
                                                                        {summary.wqi.score?.toFixed(
                                                                            1,
                                                                        ) ||
                                                                            '-'}
                                                                        /100
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Status
                                                                    </p>
                                                                    <p
                                                                        className={`mt-1 font-bold ${
                                                                            summary
                                                                                .wqi
                                                                                .label ===
                                                                            'Excellent'
                                                                                ? 'text-green-600'
                                                                                : summary
                                                                                        .wqi
                                                                                        .label ===
                                                                                    'Good'
                                                                                  ? 'text-yellow-600'
                                                                                  : 'text-red-600'
                                                                        }`}
                                                                    >
                                                                        {summary
                                                                            .wqi
                                                                            .label ||
                                                                            '-'}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Risk
                                                                    </p>
                                                                    <p className="mt-1 font-bold text-slate-800">
                                                                        {summary
                                                                            .risk
                                                                            ?.status ||
                                                                            '-'}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Confidence
                                                                    </p>
                                                                    <p className="mt-1 font-bold text-slate-800">
                                                                        {summary.forecast_24h?.confidence_score?.toFixed(
                                                                            1,
                                                                        ) ||
                                                                            '-'}
                                                                        %
                                                                    </p>
                                                                </div>
                                                                {summary
                                                                    .abnormal_parameters
                                                                    ?.length >
                                                                    0 && (
                                                                    <div className="col-span-2 mt-4">
                                                                        <p className="text-xs text-slate-500 mb-3">
                                                                            {
                                                                                summary
                                                                                    .abnormal_parameters
                                                                                    .length
                                                                            }{' '}
                                                                            tham
                                                                            số
                                                                            vượt
                                                                            ngưỡng
                                                                        </p>

                                                                        <div className="space-y-2">
                                                                            {summary.abnormal_parameters.map(
                                                                                (
                                                                                    item: any,
                                                                                    index: number,
                                                                                ) => (
                                                                                    <div
                                                                                        key={
                                                                                            index
                                                                                        }
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
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                <div className="mt-6 flex items-center justify-between">
                    <div className="text-sm text-slate-600">
                        Showing{' '}
                        <span className="font-semibold">{startIndex + 1}</span>{' '}
                        to{' '}
                        <span className="font-semibold">
                            {Math.min(endIndex, data.length)}
                        </span>{' '}
                        of <span className="font-semibold">{data.length}</span>{' '}
                        records
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() =>
                                setCurrentPage(Math.max(1, currentPage - 1))
                            }
                            disabled={currentPage === 1}
                            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            Previous
                        </button>

                        <div className="flex items-center gap-1">
                            {Array.from(
                                { length: totalPages },
                                (_, i) => i + 1,
                            ).map((page) => (
                                <button
                                    key={page}
                                    onClick={() => setCurrentPage(page)}
                                    className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                                        currentPage === page
                                            ? 'bg-blue-600 text-white'
                                            : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                                    }`}
                                >
                                    {page}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={() =>
                                setCurrentPage(
                                    Math.min(totalPages, currentPage + 1),
                                )
                            }
                            disabled={currentPage === totalPages}
                            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
