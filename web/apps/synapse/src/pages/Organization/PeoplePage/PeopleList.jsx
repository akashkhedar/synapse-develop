import { formatDistance } from "date-fns";
import { useCallback, useEffect, useState } from "react";
import { Userpic } from "@synapse/ui";
import { Pagination, Spinner } from "../../../components";
import { usePage, usePageSize } from "../../../components/Pagination/Pagination";
import { useAPI } from "../../../providers/ApiProvider";
import { cn } from "../../../utils/bem";
import { isDefined } from "../../../utils/helpers";
import "./PeopleList.scss";
import { CopyableTooltip } from "../../../components/CopyableTooltip/CopyableTooltip";

export const PeopleList = ({ onSelect, selectedUser, defaultSelected, organizationId, refreshTrigger }) => {
  const api = useAPI();
  const [usersList, setUsersList] = useState();
  const [currentPage] = usePage("page", 1);
  const [currentPageSize] = usePageSize("page_size", 30);
  const [totalItems, setTotalItems] = useState(0);

  const fetchUsers = useCallback(async (page, pageSize) => {
    // Use provided organizationId or fetch from user data
    const orgId = organizationId || (await api.callApi("me").then(user => user.active_organization));
    
    const response = await api.callApi("memberships", {
      params: {
        pk: orgId,
        contributed_to_projects: 1,
        page,
        page_size: pageSize,
      },
    });

    if (response.results) {
      setUsersList(response.results);
      setTotalItems(response.count);
    }
  }, [organizationId]);

  const selectUser = useCallback(
    (user, role) => {
      if (selectedUser?.id === user.id) {
        onSelect?.(null, null);
      } else {
        onSelect?.(user, role);
      }
    },
    [selectedUser, onSelect],
  );

  const getRoleBadge = (role) => {
    if (role === 'owner') {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '10px',
          backgroundColor: '#FFD700',
          color: '#000',
          fontSize: '11px',
          fontWeight: '600',
        }}>
          👑 Owner
        </span>
      );
    }
    if (role === 'admin') {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '10px',
          backgroundColor: '#3B82F6',
          color: '#fff',
          fontSize: '11px',
          fontWeight: '600',
        }}>
          ⭐ Admin
        </span>
      );
    }
    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        fontSize: '11px',
        color: '#6B7280',
      }}>
        Member
      </span>
    );
  };

  useEffect(() => {
    fetchUsers(currentPage, currentPageSize);
  }, [refreshTrigger]);

  useEffect(() => {
    if (isDefined(defaultSelected) && usersList) {
      const selected = usersList.find(({ user }) => user.id === Number(defaultSelected));

      if (selected) selectUser(selected.user, selected.role);
    }
  }, [usersList, defaultSelected]);

  return (
    <>
      <div className={cn("people-list").toClassName()}>
        <div className={cn("people-list").elem("wrapper").toClassName()}>
          {usersList ? (
            <div className={cn("people-list").elem("users").toClassName()}>
              <div className={cn("people-list").elem("header").toClassName()}>
                <div className={cn("people-list").elem("column").mix("avatar").toClassName()} />
                <div className={cn("people-list").elem("column").mix("email").toClassName()}>Email</div>
                <div className={cn("people-list").elem("column").mix("name").toClassName()}>Name</div>
                <div className={cn("people-list").elem("column").mix("role").toClassName()}>Role</div>
                <div className={cn("people-list").elem("column").mix("last-activity").toClassName()}>Last Activity</div>
              </div>
              <div className={cn("people-list").elem("body").toClassName()}>
                {usersList.map(({ user, role }) => {
                  const active = user.id === selectedUser?.id;

                  return (
                    <div
                      key={`user-${user.id}`}
                      className={cn("people-list").elem("user").mod({ active }).toClassName()}
                      onClick={() => selectUser(user, role)}
                    >
                      <div className={cn("people-list").elem("field").mix("avatar").toClassName()}>
                        <CopyableTooltip title={`User ID: ${user.id}`} textForCopy={user.id}>
                          <Userpic user={user} style={{ width: 28, height: 28 }} />
                        </CopyableTooltip>
                      </div>
                      <div className={cn("people-list").elem("field").mix("email").toClassName()}>{user.email}</div>
                      <div className={cn("people-list").elem("field").mix("name").toClassName()}>
                        {user.first_name} {user.last_name}
                      </div>
                      <div className={cn("people-list").elem("field").mix("role").toClassName()}>
                        {getRoleBadge(role)}
                      </div>
                      <div className={cn("people-list").elem("field").mix("last-activity").toClassName()}>
                        {formatDistance(new Date(user.last_activity), new Date(), { addSuffix: true })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className={cn("people-list").elem("loading").toClassName()}>
              <Spinner size={36} />
            </div>
          )}
        </div>
        <Pagination
          page={currentPage}
          urlParamName="page"
          totalItems={totalItems}
          pageSize={currentPageSize}
          pageSizeOptions={[30, 50, 100]}
          onPageLoad={fetchUsers}
          style={{ paddingTop: 16 }}
        />
      </div>
    </>
  );
};

