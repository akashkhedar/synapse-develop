import { EnterpriseBadge, IconSpark } from "@synapse/ui";
import { Alert, AlertTitle, AlertDescription } from "@synapse/shad/components/ui/alert";
import { IconCloudProviderDatabricks } from "@synapse/icons";
import type { ProviderConfig } from "@synapse/app-common/blocks/StorageProviderForm/types/provider";

const databricksProvider: ProviderConfig = {
  name: "databricks",
  title: "Databricks Files\n(UC Volumes)",
  description: "Configure your Databricks Unity Catalog Volumes connection with all required settings (proxy only)",
  icon: IconCloudProviderDatabricks,
  disabled: true,
  badge: <EnterpriseBadge />,
  fields: [
    {
      name: "enterprise_info",
      type: "message",
      content: (
        <Alert variant="gradient">
          <IconSpark />
          <AlertTitle>Enterprise Feature</AlertTitle>
          <AlertDescription>
            Databricks Files (UC Volumes) is available in Synapse Enterprise.{" "}
            <a
              href="https://docs.Synapse.com/guide/storage.html#Databricks-Files-UC-Volumes"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:no-underline"
            >
              Learn more
            </a>
          </AlertDescription>
        </Alert>
      ),
    },
  ],
  layout: [{ fields: ["enterprise_info"] }],
};

export default databricksProvider;

