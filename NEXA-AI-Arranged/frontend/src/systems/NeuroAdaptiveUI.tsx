import React, {
  createContext, useContext, useState,
  useEffect, useCallback, useRef
} from 'react';

interface UIBehavior {
  panelOrder: string[];
  expandedPanels: string[];
  hiddenPanels: string[];
  sidebarWidth: number;
  fontScale: number;
  colorIntensity: number;
  animationSpeed: number;
  infoDepth: 'minimal' | 'normal' | 'detailed';
  preferredFeatures: string[];
  avoidedFeatures: string[];
}

interface UsageEvent {
  element: string;
  action: 'click' | 'hover' | 'ignore' | 'close' | 'expand';
  timestamp: number;
  duration?: number;
  context?: string;
}

interface NeuroAdaptiveContextType {
  behavior: UIBehavior;
  recordInteraction: (event: UsageEvent) => void;
  getFeaturePriority: (feature: string) => number;
  suggestLayout: () => UIBehavior;
  applyAdaptation: (adaptation: Partial<UIBehavior>) => void;
  resetToDefault: () => void;
  adaptationLevel: number;
}

const defaultBehavior: UIBehavior = {
  panelOrder: ['assistant', 'timeline', 'system', 'history', 'files'],
  expandedPanels: ['assistant', 'timeline'],
  hiddenPanels: [],
  sidebarWidth: 280,
  fontScale: 1.0,
  colorIntensity: 1.0,
  animationSpeed: 1.0,
  infoDepth: 'normal',
  preferredFeatures: [],
  avoidedFeatures: [],
};

const NeuroAdaptiveContext = createContext<NeuroAdaptiveContextType | null>(null);

export const NeuroAdaptiveProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [behavior, setBehavior] = useState<UIBehavior>(() => {
    const saved = localStorage.getItem('nexa_ui_behavior');
    return saved ? JSON.parse(saved) : defaultBehavior;
  });

  const [interactions, setInteractions] = useState<UsageEvent[]>([]);
  const [adaptationLevel, setAdaptationLevel] = useState(0);
  const analysisTimer = useRef<NodeJS.Timeout>();

  // Save behavior to localStorage
  useEffect(() => {
    localStorage.setItem('nexa_ui_behavior', JSON.stringify(behavior));
  }, [behavior]);

  // Analyze interactions every 2 minutes
  useEffect(() => {
    analysisTimer.current = setInterval(() => {
      if (interactions.length >= 20) {
        const newBehavior = analyzeAndAdapt(interactions, behavior);
        setBehavior(newBehavior);
        setAdaptationLevel(prev => Math.min(100, prev + 5));
      }
    }, 120000);

    return () => {
      if (analysisTimer.current) clearInterval(analysisTimer.current);
    };
  }, [interactions, behavior]);

  const recordInteraction = useCallback((event: UsageEvent) => {
    setInteractions(prev => [...prev.slice(-500), event]);
  }, []);

  const getFeaturePriority = useCallback((feature: string): number => {
    const preferred = behavior.preferredFeatures.indexOf(feature);
    const avoided = behavior.avoidedFeatures.indexOf(feature);

    if (preferred !== -1) return 10 - preferred;
    if (avoided !== -1) return -avoided;
    return 5;
  }, [behavior]);

  const suggestLayout = useCallback((): UIBehavior => {
    return analyzeAndAdapt(interactions, behavior);
  }, [interactions, behavior]);

  const applyAdaptation = useCallback((adaptation: Partial<UIBehavior>) => {
    setBehavior(prev => ({ ...prev, ...adaptation }));
  }, []);

  const resetToDefault = useCallback(() => {
    setBehavior(defaultBehavior);
    setInteractions([]);
    setAdaptationLevel(0);
    localStorage.removeItem('nexa_ui_behavior');
  }, []);

  return (
    <NeuroAdaptiveContext.Provider value={{
      behavior,
      recordInteraction,
      getFeaturePriority,
      suggestLayout,
      applyAdaptation,
      resetToDefault,
      adaptationLevel,
    }}>
      {children}
    </NeuroAdaptiveContext.Provider>
  );
};

function analyzeAndAdapt(
  interactions: UsageEvent[],
  currentBehavior: UIBehavior
): UIBehavior {
  const newBehavior = { ...currentBehavior };

  // Count interactions per element
  const elementCounts: Record<string, number> = {};
  const elementDurations: Record<string, number[]> = {};
  const ignoredElements: Record<string, number> = {};

  for (const event of interactions) {
    if (event.action === 'click' || event.action === 'expand') {
      elementCounts[event.element] = (elementCounts[event.element] || 0) + 1;
    }

    if (event.action === 'ignore' || event.action === 'close') {
      ignoredElements[event.element] = (ignoredElements[event.element] || 0) + 1;
    }

    if (event.duration) {
      if (!elementDurations[event.element]) {
        elementDurations[event.element] = [];
      }
      elementDurations[event.element].push(event.duration);
    }
  }

  // Determine preferred features
  const sorted = Object.entries(elementCounts)
    .sort(([, a], [, b]) => b - a)
    .map(([element]) => element);

  newBehavior.preferredFeatures = sorted.slice(0, 5);

  // Determine avoided features
  const avoided = Object.entries(ignoredElements)
    .filter(([element, count]) => count > 3 && (elementCounts[element] || 0) < 2)
    .map(([element]) => element);

  newBehavior.avoidedFeatures = avoided;

  // Adapt panel order
  const panels = ['assistant', 'timeline', 'system', 'history', 'files', 'memory'];
  newBehavior.panelOrder = panels.sort((a, b) => {
    const countA = elementCounts[a] || 0;
    const countB = elementCounts[b] || 0;
    return countB - countA;
  });

  // Hide consistently ignored panels
  newBehavior.hiddenPanels = avoided.filter(el => panels.includes(el));

  // Expand frequently used panels
  const expandThreshold = Math.max(3, interactions.length * 0.05);
  newBehavior.expandedPanels = panels.filter(
    p => (elementCounts[p] || 0) >= expandThreshold
  );

  // Adapt info depth
  const avgDuration = Object.values(elementDurations)
    .flat()
    .reduce((a, b) => a + b, 0) /
    Math.max(Object.values(elementDurations).flat().length, 1);

  if (avgDuration > 5000) {
    newBehavior.infoDepth = 'detailed';
  } else if (avgDuration < 1000) {
    newBehavior.infoDepth = 'minimal';
  } else {
    newBehavior.infoDepth = 'normal';
  }

  // Adapt font scale for readability
  const readingElements = ['timeline', 'history', 'output'];
  const readingTime = readingElements
    .flatMap(el => elementDurations[el] || [])
    .reduce((a, b) => a + b, 0);

  if (readingTime > 60000) {
    newBehavior.fontScale = Math.min(1.2, newBehavior.fontScale + 0.05);
  }

  return newBehavior;
}

export const useNeuroAdaptive = () => {
  const context = useContext(NeuroAdaptiveContext);
  if (!context) {
    throw new Error('useNeuroAdaptive must be used within NeuroAdaptiveProvider');
  }
  return context;
};

// HOC to make any component trackable
export function withAdaptiveTracking<T extends object>(
  Component: React.ComponentType<T>,
  elementId: string
) {
  return function TrackedComponent(props: T) {
    const { recordInteraction } = useNeuroAdaptive();
    const enterTime = useRef<number>(0);

    const handleMouseEnter = () => {
      enterTime.current = Date.now();
    };

    const handleMouseLeave = () => {
      const duration = Date.now() - enterTime.current;
      recordInteraction({
        element: elementId,
        action: 'hover',
        timestamp: Date.now(),
        duration,
      });
    };

    const handleClick = () => {
      recordInteraction({
        element: elementId,
        action: 'click',
        timestamp: Date.now(),
      });
    };

    return (
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        style={{ display: 'contents' }}
      >
        <Component {...props} />
      </div>
    );
  };
}

// Adaptive Layout Component
export const AdaptiveLayout: React.FC<{
  children: React.ReactNode;
  panelId: string;
}> = ({ children, panelId }) => {
  const { behavior, recordInteraction } = useNeuroAdaptive();
  const isHidden = behavior.hiddenPanels.includes(panelId);
  const isExpanded = behavior.expandedPanels.includes(panelId);
  const priority = behavior.preferredFeatures.indexOf(panelId);

  if (isHidden) return null;

  return (
    <div
      data-panel-id={panelId}
      data-priority={priority}
      style={{
        order: priority >= 0 ? priority : 999,
        flexGrow: isExpanded ? 1 : 0,
      }}
      onClick={() => recordInteraction({
        element: panelId,
        action: 'click',
        timestamp: Date.now(),
      })}
    >
      {children}
    </div>
  );
};
