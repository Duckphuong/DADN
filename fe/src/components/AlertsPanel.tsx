import React, { useEffect, useState } from 'react';
import { alertService } from '../services/api';
import { AlertTriangle, AlertCircle, Info, XCircle, Bell, Loader2, Mail, } from 'lucide-react';

// Interface cho dữ liệu từ Backend (dựa trên alert_routes.py)
interface AlertItem {
  id: string;
  level: 'Critical' | 'Warning' | 'Info';
  message: string;
  time_ago: string;
  wqi_score: number;
  contamination_risk: string;
}

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEmailEnabled, setIsEmailEnabled] = useState(false);
  const [isUpdatingMail, setIsUpdatingMail] = useState(false);

  const fetchInitialData = async () => {
  try {
    setLoading(true);
    const [alertsData, emailSettings] = await Promise.all([
      alertService.getAlerts('unread'),
      alertService.getEmailSetting()
    ]);
    setAlerts(alertsData);
    setIsEmailEnabled(emailSettings.enabled);
  } catch (error) {
    console.error("Failed to fetch initial data:", error);
  } finally {
    setLoading(false);
  }
};

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const data = await alertService.getAlerts('unread');
      setAlerts(data);
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    const minutes = 15;
    const interval = setInterval(fetchAlerts, minutes * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Hàm xử lý tắt/bật tự động gửi mail
  const handleToggleEmail = async () => {
  try {
    setIsUpdatingMail(true);
    const nextStatus = !isEmailEnabled;
    const response = await alertService.updateEmailSetting(nextStatus);
    setIsEmailEnabled(response.enabled);
    // toast.success(response.message); 
  } catch (error) {
    console.error("Failed to update email setting:", error);
  } finally {
    setIsUpdatingMail(false);
  }
};

  // Hàm đánh dấu đã đọc
  const handleMarkAsRead = async (id: string) => {
    try {
      await alertService.markAsRead(id);
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch (error) {
      console.error("Failed to mark alert as read:", error);
    }
  };

  // Mapping cấu hình hiển thị dựa trên 'level' từ backend
  const getAlertConfig = (level: string) => {
    switch (level) {
      case 'Critical':
        return { icon: XCircle, color: 'red', title: 'Critical Alert' };
      case 'Warning':
        return { icon: AlertTriangle, color: 'yellow', title: 'System Warning' };
      default:
        return { icon: Info, color: 'blue', title: 'System Info' };
    }
  };

  // Tính toán số lượng cho phần Summary
  const summary = {
    critical: alerts.filter(a => a.level === 'Critical').length,
    warning: alerts.filter(a => a.level === 'Warning').length,
    info: alerts.filter(a => a.level === 'Info').length,
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 max-h-[550px]">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-gray-900 font-medium">System Alerts</h2>
        <div className="flex items-center gap-4">
          {/* Toggle Email Section */}
          <button
            onClick={handleToggleEmail}
            disabled={isUpdatingMail}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-300 ${
              isEmailEnabled 
                ? 'bg-green-50 border-green-200 text-green-700' 
                : 'bg-gray-50 border-gray-200 text-gray-500'
            }`}
            title={isEmailEnabled ? "Disable Email Alerts" : "Enable Email Alerts"}
          >
            {isUpdatingMail ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : isEmailEnabled ? (
              <Mail className="w-3.5 h-3.5" />
            ) : (
              <Mail className="w-3.5 h-3.5" />
            )}
            <span className="text-[11px] font-semibold uppercase tracking-tight">
              {isEmailEnabled ? 'Mail On' : 'Mail Off'}
            </span>
          </button>

          <div className="relative">
            <Bell className="w-5 h-5 text-gray-600" />
            {alerts.length > 0 && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white"></div>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
      {/* <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar"> */}
        {loading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-10 text-gray-400 text-sm italic">
            No unread alerts
          </div>
        ) : (
          alerts.map((alert) => {
            const config = getAlertConfig(alert.level);
            const Icon = config.icon;
            
            const colorClasses = {
              red: 'bg-red-50 border-red-200 text-red-700 hover:bg-red-100',
              yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100',
              blue: 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100',
            };

            const iconColorClasses = {
              red: 'text-red-500',
              yellow: 'text-yellow-500',
              blue: 'text-blue-500',
            };

            return (
              <div
                key={alert.id}
                onClick={() => handleMarkAsRead(alert.id)}
                className={`${colorClasses[config.color as keyof typeof colorClasses]} rounded-xl p-4 border transition-all duration-200 hover:shadow-md cursor-pointer group`}
                title="Click to mark as read"
              >
                <div className="flex items-start gap-3">
                  <Icon
                    className={`w-5 h-5 mt-0.5 ${iconColorClasses[config.color as keyof typeof iconColorClasses]} flex-shrink-0`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <div className="text-sm font-medium mb-2">
                        {config.title}
                      </div>
                      <span className="text-[10px] uppercase opacity-0 group-hover:opacity-100 transition-opacity">
                        Mark Read
                      </span>
                    </div>
                    <div className="text-xs mb-2 text-gray-900">
                      {alert.message}
                    </div>
                    <div className="text-[10px] text-gray-500">
                      {alert.time_ago}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Alert Summary - Tự động cập nhật theo data */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-red-600 text-2xl">{summary.critical}</div>
            <div className="text-xs text-gray-500 mt-1">Critical</div>
          </div>
          <div>
            <div className="text-yellow-600 text-2xl">{summary.warning}</div>
            <div className="text-xs text-gray-500 mt-1">Warning</div>
          </div>
          <div>
            <div className="text-blue-600 text-2xl">{summary.info}</div>
            <div className="text-xs text-gray-500 mt-1">Info</div>
          </div>
        </div>
      </div>
    </div>
  );
}