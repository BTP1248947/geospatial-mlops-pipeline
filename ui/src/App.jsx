import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import YearSelector from './components/YearSelector';
import VisualizationViewer from './components/VisualizationViewer';

function App() {
  const [theme, setTheme] = useState('light');
  const [regions, setRegions] = useState([]);
  const [yearsData, setYearsData] = useState({});
  const [years, setYears] = useState([]);
  const [selectedBeforeYear, setSelectedBeforeYear] = useState(null);
  const [selectedAfterYear, setSelectedAfterYear] = useState(null);
  const [selectedROI, setSelectedROI] = useState('');
  const [loading, setLoading] = useState(true);

  // Initialize theme
  useEffect(() => {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    }
  }, []);

  // Apply theme class
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Fetch available regions and years
  useEffect(() => {
    fetch('/visualization_results/index.json')
      .then(res => res.json())
      .then(data => {
        // data structure: { regions: ["name1", ...], years: { "name1": [2023, 2024], ... } }
        setRegions(data.regions || []);
        setYearsData(data.years || {});

        if (data.regions && data.regions.length > 0) {
          const initialROI = data.regions[0];
          setSelectedROI(initialROI);
          const roiYears = data.years[initialROI] || [];
          setYears(roiYears);
          if (roiYears.length >= 1) setSelectedBeforeYear(roiYears[0]);
          if (roiYears.length >= 1) setSelectedAfterYear(roiYears[roiYears.length - 1]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load index:", err);
        setLoading(false);
      });
  }, []);

  // Update years when ROI changes
  useEffect(() => {
    if (selectedROI && yearsData[selectedROI]) {
      const roiYears = yearsData[selectedROI];
      setYears(roiYears);
      // Reset years if current selection is not in new list, or just default to first/last
      if (!roiYears.includes(selectedBeforeYear)) setSelectedBeforeYear(roiYears[0]);
      if (!roiYears.includes(selectedAfterYear)) setSelectedAfterYear(roiYears[roiYears.length - 1]);
    }
  }, [selectedROI, yearsData]);

  const beforeImage = selectedBeforeYear && selectedROI
    ? `/visualization_results/${selectedROI}/before_${selectedBeforeYear}.png`
    : null;

  const afterImage = selectedAfterYear && selectedROI
    ? `/visualization_results/${selectedROI}/after_${selectedAfterYear}.png`
    : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0f172a] transition-colors duration-500 font-sans text-gray-900 dark:text-gray-100 flex flex-col relative overflow-hidden">
      {/* Background Decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-emerald-400/20 dark:bg-emerald-600/10 blur-[120px] animate-float" />
        <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-cyan-400/20 dark:bg-cyan-600/10 blur-[100px] animate-float delay-1000" />
      </div>

      <Header theme={theme} toggleTheme={toggleTheme} />

      <main className="w-full max-w-7xl mx-auto px-6 py-12 flex flex-col items-center gap-12 flex-grow relative z-10">
        <div className="text-center space-y-6 max-w-4xl animate-slide-up">
          <h2 className="text-5xl md:text-7xl font-black text-gradient tracking-tight pb-2 drop-shadow-sm">
            Deforestation Analysis
          </h2>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 leading-relaxed font-light max-w-2xl mx-auto">
            Visualize the impact. Compare satellite imagery to track the progression of deforestation in the Amazon.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64 animate-fade-in">
            <div className="relative">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-emerald-500"></div>
              <div className="absolute top-0 left-0 h-16 w-16 rounded-full border-t-2 border-b-2 border-emerald-500 animate-ping opacity-20"></div>
            </div>
          </div>
        ) : (
          <div className="w-full flex flex-col gap-12 animate-slide-up delay-200">
            <YearSelector
              years={years}
              regions={regions}
              selectedBeforeYear={selectedBeforeYear}
              selectedAfterYear={selectedAfterYear}
              onBeforeChange={setSelectedBeforeYear}
              onAfterChange={setSelectedAfterYear}
              selectedROI={selectedROI}
              onROIChange={setSelectedROI}
            />

            <VisualizationViewer
              beforeImage={beforeImage}
              afterImage={afterImage}
              maskImage={selectedBeforeYear && selectedROI ? `/visualization_results/${selectedROI}/mask_${selectedBeforeYear}.png` : null}
              beforeYear={selectedBeforeYear}
              afterYear={selectedAfterYear}
            />
          </div>
        )}
      </main>

      <footer className="mt-auto py-8 text-center text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-800/50 backdrop-blur-sm relative z-10">
        <p>© {new Date().getFullYear()} Deforestation Detection Project</p>
      </footer>
    </div>
  );
}

export default App;
