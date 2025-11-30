import React from 'react';
import { Calendar, ArrowRight, ChevronDown, MapPin } from 'lucide-react';

const YearSelector = ({ years, areas, selectedArea, onAreaChange, selectedLocation, onLocationChange, selectedBeforeYear, selectedAfterYear, onBeforeChange, onAfterChange }) => {
  return (
    <div className="w-full glass-card rounded-3xl p-8 md:p-10 transition-all duration-500 hover:shadow-2xl hover:shadow-emerald-500/10 border border-white/40 dark:border-gray-700/40">
      <div className="flex flex-col items-center gap-8 w-full">

        {/* Area Selector */}
        <div className="flex flex-col md:flex-row gap-8 w-full justify-center">
          <div className="w-full md:w-72 group">
            <label className="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-2 uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
              <MapPin className="w-4 h-4" />
              Area
            </label>
            <div className="relative">
              <select
                value={selectedArea || ''}
                onChange={(e) => onAreaChange(e.target.value)}
                className="w-full appearance-none bg-gray-50/50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-2xl py-4 pl-6 pr-12 text-lg font-semibold focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-white dark:hover:bg-gray-800"
              >
                {Object.keys(areas).sort().map((areaKey) => (
                  <option key={areaKey} value={areaKey}>
                    {areas[areaKey].label}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-5 text-gray-400 group-hover:text-emerald-500 transition-colors">
                <ChevronDown className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Location Selector (Conditional) */}
          {selectedArea && areas[selectedArea] && areas[selectedArea].locations.length > 1 && (
            <div className="w-full md:w-48 group animate-fade-in">
              <label className="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-2 uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
                <MapPin className="w-4 h-4" />
                Location
              </label>
              <div className="relative">
                <select
                  value={selectedLocation || '1'}
                  onChange={(e) => onLocationChange(e.target.value)}
                  className="w-full appearance-none bg-gray-50/50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-2xl py-4 pl-6 pr-12 text-lg font-semibold focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-white dark:hover:bg-gray-800"
                >
                  {areas[selectedArea].locations.map((loc) => (
                    <option key={loc} value={loc}>
                      Location {loc}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-5 text-gray-400 group-hover:text-emerald-500 transition-colors">
                  <ChevronDown className="w-5 h-5" />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16 w-full">

          {/* Before Year Selector */}
          <div className="w-full md:w-72 group">
            <label className="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-2 uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
              <Calendar className="w-4 h-4" />
              Before Year
            </label>
            <div className="relative">
              <select
                value={selectedBeforeYear || ''}
                onChange={(e) => onBeforeChange(e.target.value)}
                className="w-full appearance-none bg-gray-50/50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-2xl py-4 pl-6 pr-12 text-lg font-semibold focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-white dark:hover:bg-gray-800"
              >
                <option value="" disabled>Select Year</option>
                {years.map((year) => (
                  <option key={`before-${year}`} value={year}>
                    {year}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-5 text-gray-400 group-hover:text-emerald-500 transition-colors">
                <ChevronDown className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Arrow Indicator */}
          <div className="hidden md:flex items-center justify-center pt-8 text-gray-300 dark:text-gray-600">
            <div className="p-3 rounded-full bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
              <ArrowRight className="w-6 h-6" />
            </div>
          </div>

          {/* After Year Selector */}
          <div className="w-full md:w-72 group">
            <label className="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-2 uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
              <Calendar className="w-4 h-4" />
              After Year
            </label>
            <div className="relative">
              <select
                value={selectedAfterYear || ''}
                onChange={(e) => onAfterChange(e.target.value)}
                className="w-full appearance-none bg-gray-50/50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-2xl py-4 pl-6 pr-12 text-lg font-semibold focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-white dark:hover:bg-gray-800"
              >
                <option value="" disabled>Select Year</option>
                {years.map((year) => (
                  <option key={`after-${year}`} value={year}>
                    {year}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-5 text-gray-400 group-hover:text-emerald-500 transition-colors">
                <ChevronDown className="w-5 h-5" />
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default YearSelector;
