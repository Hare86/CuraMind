import type { QueryMode } from "@/lib/types";

const MODES: { value: QueryMode; label: string; description: string }[] = [
  { value: "question_answer", label: "Q&A", description: "Ask any psychology question" },
  { value: "long_academic", label: "Academic Essay", description: "Comprehensive academic response" },
  { value: "mcq", label: "MCQ", description: "Generate multiple choice questions" },
  { value: "case_study", label: "Case Study", description: "Generate clinical case study" },
  { value: "symptoms_to_disorder", label: "Symptoms → Disorder", description: "Map symptoms to disorders" },
  { value: "disorder_to_symptoms", label: "Disorder → Symptoms", description: "Explore disorder presentation" },
  { value: "treatment_approach", label: "Treatment", description: "Evidence-based treatment info" },
];

interface QueryModeSelectorProps {
  value: QueryMode;
  onChange: (mode: QueryMode) => void;
}

export default function QueryModeSelector({ value, onChange }: QueryModeSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {MODES.map((mode) => (
        <button
          key={mode.value}
          onClick={() => onChange(mode.value)}
          title={mode.description}
          className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors
            ${value === mode.value
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
