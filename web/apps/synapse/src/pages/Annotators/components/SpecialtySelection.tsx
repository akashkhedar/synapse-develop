import React, { useState } from "react";
import "./SpecialtySelection.css";

export interface Specialty {
  id: string;
  name: string;
  description: string;
  iconType: "cv" | "nlp" | "audio" | "chat" | "ai" | "ranking";
  testCount: number;
}

// SVG icons for each specialty
const SpecialtyIcon: React.FC<{ type: Specialty["iconType"] }> = ({ type }) => {
  const icons = {
    cv: ( // Image/Vision icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="M21 15l-5-5L5 21" />
      </svg>
    ),
    nlp: ( // Text/Document icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <line x1="10" y1="9" x2="8" y2="9" />
      </svg>
    ),
    audio: ( // Audio/Waveform icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="22" />
      </svg>
    ),
    chat: ( // Chat/Conversation icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        <line x1="8" y1="9" x2="16" y2="9" />
        <line x1="8" y1="13" x2="12" y2="13" />
      </svg>
    ),
    ai: ( // AI/Brain icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v8a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4v-8a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
        <circle cx="9" cy="13" r="1" />
        <circle cx="15" cy="13" r="1" />
        <path d="M9 17h6" />
      </svg>
    ),
    ranking: ( // Chart/Ranking icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  };
  return <div className="specialty-icon">{icons[type]}</div>;
};

export const SPECIALTIES: Specialty[] = [
  {
    id: "computer-vision",
    name: "Computer Vision",
    description: "Image classification, object detection, segmentation, and OCR tasks",
    iconType: "cv",
    testCount: 3,
  },
  {
    id: "natural-language-processing",
    name: "Natural Language Processing",
    description: "Text classification, named entity recognition, and sentiment analysis",
    iconType: "nlp",
    testCount: 3,
  },
  {
    id: "audio-speech-processing",
    name: "Audio & Speech Processing",
    description: "Audio transcription, speaker identification, and sound classification",
    iconType: "audio",
    testCount: 2,
  },
  {
    id: "conversational-ai",
    name: "Conversational AI",
    description: "Dialogue quality assessment, intent classification, and response rating",
    iconType: "chat",
    testCount: 2,
  },
  {
    id: "generative-ai",
    name: "Generative AI",
    description: "LLM response evaluation, content quality rating, and comparison tasks",
    iconType: "ai",
    testCount: 2,
  },
  {
    id: "ranking-and-scoring",
    name: "Ranking & Scoring",
    description: "Content ranking, relevance scoring, and preference comparison",
    iconType: "ranking",
    testCount: 2,
  },
];

interface SpecialtySelectionProps {
  onConfirm: (selectedSpecialties: string[]) => void;
  isLoading?: boolean;
}

export const SpecialtySelection: React.FC<SpecialtySelectionProps> = ({
  onConfirm,
  isLoading = false,
}) => {
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);

  const toggleSpecialty = (specialtyId: string) => {
    setSelectedSpecialties((prev) =>
      prev.includes(specialtyId)
        ? prev.filter((id) => id !== specialtyId)
        : [...prev, specialtyId]
    );
  };

  const handleConfirm = () => {
    if (selectedSpecialties.length > 0) {
      onConfirm(selectedSpecialties);
    }
  };

  const totalTests = selectedSpecialties.reduce((total, id) => {
    const specialty = SPECIALTIES.find((s) => s.id === id);
    return total + (specialty?.testCount || 0);
  }, 0);

  return (
    <div className="specialty-selection">
      <div className="specialty-selection__header">
        <div className="specialty-selection__number">01/</div>
        <h1 className="specialty-selection__title">Select Your Specialties</h1>
        <p className="specialty-selection__subtitle">
          Choose the annotation areas you're skilled in. You'll be tested on each selected specialty.
        </p>
      </div>

      <div className="specialty-selection__grid">
        {SPECIALTIES.map((specialty) => {
          const isSelected = selectedSpecialties.includes(specialty.id);
          return (
            <button
              key={specialty.id}
              type="button"
              className={`specialty-card ${isSelected ? "specialty-card--selected" : ""}`}
              onClick={() => toggleSpecialty(specialty.id)}
            >
              <SpecialtyIcon type={specialty.iconType} />
              <div className="specialty-card__content">
                <h3 className="specialty-card__name">{specialty.name}</h3>
                <p className="specialty-card__description">{specialty.description}</p>
                <div className="specialty-card__meta">
                  <span className="specialty-card__tests">{specialty.testCount} test tasks</span>
                </div>
              </div>
              <div className="specialty-card__checkbox">
                {isSelected ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <div className="specialty-card__checkbox-empty" />
                )}
              </div>
            </button>
          );
        })}
      </div>

      <div className="specialty-selection__footer">
        <div className="specialty-selection__summary">
          {selectedSpecialties.length > 0 ? (
            <>
              <span className="specialty-selection__count">
                {selectedSpecialties.length} specialty selected
              </span>
              <span className="specialty-selection__divider">•</span>
              <span className="specialty-selection__total-tests">
                {totalTests} total test tasks
              </span>
            </>
          ) : (
            <span className="specialty-selection__hint">
              Select at least one specialty to continue
            </span>
          )}
        </div>
        <button
          type="button"
          className="specialty-selection__confirm"
          onClick={handleConfirm}
          disabled={selectedSpecialties.length === 0 || isLoading}
        >
          {isLoading ? (
            <span className="specialty-selection__loading">Loading tests...</span>
          ) : (
            <>
              Start Test
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
