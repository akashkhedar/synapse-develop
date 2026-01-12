import { format } from "date-fns";
import styles from "./MembershipInfo.module.scss";
import { useQuery } from "@tanstack/react-query";
import { getApiInstance } from "@synapse/core";
import { useMemo } from "react";
import type { WrappedResponse } from "@synapse/core/lib/api-proxy/types";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { ROLES } from "./index";

function formatDate(date?: string) {
  return format(new Date(date ?? ""), "dd MMM yyyy, KK:mm a");
}

// Role badge component
const RoleBadge = ({ role }: { role: string }) => {
  const roleColors: Record<string, { bg: string; border: string; text: string }> = {
    Owner: { bg: 'rgba(139, 92, 246, 0.15)', border: 'rgba(139, 92, 246, 0.3)', text: '#a78bfa' },
    Administrator: { bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)', text: '#60a5fa' },
    Manager: { bg: 'rgba(34, 197, 94, 0.15)', border: 'rgba(34, 197, 94, 0.3)', text: '#4ade80' },
    Annotator: { bg: 'rgba(251, 191, 36, 0.15)', border: 'rgba(251, 191, 36, 0.3)', text: '#fbbf24' },
    Reviewer: { bg: 'rgba(236, 72, 153, 0.15)', border: 'rgba(236, 72, 153, 0.3)', text: '#f472b6' },
    Pending: { bg: 'rgba(107, 114, 128, 0.15)', border: 'rgba(107, 114, 128, 0.3)', text: '#9ca3af' },
    Deactivated: { bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)', text: '#f87171' },
  };

  const colors = roleColors[role] || roleColors.Pending;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '4px 12px',
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        color: colors.text,
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
      }}
    >
      {role}
    </span>
  );
};

// Stat card component
const StatCard = ({ 
  label, 
  value, 
  icon 
}: { 
  label: string; 
  value: string | number | undefined; 
  icon?: React.ReactNode;
}) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      padding: '20px',
      background: 'rgba(255, 255, 255, 0.02)',
      border: '1px solid #1f1f1f',
    }}
  >
    <span
      style={{
        fontSize: '12px',
        color: '#6b7280',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        fontFamily: 'monospace',
      }}
    >
      {label}
    </span>
    <span
      style={{
        fontSize: '24px',
        fontWeight: 700,
        color: '#fff',
        letterSpacing: '-0.02em',
      }}
    >
      {value ?? '—'}
    </span>
  </div>
);

// Info row component
const InfoRow = ({ 
  label, 
  value, 
  highlight 
}: { 
  label: string; 
  value: React.ReactNode; 
  highlight?: boolean;
}) => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '14px 0',
      borderBottom: '1px solid #1f1f1f',
    }}
  >
    <span style={{ color: '#6b7280', fontFamily: 'monospace', fontSize: '14px' }}>
      {label}
    </span>
    <span style={{ color: highlight ? '#8b5cf6' : '#fff', fontSize: '14px', fontWeight: 500 }}>
      {value}
    </span>
  </div>
);

export const MembershipInfo = () => {
  const { user } = useAuth();
  const dateJoined = useMemo(() => {
    if (!user?.date_joined) return null;
    return formatDate(user?.date_joined);
  }, [user?.date_joined]);

  const membership = useQuery({
    queryKey: [user?.active_organization, user?.id, "user-membership"],
    async queryFn() {
      if (!user) return {};
      const api = getApiInstance();
      const response = (await api.invoke("userMemberships", {
        pk: user.active_organization,
        userPk: user.id,
      })) as WrappedResponse<{
        user: number;
        organization: number;
        contributed_projects_count: number;
        annotations_count: number;
        created_at: string;
        role: string;
      }>;

      const annotationCount = response?.annotations_count;
      const contributions = response?.contributed_projects_count;
      let role = "Owner";
      let roleCode = response.role;

      switch (response.role) {
        case "OW":
          role = "Owner";
          break;
        case "DI":
          role = "Deactivated";
          break;
        case "AD":
          role = "Administrator";
          break;
        case "MA":
          role = "Manager";
          break;
        case "AN":
          role = "Annotator";
          break;
        case "RE":
          role = "Reviewer";
          break;
        case "NO":
          role = "Pending";
          break;
      }

      return {
        annotationCount,
        contributions,
        role,
        roleCode,
      };
    },
  });

  const organization = useQuery({
    queryKey: ["organization", user?.active_organization],
    async queryFn() {
      if (!user) return null;
      if (!window?.APP_SETTINGS?.billing) return null;
      const api = getApiInstance();
      const organization = (await api.invoke("organization", {
        pk: user.active_organization,
      })) as WrappedResponse<{
        id: number;
        external_id: string;
        title: string;
        token: string;
        default_role: string;
        created_at: string;
      }>;

      if (!organization.$meta.ok) {
        return null;
      }

      return {
        ...organization,
        createdAt: formatDate(organization.created_at),
      } as const;
    },
  });

  const isAnnotator = membership.data?.roleCode === ROLES.ANNOTATOR;

  return (
    <div className={styles.membershipInfo} id="membership-info">
      {/* Stats Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1px',
          background: '#1f1f1f',
          border: '1px solid #1f1f1f',
        }}
      >
        <StatCard
          label="Annotations"
          value={membership.data?.annotationCount?.toLocaleString()}
        />
        <StatCard
          label="Projects"
          value={membership.data?.contributions}
        />
        <StatCard
          label="Member Since"
          value={dateJoined ? format(new Date(user?.date_joined ?? ""), "MMM yyyy") : "—"}
        />
      </div>

      {/* User Info Section */}
      <div style={{ marginTop: '2rem' }}>
        <h3
          style={{
            fontSize: '14px',
            fontWeight: 600,
            color: '#8b5cf6',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            marginBottom: '1rem',
            fontFamily: 'monospace',
          }}
        >
          Account Details
        </h3>
        <div>
          <InfoRow label="User ID" value={user?.id} />
          <InfoRow label="Registration Date" value={dateJoined} />
          {membership.data?.role && (
            <InfoRow 
              label="My Role" 
              value={<RoleBadge role={membership.data.role} />}
            />
          )}
        </div>
      </div>

      {/* Organization Section - Only for non-annotators */}
      {!isAnnotator && user?.active_organization_meta && (
        <div style={{ marginTop: '2rem' }}>
          <h3
            style={{
              fontSize: '14px',
              fontWeight: 600,
              color: '#8b5cf6',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '1rem',
              fontFamily: 'monospace',
            }}
          >
            Organization
          </h3>
          <div>
            <InfoRow 
              label="Name" 
              value={user.active_organization_meta.title}
              highlight
            />
            <InfoRow label="Organization ID" value={user.active_organization} />
            <InfoRow label="Owner" value={user.active_organization_meta.email} />
            {organization.data?.createdAt && (
              <InfoRow label="Created" value={organization.data.createdAt} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

