import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { StaticContent } from "../../app/StaticContent/StaticContent";
import {
  IconBook,
  IconFolderOpen,
  IconHome,
  IconHotkeys,
  IconPeople,
  IconGear,
  IconPin,
  IconTerminal,
  IconDoor,
  IconSpark,
  IconMastercard,
} from "@synapse/icons";
import { LSLogo } from "../../assets/images";
import { Button, Userpic, ThemeToggle } from "@synapse/ui";
import { useConfig } from "../../providers/ConfigProvider";
import {
  useContextComponent,
  useFixedLocation,
} from "../../providers/RoutesProvider";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { cn } from "../../utils/bem";
import { absoluteURL, isDefined } from "../../utils/helpers";
import { Breadcrumbs } from "../Breadcrumbs/Breadcrumbs";
import { Dropdown } from "@synapse/ui";
import { Hamburger } from "../Hamburger/Hamburger";
import { Menu } from "../Menu/Menu";
import {
  VersionNotifier,
  VersionProvider,
} from "../VersionNotifier/VersionNotifier";
import { OrganizationSwitcher } from "../OrganizationSwitcher/OrganizationSwitcher";
import { CreditBalance } from "../CreditBalance/CreditBalance";
import "./Menubar.scss";
import "./MenuContent.scss";
import "./MenuSidebar.scss";
import { FF_HOMEPAGE } from "../../utils/feature-flags";
import { pages } from "@synapse/app-common";
import { isFF } from "../../utils/feature-flags";
import { ff } from "@synapse/core";
import { openHotkeyHelp } from "@synapse/app-common/pages/AccountSettings/sections/Hotkeys/Help";
import { useHistory } from "react-router";

export const MenubarContext = createContext();

const LeftContextMenu = ({ className }) => (
  <StaticContent id="context-menu-left" className={className}>
    {(template) => <Breadcrumbs fromTemplate={template} />}
  </StaticContent>
);

const RightContextMenu = ({ className, ...props }) => {
  const { ContextComponent, contextProps } = useContextComponent();

  return ContextComponent ? (
    <div className={className}>
      <ContextComponent {...props} {...(contextProps ?? {})} />
    </div>
  ) : (
    <StaticContent id="context-menu-right" className={className} />
  );
};

export const Menubar = ({
  enabled,
  defaultOpened,
  defaultPinned,
  children,
  onSidebarToggle,
  onSidebarPin,
}) => {
  const menuDropdownRef = useRef();
  const useMenuRef = useRef();
  const { user, isLoading } = useAuth();
  // Use role flags from user object for RBAC
  const isAnnotator = !!user?.is_annotator;
  const isClient = !!user?.is_client;
  const isExpert = !!user?.is_expert;
  console.log(isExpert)
  // Experts and annotators have limited menu (no org, no billing, but show earnings)
  // Only show limited menu if user data is loaded AND user has limited role
  const hasLimitedMenu = !isLoading && user && (isAnnotator || isExpert);
  // Only show full menu items if user data is loaded AND user is NOT limited
  const showFullMenu = !isLoading && user && !hasLimitedMenu;

  const location = useFixedLocation();
  const history = useHistory();

  const config = useConfig();
  const [sidebarOpened, setSidebarOpened] = useState(defaultOpened ?? false);
  const [sidebarPinned, setSidebarPinned] = useState(defaultPinned ?? false);
  const [PageContext, setPageContext] = useState({
    Component: null,
    props: {},
  });

  const menubarClass = cn("menu-header");
  const menubarContext = menubarClass.elem("context");
  const sidebarClass = cn("sidebar");
  const contentClass = cn("content-wrapper");
  const contextItem = menubarClass.elem("context-item");

  const sidebarPin = useCallback(
    (e) => {
      e.preventDefault();

      const newState = !sidebarPinned;

      setSidebarPinned(newState);
      onSidebarPin?.(newState);
    },
    [sidebarPinned]
  );

  const sidebarToggle = useCallback(
    (visible) => {
      const newState = visible;

      setSidebarOpened(newState);
      onSidebarToggle?.(newState);
    },
    [sidebarOpened]
  );

  const providerValue = useMemo(
    () => ({
      PageContext,

      setContext(ctx) {
        setTimeout(() => {
          setPageContext({
            ...PageContext,
            Component: ctx,
          });
        });
      },

      setProps(props) {
        setTimeout(() => {
          setPageContext({
            ...PageContext,
            props,
          });
        });
      },

      contextIsSet(ctx) {
        return PageContext.Component === ctx;
      },
    }),
    [PageContext]
  );

  useEffect(() => {
    if (!sidebarPinned) {
      menuDropdownRef?.current?.close();
    }
    useMenuRef?.current?.close();
  }, [location]);

  return (
    <div className={contentClass}>
      {enabled && (
        <div className={menubarClass}>
          <Dropdown.Trigger
            dropdown={menuDropdownRef}
            closeOnClickOutside={!sidebarPinned}
          >
            <div
              className={`${menubarClass.elem("trigger")} main-menu-trigger`}
            >
              <h3>
                <b>Synapse</b>
              </h3>
              <Hamburger opened={sidebarOpened} />
            </div>
          </Dropdown.Trigger>
          <div className={menubarContext}>
            <LeftContextMenu className={contextItem.mod({ left: true })} />
            <RightContextMenu className={contextItem.mod({ right: true })} />
          </div>
          {showFullMenu && (
            <OrganizationSwitcher
              className={menubarClass.elem("organization")}
            />
          )}
          {showFullMenu && (
            <div className={menubarClass.elem("credits")}>
              <CreditBalance onClick={() => history.push("/billing")} />
            </div>
          )}
          <div className={menubarClass.elem("hotkeys")}>
            <div className={menubarClass.elem("hotkeys-button")}>
              <Button
                variant="neutral"
                look="outlined"
                tooltip="Keyboard Shortcuts"
                data-testid="hotkeys-button"
                size="small"
                onClick={() => {
                  openHotkeyHelp([
                    "annotation",
                    "data_manager",
                    "regions",
                    "tools",
                    "audio",
                    "video",
                    "timeseries",
                    "image_gallery",
                  ]);
                }}
                icon={<IconHotkeys />}
              />
            </div>
          </div>
          
          <Dropdown.Trigger
            ref={useMenuRef}
            align="right"
            content={
              <Menu>
                <Menu.Item
                  icon={<IconGear />}
                  label="Account & Settings"
                  href={pages.AccountSettingsPage.path}
                />
                {/* <Menu.Item label="Dark Mode"/> */}
                <Menu.Item
                  icon={<IconDoor />}
                  label="Log Out"
                  href={absoluteURL("/logout")}
                  data-external
                />
              </Menu>
            }
          >
            <div title={user?.email} className={menubarClass.elem("user")}>
              <Userpic user={user} isInProgress={isLoading} />
              
            </div>
          </Dropdown.Trigger>
        </div>
      )}

      <VersionProvider>
        <div className={contentClass.elem("body")}>
          {enabled && (
            <Dropdown
              ref={menuDropdownRef}
              onToggle={sidebarToggle}
              onVisibilityChanged={() =>
                window.dispatchEvent(new Event("resize"))
              }
              visible={sidebarOpened}
              className={[
                sidebarClass,
                sidebarClass.mod({ floating: !sidebarPinned }),
              ].join(" ")}
              style={{ width: 240 }}
            >
              <Menu>
                {isFF(FF_HOMEPAGE) && showFullMenu && (
                  <Menu.Item
                    label="Dashboard"
                    to="/dashboard"
                    icon={<IconHome />}
                    data-external
                    exact
                  />
                )}
                <Menu.Item
                  label="Projects"
                  to="/projects"
                  icon={<IconFolderOpen />}
                  data-external
                  exact
                />
                {showFullMenu && (
                  <Menu.Item
                    label="Organization"
                    to="/organization"
                    icon={<IconPeople />}
                    data-external
                    exact
                  />
                )}
                {showFullMenu ? (
                  <Menu.Item
                    label="Billing & Credits"
                    to="/billing"
                    icon={<IconMastercard />}
                    data-external
                    exact
                  />
                ) : hasLimitedMenu ? (
                  <>
                    <Menu.Item
                      label="Earnings"
                      to={
                        // Only pure experts go to expert earnings; annotators (even with expert flag) go to annotator earnings
                        isExpert && !isAnnotator ? "/expert/earnings" : "/annotators/earnings"
                      }
                      icon={<IconSpark />}
                      data-external
                      exact
                    />
                  </>
                ) : null}

                <Menu.Spacer />

                <Menu.Divider />

                <Menu.Item
                  icon={<IconPin />}
                  className={sidebarClass.elem("pin")}
                  onClick={sidebarPin}
                  active={sidebarPinned}
                >
                  {sidebarPinned ? "Unpin menu" : "Pin menu"}
                </Menu.Item>
              </Menu>
            </Dropdown>
          )}

          <MenubarContext.Provider value={providerValue}>
            <div
              className={contentClass
                .elem("content")
                .mod({ withSidebar: sidebarPinned && sidebarOpened })}
            >
              {children}
            </div>
          </MenubarContext.Provider>
        </div>
      </VersionProvider>
    </div>
  );
};

