import React, { useEffect, useState, useMemo } from "react";
import { ExpertiseDropdown, DropdownOption } from "./ExpertiseDropdown";
import "./ExpertiseSelector.scss";

export interface ExpertiseSelectorProps {
  categoryId: number | null;
  specializationId: number | null;
  onCategoryChange: (id: number | null) => void;
  onSpecializationChange: (id: number | null) => void;
}

interface ExpertiseSpecialization {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
}

interface ExpertiseCategory {
  id: number;
  name: string;
  slug: string;
  icon: string;
  specializations: ExpertiseSpecialization[];
}

export const ExpertiseSelector: React.FC<ExpertiseSelectorProps> = ({
  categoryId,
  specializationId,
  onCategoryChange,
  onSpecializationChange,
}) => {
  const [categories, setCategories] = useState<ExpertiseCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api/annotators/expertise/categories", {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setCategories(data.categories || []);
        }
      } catch (error) {
        console.error("Failed to fetch expertise categories:", error);
      } finally {
        setLoadingCategories(false);
      }
    };
    fetchCategories();
  }, []);

  const selectedCategory = useMemo(
    () => categories.find((cat) => cat.id === categoryId),
    [categories, categoryId],
  );

  const specializations = useMemo(
    () =>
      selectedCategory
        ? selectedCategory.specializations.filter((s) => s.is_active)
        : [],
    [selectedCategory],
  );

  const categoryOptions: DropdownOption[] = categories.map((cat) => ({
    id: cat.id,
    name: cat.name,
  }));

  const specializationOptions: DropdownOption[] = specializations.map(
    (spec) => ({
      id: spec.id,
      name: spec.name,
    }),
  );

  return (
    <div className="expertise-selector">
      <ExpertiseDropdown
        label="ANNOTATION TYPE"
        value={categoryId}
        options={categoryOptions}
        placeholder="Select annotation type..."
        onChange={(v) => {
          onCategoryChange(v);
          onSpecializationChange(null);
        }}
        loading={loadingCategories}
      />

      <ExpertiseDropdown
        label="EXPERTISE TYPE"
        value={specializationId}
        options={specializationOptions}
        placeholder={
          categoryId ? "Select expertise type..." : "Select annotation first"
        }
        onChange={onSpecializationChange}
        disabled={!categoryId}
      />
    </div>
  );
};

export default ExpertiseSelector;
