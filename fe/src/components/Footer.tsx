import { Droplets, Code, Database, Cloud, MapPin } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gradient-to-r from-gray-900 via-slate-800 to-gray-900 text-white mt-16">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Team & Project Info */}
        <div className="grid md:grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div>
            <h4 className="text-cyan-400 mb-3 text-sm">Project Information</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <div>AI-Based Water Quality Monitoring</div>
              <div>IoT + Machine Learning System</div>
              <div>Real-time Contamination Detection</div>
            </div>
          </div>
          <div>
            <h4 className="text-cyan-400 mb-3 text-sm">Team Members</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <div>Student Name 1 </div>
              <div>Student Name 2 </div>
              <div>Student Name 3 </div>
            </div>
          </div>
          <div>
            <h4 className="text-cyan-400 mb-3 text-sm">Project Alignment</h4>
            <div className="flex items-start gap-3">
              <div className="bg-cyan-500 rounded-lg p-3">
                <Droplets className="w-8 h-8 text-white" />
              </div>
              <div className="text-sm text-gray-400">
                <div className="text-cyan-400 mb-1">Group 3</div>
                <div>Aquaculture Intelligence</div>
                <div className="text-xs mt-1">AI-Powered Water Insights for Smarter Farming</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-gray-700 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-500">
            © 2026 Water Quality Monitoring System. Academic Project.
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>Powered by AI & IoT</span>
            <span>•</span>
            <span>For Educational Purposes</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
