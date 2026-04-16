import { Cpu, Cloud, Database, Brain, Smartphone, Bell, Droplet, Thermometer, Zap, ArrowRight } from 'lucide-react';

export function SystemArchitecture() {
  return (
    <section>
      <h2 className="text-cyan-900 mb-6 font-medium text-xl">System Architecture</h2>
      
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 overflow-x-auto">
        {/* <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:min-w-[800px] md:flex-nowrap"> */}
        <div className="flex md:flex-row items-center md:items-start justify-between gap-4 min-w-full md:min-w-[900px]">
          {/* IoT Sensors */}
          <div className="flex flex-col items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-4 shadow-lg w-full">
              <div className="text-white text-center mb-3">
                <Droplet className="w-8 h-8 mx-auto mb-2" />
                <div className="text-sm">IoT Sensors</div>
              </div>
              <div className="space-y-1.5">
                <div className="bg-white/20 rounded-lg p-2 text-white text-xs flex items-center gap-2">
                  <Droplet className="w-3 h-3" />
                  <span>pH</span>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-white text-xs flex items-center gap-2">
                  <Thermometer className="w-3 h-3" />
                  <span>Temp</span>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-white text-xs flex items-center gap-2">
                  <Zap className="w-3 h-3" />
                  <span>Cond</span>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-white text-xs flex items-center gap-2">
                  <Droplet className="w-3 h-3" />
                  <span>DO</span>
                </div>
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="flex justify-center items-center h-full">
            <ArrowRight className="w-6 h-6 text-cyan-500" />
          </div>

          {/* Microcontroller */}
          <div className="flex flex-col items-center gap-3">
            <div className="bg-gradient-to-br from-purple-500 to-indigo-500 rounded-2xl p-6 shadow-lg w-full">
              <Cpu className="w-10 h-10 text-white mx-auto mb-2" />
              <div className="text-white text-center text-sm">
                Microcontroller
              </div>
              <div className="text-white/80 text-center text-xs mt-1">
                NodeMCU / RPi
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="flex justify-center items-center h-full">
            <ArrowRight className="w-6 h-6 text-cyan-500" />
          </div>

          {/* Cloud Storage */}
          <div className="flex flex-col items-center gap-3">
            <div className="bg-gradient-to-br from-sky-500 to-blue-500 rounded-2xl p-6 shadow-lg w-full">
              <Cloud className="w-10 h-10 text-white mx-auto mb-2" />
              <div className="text-white text-center text-sm">
                Cloud Storage
              </div>
              <div className="text-white/80 text-center text-xs mt-1">
                Firebase
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="flex justify-center items-center h-full">
            <ArrowRight className="w-6 h-6 text-cyan-500" />
          </div>

          {/* ML Model */}
          <div className="flex flex-col items-center gap-3">
            <div className="bg-gradient-to-br from-violet-500 to-purple-500 rounded-2xl p-6 shadow-lg w-full">
              <Brain className="w-10 h-10 text-white mx-auto mb-2" />
              <div className="text-white text-center text-sm">
                ML Model
              </div>
              <div className="text-white/80 text-center text-xs mt-1">
                Random Forest
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="flex justify-center items-center h-full">
            <ArrowRight className="w-6 h-6 text-cyan-500" />
          </div>

          {/* Outputs */}
          <div className="flex flex-col gap-3">
            <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl p-4 shadow-lg">
              <Smartphone className="w-6 h-6 text-white mx-auto mb-1" />
              <div className="text-white text-center text-xs">
                Dashboard UI
              </div>
            </div>
            <div className="bg-gradient-to-br from-red-500 to-orange-500 rounded-xl p-4 shadow-lg">
              <Bell className="w-6 h-6 text-white mx-auto mb-1" />
              <div className="text-white text-center text-xs">
                Alerts
              </div>
            </div>
          </div>
        </div>

        {/* Data Flow Description */}
        <div className="mt-8 grid md:grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl p-4 border border-cyan-100">
            <div className="text-sm text-gray-900 mb-2">Data Collection</div>
            <div className="text-xs text-gray-600">
              IoT sensors continuously monitor water parameters (pH, temperature, conductivity, turbidity, DO, TDS) and transmit data via NodeMCU/Raspberry Pi.
            </div>
          </div>
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-100">
            <div className="text-sm text-gray-900 mb-2">AI Processing</div>
            <div className="text-xs text-gray-600">
              Machine learning models (Random Forest/LSTM) analyze sensor data to predict water quality index and detect contamination patterns.
            </div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
            <div className="text-sm text-gray-900 mb-2">Real-Time Alerts</div>
            <div className="text-xs text-gray-600">
              System sends instant notifications via SMS/email when anomalies detected, with visual dashboard for monitoring and control.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
