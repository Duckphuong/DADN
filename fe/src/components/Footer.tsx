import React from 'react';
import { BrainCircuit, Cpu, Database, Users } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-[#0f172a] text-slate-400 mt-16 border-t border-slate-800">
      <div className="max-w-[1600px] mx-auto px-6 py-10">
        <div className="grid md:grid-cols-4 gap-8 mb-10">
          
          {/* Brand & AI Core */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="bg-cyan-500/20 p-2 rounded-lg">
                <BrainCircuit className="w-5 h-5 text-cyan-400" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">AquaSense AI</span>
            </div>
            <p className="text-xs leading-relaxed max-w-xs">
              Advanced Deep Learning platform designed to predict water quality fluctuations and optimize aquaculture environments.
            </p>
          </div>

          {/* Column 2: Project Team - CỘT MỚI THÊM */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" /> Project Team
            </h4>
            <ul className="text-xs space-y-2">
              <li className="text-cyan-400 font-medium">Group 03_L01</li>
              <li>Multidisciplinary Project</li>
            </ul>
          </div>

          {/* AI Features */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-3 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" /> AI Capabilities
            </h4>
            <ul className="text-xs space-y-2">
              <li className="flex items-center gap-2">• Dissolved Oxygen (DO) Forecasting</li>
              <li className="flex items-center gap-2">• Early Contamination Anomaly Detection</li>
              <li className="flex items-center gap-2">• Predictive Historical Trend Analysis</li>
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-3 flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" /> Technical Specs
            </h4>
            <ul className="text-xs space-y-2 text-slate-400">
              <li>Models: LSTM & Random Forest Regressors</li>
              <li>Engine: Real-time IoT Data Streaming</li>
              <li>Architecture: Scalable Edge-to-Cloud Integration</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar - Retained as requested */}
        <div className="pt-8 border-t border-slate-800/60 text-center">
          <div className="text-xs text-slate-500 space-y-1">
            <p>© 2026 Water Quality Monitoring System. Academic Project.</p>
            <p className="flex items-center justify-center gap-2 font-medium">
              Powered by AI & IoT
              <span className="text-slate-700">•</span>
              For Educational Purposes
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}