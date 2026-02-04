import React from "react";
import { Spinner } from "../../../components";
import { useAPI } from "../../../providers/ApiProvider";
import { cn } from "../../../utils/bem";
import "./Config.scss";
import { IconInfo } from "@synapse/icons";
import { Button, EnterpriseBadge } from "@synapse/ui";


const listClass = cn("templates-list");

const Arrow = () => (
  <svg width="8" height="12" viewBox="0 0 8 12" fill="none" xmlns="http://www.w3.org/2000/svg">
    <title>Arrow Icon</title>
    <path opacity="0.9" d="M2 10L6 6L2 2" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
  </svg>
);

const isCompatible = (recipe, detectedFileType) => {
    if (!detectedFileType) return true;
    
    // Simple verification maps
    const config = recipe.config;
    let valid = true;
    
    // If we have a file type, we must find a corresponding tag in the config
    if (["image", "bmp", "png", "jpg", "jpeg"].includes(detectedFileType)) {
        if (!config.includes("<Image") && !config.includes("<Img")) valid = false;
    } else if (["audio", "wav", "mp3"].includes(detectedFileType)) {
        if (!config.includes("<Audio")) valid = false;
    } else if (["video", "mp4"].includes(detectedFileType)) {
        if (!config.includes("<Video")) valid = false;
    } else if (["text", "txt"].includes(detectedFileType)) {
        if (!config.includes("<Text") && !config.includes("<HyperText")) valid = false;
    } else if (["medical", "dicom", "dcm"].includes(detectedFileType)) {
        // Only filter for DICOM templates when we actually have DICOM files
        // ZIP files are now analyzed by the backend, so they won't automatically be "medical"
        if (!config.includes("<Dicom") && !config.includes("<Dicom3D")) valid = false;
    }
    // Note: ZIP files are no longer automatically assumed to be medical/DICOM
    // The backend analyzes ZIP contents and returns the actual file type
    
    return valid;
};

const TemplatesInGroup = ({ templates, group, onSelectRecipe, isEdition, detectedFileType }) => {
  const picked = templates
    .filter((recipe) => recipe.group === group)
    // Filter compatible templates ONLY
    .filter((recipe) => isCompatible(recipe, detectedFileType))
    .sort((a, b) => (a.order ?? Number.POSITIVE_INFINITY) - (b.order ?? Number.POSITIVE_INFINITY));

  const isCommunityEdition = isEdition === "Community";

  if (picked.length === 0) return null;

  return (
    <ul>
      {picked.map((recipe) => {
        const isEnterpriseTemplate = recipe.type === "enterprise";
        const isDisabled = isCommunityEdition && isEnterpriseTemplate;
        const title = isDisabled ? "Enterprise feature - Available in Synapse Enterprise" : "";

        return (
          <li
            key={recipe.title}
            onClick={() => !isDisabled && onSelectRecipe(recipe)}
            className={listClass.elem("template").mod({ disabled: isDisabled })}
            title={title}
          >
            <img src={recipe.image} alt={""} />
            <div className="flex w-full relative">
              <h3 className="flex flex-1 justify-center text-center">{recipe.title}</h3>
              {isEnterpriseTemplate && isCommunityEdition && (
                <EnterpriseBadge className="absolute bottom-[-10px] left-1/2 translate-x-[-40px]" />
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export const TemplatesList = ({ selectedGroup, selectedRecipe, onCustomTemplate, onSelectGroup, onSelectRecipe, detectedFileType }) => {
  const [groups, setGroups] = React.useState([]);
  const [templates, setTemplates] = React.useState();
  const api = useAPI();
  const isEdition = window?.APP_SETTINGS?.version_edition;

  React.useEffect(() => {
    const fetchData = async () => {
      const res = await api.callApi("configTemplates");

      if (!res) return;
      const { templates, groups } = res;

      setTemplates(templates);
      setTemplates(templates);

      // Inject Medical 3D Template
      templates.push({
          title: "3D Medical Volume",
          group: "Medical Imaging",
          config: '<View>\n  <Dicom3D name="volume" value="$volume" />\n</View>',
          image: "https://ls-assets.s3.amazonaws.com/templates/medical.png",
          type: "community"
      });
      
      // Ensure "Medical Imaging" group exists if we have templates for it
      // This handles cases where backend doesn't explicitly return the group in the list
      if (!groups.includes("Medical Imaging") && templates.some(t => t.group === "Medical Imaging")) {
        groups.push("Medical Imaging");
      }
      
      setGroups(groups);
    };
    fetchData();
  }, []);

  // Filter groups to only those that have at least one compatible template
  const filteredGroups = React.useMemo(() => {
      if (!groups || !templates) return [];
      return groups.filter(group => {
          return templates.some(t => t.group === group && isCompatible(t, detectedFileType));
      });
  }, [groups, templates, detectedFileType]);

  const selected = selectedGroup || filteredGroups[0];

  return (
    <div className={listClass}>
      <aside className={listClass.elem("sidebar")}>
        <ul>
          {filteredGroups.map((group) => (
            <li
              key={group}
              onClick={() => onSelectGroup(group)}
              className={listClass.elem("group").mod({
                active: selected === group,
                selected: selectedRecipe?.group === group,
              })}
            >
              {group}
              <Arrow />
            </li>
          ))}
        </ul>
        <Button
          type="button"
          align="left"
          look="string"
          size="small"
          onClick={onCustomTemplate}
          className="w-full"
          aria-label="Create custom template"
        >
          Custom template
        </Button>
      </aside>
      <main>
        {!templates && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 200, width: "100%" }}>
            <Spinner size={40} />
          </div>
        )}
        <TemplatesInGroup
          templates={templates || []}
          group={selected}
          onSelectRecipe={onSelectRecipe}
          isEdition={isEdition}
          detectedFileType={detectedFileType}
        />
      </main>
      <footer className="flex items-center justify-center gap-1">
        <IconInfo className={listClass.elem("info-icon")} width="20" height="20" />
        <span>
          See the documentation to{" "}
          <a href="https://synapse.io/guide" target="_blank" rel="noreferrer">
            contribute a template
          </a>
          .
        </span>
      </footer>
    </div>
  );
};

