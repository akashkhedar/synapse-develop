import { EnterpriseBadge, IconSpark } from "@synapse/ui";
import { Alert, AlertTitle, AlertDescription } from "@synapse/shad/components/ui/alert";
import { IconCloudProviderAzure } from "@synapse/icons";
import type { ProviderConfig } from "@synapse/app-common/blocks/StorageProviderForm/types/provider";

const azureSpiProvider: ProviderConfig = {
  name: "azure_spi",
  title: "Azure Blob Storage\nwith Service Principal",
  description:
    "Configure your Azure Blob Storage connection using Service Principal authentication for enhanced security (proxy only)",
  icon: IconCloudProviderAzure,
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
            Azure Blob Storage with Service Principal is available in Synapse Enterprise.{" "}
            <a
              href="https://docs.Synapse.com/guide/storage.html#Azure-Blob-Storage-with-Service-Principal-authentication"
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

export default azureSpiProvider;

