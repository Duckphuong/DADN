import React, {useEffect, useState } from 'react';
import { alertService } from '../services/api';
import { AlertTriangle, AlertCircle, Info, XCircle, Bell } from 'lucide-react';

const alerts = [
    {
        id: 1,
        type: 'critical',
        icon: XCircle,
        title: 'Low Dissolved Oxygen',
        message: 'Site D: DO level at 4.2 mg/L',
        time: '2 min ago',
        color: 'red',
    },
    {
        id: 2,
        type: 'warning',
        icon: AlertTriangle,
        title: 'High Turbidity',
        message: 'Site B: Turbidity at 8.5 NTU',
        time: '15 min ago',
        color: 'yellow',
    },
    {
        id: 3,
        type: 'warning',
        icon: AlertTriangle,
        title: 'High Conductivity',
        message: 'Site A: 1850 µS/cm detected',
        time: '1 hour ago',
        color: 'yellow',
    },
    {
        id: 4,
        type: 'info',
        icon: Info,
        title: 'Contamination Predicted',
        message: 'AI model predicts risk in 12h',
        time: '2 hours ago',
        color: 'blue',
    },
    {
        id: 5,
        type: 'warning',
        icon: AlertCircle,
        title: 'Unsafe pH Level',
        message: 'Site C: pH at 9.2 (alkaline)',
        time: '3 hours ago',
        color: 'orange',
    },
];

export function AlertsPanel() {
    return (
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 h-fit">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-gray-900">System Alerts</h2>
                <div className="relative">
                    <Bell className="w-5 h-5 text-gray-600" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white"></div>
                </div>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {alerts.map((alert) => {
                    const Icon = alert.icon;
                    const colorClasses = {
                        red: 'bg-red-50 border-red-200 text-red-700',
                        yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
                        orange: 'bg-orange-50 border-orange-200 text-orange-700',
                        blue: 'bg-blue-50 border-blue-200 text-blue-700',
                    };

                    const iconColorClasses = {
                        red: 'text-red-500',
                        yellow: 'text-yellow-500',
                        orange: 'text-orange-500',
                        blue: 'text-blue-500',
                    };

                    return (
                        <div
                            key={alert.id}
                            className={`${colorClasses[alert.color]} rounded-xl p-4 border transition-all duration-200 hover:shadow-md`}
                        >
                            <div className="flex items-start gap-3">
                                <Icon
                                    className={`w-5 h-5 mt-0.5 ${iconColorClasses[alert.color]} flex-shrink-0`}
                                />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm text-gray-900 mb-1">
                                        {alert.title}
                                    </div>
                                    <div className="text-xs text-gray-600 mb-2">
                                        {alert.message}
                                    </div>
                                    <div className="text-xs text-gray-400">
                                        {alert.time}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Alert Summary */}
            <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                        <div className="text-red-600 text-2xl">1</div>
                        <div className="text-xs text-gray-500 mt-1">
                            Critical
                        </div>
                    </div>
                    <div>
                        <div className="text-yellow-600 text-2xl">3</div>
                        <div className="text-xs text-gray-500 mt-1">
                            Warning
                        </div>
                    </div>
                    <div>
                        <div className="text-blue-600 text-2xl">1</div>
                        <div className="text-xs text-gray-500 mt-1">Info</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
