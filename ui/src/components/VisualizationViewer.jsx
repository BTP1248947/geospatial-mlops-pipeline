import React, { useState, useRef, useEffect } from 'react';
import { AlertCircle, Maximize2, MoveHorizontal } from 'lucide-react';

const VisualizationViewer = ({ beforeImage, afterImage, maskImage, heatImage, beforeYear, afterYear }) => {
  const [imageError, setImageError] = useState({ before: false, after: false, mask: false, heat: false });
  const [sliderPosition, setSliderPosition] = useState(50);
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const handleImageError = (type) => {
    setImageError(prev => ({ ...prev, [type]: true }));
  };

  // Reset error state when images change
  useEffect(() => {
    setImageError({ before: false, after: false, mask: false, heat: false });
  }, [beforeImage, afterImage, maskImage, heatImage]);

  const handleMouseDown = () => { isDragging.current = true; };
  const handleMouseUp = () => { isDragging.current = false; };
  const handleMouseMove = (e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    setSliderPosition((x / rect.width) * 100);
  };

  // Touch support
  const handleTouchMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.touches[0].clientX - rect.left, rect.width));
    setSliderPosition((x / rect.width) * 100);
  };

  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    return () => document.removeEventListener('mouseup', handleMouseUp);
  }, []);

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
    <div className="w-full flex flex-col gap-8">

      {/* Main Comparison Slider */}
      <div className="w-full glass-card rounded-3xl p-2 animate-slide-up delay-100">
        <div
          ref={containerRef}
          className="relative w-full aspect-[21/9] rounded-2xl overflow-hidden cursor-col-resize select-none"
          onMouseMove={handleMouseMove}
          onMouseDown={handleMouseDown}
          onTouchMove={handleTouchMove}
        >
          {/* After Image (Background) */}
          <img
            src={afterImage}
            alt="After"
            className="absolute top-0 left-0 w-full h-full object-cover"
            onError={() => handleImageError('after')}
          />

          {/* Before Image (Foreground - Clipped) */}
          <div
            className="absolute top-0 left-0 h-full overflow-hidden border-r-2 border-white/50 shadow-xl"
            style={{ width: `${sliderPosition}%` }}
          >
            <img
              src={beforeImage}
              alt="Before"
              className="absolute top-0 left-0 max-w-none h-full object-cover"
              style={{ width: `${100 * (100 / sliderPosition)}%` }} // Counter-scale to keep image static
            // Actually, simpler approach: set width of container, img is full width of PARENT container?
            // No, standard slider: img is absolute, width 100vw equivalent.
            // Let's fix: set img width to container width.
            />
            {/* Fix for clipped image scaling: we need the image to be full width of the CONTAINER, not the clipped div. */}
            {/* We can achieve this by setting the image width to the container's width programmatically or using vw if full screen, but here it's relative. */}
            {/* Better approach: Use background images or fixed width. Let's try standard absolute positioning. */}
            <img
              src={beforeImage}
              alt="Before"
              className="absolute top-0 left-0 h-full object-cover max-w-none"
              style={{ width: containerRef.current ? containerRef.current.offsetWidth : '100%' }}
              onError={() => handleImageError('before')}
            />
          </div>

          {/* Slider Handle */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-white/50 cursor-col-resize flex items-center justify-center shadow-[0_0_20px_rgba(0,0,0,0.5)]"
            style={{ left: `${sliderPosition}%` }}
          >
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg text-emerald-600">
              <MoveHorizontal size={16} />
            </div>
          </div>

          {/* Labels */}
          <div className="absolute top-4 left-4 px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10 pointer-events-none">
            {beforeYear}
          </div>
          <div className="absolute top-4 right-4 px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10 pointer-events-none">
            {afterYear}
          </div>
        </div>
      </div>

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Heatmap Card */}
        <div className="group relative glass-card rounded-3xl overflow-hidden p-2 animate-slide-up delay-200">
          <div className="relative rounded-2xl overflow-hidden aspect-square">
            <img
              src={heatImage}
              alt="Heatmap"
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              onError={() => handleImageError('heat')}
            />
            <div className="absolute top-4 left-4 px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10">
              Change Intensity
            </div>

            {/* Legend */}
            <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-md rounded-xl p-3 border border-white/10">
              <div className="flex justify-between text-xs text-gray-200 mb-1 font-medium">
                <span>Low Change</span>
                <span>High Change</span>
              </div>
              <div className="h-3 w-full rounded-full bg-gradient-to-r from-[#000080] via-[#00ff00] to-[#800000] border border-white/20"></div>
              {/* Jet approximation: Blue -> Cyan -> Green -> Yellow -> Red -> Dark Red */}
              {/* Better Jet CSS: linear-gradient(90deg, #00007F 0%, #0000FF 12%, #007FFF 25%, #00FFFF 37%, #7FFF7F 50%, #FFFF00 62%, #FF7F00 75%, #FF0000 87%, #7F0000 100%) */}
              <style jsx>{`
                .bg-jet-gradient {
                  background: linear-gradient(90deg, #00007F 0%, #0000FF 12%, #007FFF 25%, #00FFFF 37%, #7FFF7F 50%, #FFFF00 62%, #FF7F00 75%, #FF0000 87%, #7F0000 100%);
                }
              `}</style>
              <div className="h-3 w-full rounded-full bg-jet-gradient border border-white/20 mt-1"></div>
            </div>
          </div>
        </div>

        {/* Mask Card */}
        <div className="group relative glass-card rounded-3xl overflow-hidden p-2 animate-slide-up delay-300">
          <div className="relative rounded-2xl overflow-hidden aspect-square">
            <img
              src={maskImage}
              alt="Mask"
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              onError={() => handleImageError('mask')}
            />
            <div className="absolute top-4 left-4 px-4 py-2 bg-black/60 backdrop-blur-md text-white text-sm font-bold rounded-full border border-white/10">
              Deforestation Mask
            </div>
            <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-md rounded-xl p-3 border border-white/10 flex items-center gap-3">
              <div className="w-4 h-4 bg-white border border-gray-500 rounded-sm"></div>
              <span className="text-xs text-gray-200 font-medium">Detected Change Area</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default VisualizationViewer;

