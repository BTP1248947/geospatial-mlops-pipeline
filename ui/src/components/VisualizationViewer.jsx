import React, { useState } from 'react';
import { AlertCircle, Maximize2 } from 'lucide-react';

const VisualizationViewer = ({ beforeImage, afterImage, maskImage, beforeYear, afterYear }) => {
  const [imageError, setImageError] = useState({ before: false, after: false, mask: false });

  const handleImageError = (type) => {
    setImageError(prev => ({ ...prev, [type]: true }));
  };

  // Reset error state when images change
  React.useEffect(() => {
    setImageError({ before: false, after: false, mask: false });
  }, [beforeImage, afterImage, maskImage]);

  if (!beforeYear || !afterYear) {
    return (
      <div className="w-full min-h-[50vh] flex flex-col items-center justify-center p-12 text-center glass-card rounded-3xl border-2 border-dashed border-gray-300/50 dark:border-gray-700/50 transition-all duration-500 hover:border-emerald-500/30 dark:hover:border-emerald-500/30 group animate-fade-in">
        <div className="p-8 bg-emerald-50/50 dark:bg-emerald-900/20 rounded-full mb-8 group-hover:scale-110 group-hover:bg-emerald-100/50 dark:group-hover:bg-emerald-900/30 transition-all duration-500">
          <Maximize2 className="w-16 h-16 text-emerald-500/80 dark:text-emerald-400/80" />
        </div>
        <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Ready to Analyze
        </h3>
        <p className="text-xl text-gray-500 dark:text-gray-400 max-w-lg leading-relaxed">
          Select a <span className="font-semibold text-emerald-600 dark:text-emerald-400">Before</span> and <span className="font-semibold text-emerald-600 dark:text-emerald-400">After</span> year from the menu above to visualize the deforestation changes.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-8 xl:gap-12">
      {/* Before Image Card */}
      <div className="group relative glass-card rounded-3xl overflow-hidden transition-all duration-500 hover:shadow-2xl hover:shadow-emerald-500/10 hover:-translate-y-2 animate-slide-up delay-100">
        <div className="absolute top-4 left-4 z-10">
          <span className="px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10 shadow-lg">
            Before: {beforeYear}
          </span>
        </div>
        
        <div className="aspect-square w-full relative bg-gray-100 dark:bg-gray-900/50 flex items-center justify-center overflow-hidden">
          {imageError.before ? (
            <div className="text-center p-6 animate-fade-in">
              <AlertCircle className="w-12 h-12 text-red-500/80 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400 font-medium">Image not found</p>
            </div>
          ) : (
            <img
              src={beforeImage}
              alt={`Deforestation state in ${beforeYear}`}
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              onError={() => handleImageError('before')}
            />
          )}
        </div>
      </div>

      {/* After Image Card */}
      <div className="group relative glass-card rounded-3xl overflow-hidden transition-all duration-500 hover:shadow-2xl hover:shadow-emerald-500/10 hover:-translate-y-2 animate-slide-up delay-200">
        <div className="absolute top-4 left-4 z-10">
          <span className="px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10 shadow-lg">
            After: {afterYear}
          </span>
        </div>

        <div className="aspect-square w-full relative bg-gray-100 dark:bg-gray-900/50 flex items-center justify-center overflow-hidden">
          {imageError.after ? (
            <div className="text-center p-6 animate-fade-in">
              <AlertCircle className="w-12 h-12 text-red-500/80 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400 font-medium">Image not found</p>
            </div>
          ) : (
            <img
              src={afterImage}
              alt={`Deforestation state in ${afterYear}`}
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              onError={() => handleImageError('after')}
            />
          )}
        </div>
      </div>

      {/* Mask Image Card */}
      <div className="group relative glass-card rounded-3xl overflow-hidden transition-all duration-500 hover:shadow-2xl hover:shadow-emerald-500/10 hover:-translate-y-2 animate-slide-up delay-300">
        <div className="absolute top-4 left-4 z-10">
          <span className="px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10 shadow-lg">
            Deforestation Mask
          </span>
        </div>

        <div className="aspect-square w-full relative bg-gray-100 dark:bg-gray-900/50 flex items-center justify-center overflow-hidden">
          {imageError.mask ? (
            <div className="text-center p-6 animate-fade-in">
              <AlertCircle className="w-12 h-12 text-red-500/80 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400 font-medium">Mask not found</p>
            </div>
          ) : (
            <img
              src={maskImage}
              alt="Deforestation Mask"
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              onError={() => handleImageError('mask')}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualizationViewer;

