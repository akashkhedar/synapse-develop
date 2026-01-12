import { type FormEventHandler, useCallback, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Button, InputFile, ToastType, useToast, Userpic } from "@synapse/ui";
import { getApiInstance } from "@synapse/core";
import styles from "../AccountSettings.module.scss";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { atomWithMutation } from "jotai-tanstack-query";
import { useAtomValue } from "jotai";

/**
 * FIXME: This is legacy imports. We're not supposed to use such statements
 * each one of these eventually has to be migrated to core or ui
 */
import { Input } from "apps/synapse/src/components/Form/Elements";

const updateUserAvatarAtom = atomWithMutation(() => ({
  mutationKey: ["update-user"],
  async mutationFn({
    userId,
    body,
    isDelete,
  }: { userId: number; body: FormData; isDelete?: never } | { userId: number; isDelete: true; body?: never }) {
    const api = getApiInstance();
    const method = isDelete ? "deleteUserAvatar" : "updateUserAvatar";
    const response = await api.invoke(
      method,
      {
        pk: userId,
      },
      {
        body,
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response;
  },
}));

// Custom styled input component matching landing page design
const StyledInput = ({ 
  label, 
  ...props 
}: { 
  label: string; 
  [key: string]: any;
}) => (
  <div className="flex flex-col gap-2">
    <label 
      className="text-xs font-medium uppercase tracking-wider"
      style={{ color: '#9ca3af', letterSpacing: '0.1em' }}
    >
      {label}
    </label>
    <Input 
      {...props}
      style={{
        background: 'transparent',
        border: '1px solid #1f1f1f',
        color: '#fff',
        padding: '14px 16px',
        fontSize: '15px',
        borderRadius: 0,
        transition: 'border-color 0.2s',
        ...props.style,
      }}
    />
  </div>
);

export const PersonalInfo = () => {
  const toast = useToast();
  const { user, refetch: refetchUser, isLoading: userInProgress, update: updateUser } = useAuth();
  const updateUserAvatar = useAtomValue(updateUserAvatarAtom);
  const [isInProgress, setIsInProgress] = useState(false);
  const [fname, setFname] = useState(user?.first_name ?? "");
  const [lname, setLname] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const avatarRef = useRef<HTMLInputElement>();
  
  const fileChangeHandler: FormEventHandler<HTMLInputElement> = useCallback(
    async (e) => {
      if (!user) return;

      const input = e.currentTarget as HTMLInputElement;
      const body = new FormData();
      body.append("avatar", input.files?.[0] ?? "");
      const response = await updateUserAvatar.mutateAsync({
        body,
        userId: user.id,
      });

      if (!response.$meta.ok) {
        toast?.show({ message: response?.response?.detail ?? "Error updating avatar", type: ToastType.error });
      } else {
        toast?.show({ message: "Avatar updated successfully", type: ToastType.info });
        refetchUser();
      }
      input.value = "";
    },
    [user?.id],
  );

  const deleteUserAvatar = async () => {
    if (!user) return;
    await updateUserAvatar.mutateAsync({ userId: user.id, isDelete: true });
    toast?.show({ message: "Avatar removed", type: ToastType.info });
    refetchUser();
  };

  const userFormSubmitHandler: FormEventHandler = useCallback(
    async (e) => {
      e.preventDefault();
      if (!user) return;
      const body = new FormData(e.currentTarget as HTMLFormElement);
      const json = Object.fromEntries(body.entries());
      const response = await updateUser(json);

      refetchUser();
      if (!response) {
        toast?.show({ message: "Error updating user", type: ToastType.error });
      } else {
        toast?.show({ message: "Profile updated successfully", type: ToastType.info });
      }
    },
    [user?.id],
  );

  useEffect(() => {
    setIsInProgress(userInProgress);
  }, [userInProgress]);

  useEffect(() => {
    setFname(user?.first_name ?? "");
    setLname(user?.last_name ?? "");
    setPhone(user?.phone ?? "");
  }, [user]);

  return (
    <div className={styles.section} id="personal-info">
      <div className={styles.sectionContent}>
        {/* Avatar Section */}
        <div 
          className="flex items-center gap-6 p-6"
          style={{ 
            background: 'rgba(139, 92, 246, 0.05)', 
            border: '1px solid rgba(139, 92, 246, 0.15)' 
          }}
        >
          <div className="relative">
            <Userpic 
              user={user} 
              isInProgress={userInProgress} 
              size={96} 
              style={{ 
                flex: "none",
                border: '2px solid #1f1f1f',
              }} 
            />
            <div 
              className="absolute -bottom-1 -right-1 w-8 h-8 flex items-center justify-center"
              style={{ 
                background: '#8b5cf6',
                cursor: 'pointer',
              }}
              onClick={() => avatarRef.current?.click()}
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
                style={{ width: 16, height: 16, color: '#fff' }}
              >
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            <div>
              <h3 className="text-lg font-semibold" style={{ color: '#fff', margin: 0 }}>
                {user?.first_name} {user?.last_name}
              </h3>
              <p className="text-sm" style={{ color: '#6b7280', fontFamily: 'monospace', margin: '4px 0 0 0' }}>
                {user?.email}
              </p>
            </div>
            <div className="flex gap-2">
              <form className="hidden">
                <InputFile
                  name="avatar"
                  onChange={fileChangeHandler}
                  accept="image/png, image/jpeg, image/jpg"
                  ref={avatarRef}
                />
              </form>
              <Button 
                variant="neutral" 
                look="outlined" 
                size="small"
                onClick={() => avatarRef.current?.click()}
                style={{ 
                  borderRadius: 0,
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontSize: '11px',
                }}
              >
                Change Avatar
              </Button>
              {user?.avatar && (
                <Button 
                  variant="negative" 
                  look="outlined" 
                  size="small" 
                  onClick={deleteUserAvatar}
                  style={{ 
                    borderRadius: 0,
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontSize: '11px',
                  }}
                >
                  Remove
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Form Section */}
        <form onSubmit={userFormSubmitHandler} className={styles.sectionContent}>
          <div 
            className="grid gap-6"
            style={{ 
              gridTemplateColumns: 'repeat(2, 1fr)',
            }}
          >
            <StyledInput
              label="First Name"
              value={fname}
              onChange={(e: React.KeyboardEvent<HTMLInputElement>) => setFname(e.currentTarget.value)}
              name="first_name"
              placeholder="Enter first name"
            />
            <StyledInput
              label="Last Name"
              value={lname}
              onChange={(e: React.KeyboardEvent<HTMLInputElement>) => setLname(e.currentTarget.value)}
              name="last_name"
              placeholder="Enter last name"
            />
          </div>
          
          <div 
            className="grid gap-6"
            style={{ 
              gridTemplateColumns: 'repeat(2, 1fr)',
            }}
          >
            <StyledInput
              label="Email Address"
              type="email"
              readOnly={true}
              value={user?.email ?? ""}
              style={{ opacity: 0.6 }}
            />
            <StyledInput
              label="Phone Number"
              type="phone"
              onChange={(e: React.KeyboardEvent<HTMLInputElement>) => setPhone(e.currentTarget.value)}
              value={phone}
              name="phone"
              placeholder="Enter phone number"
            />
          </div>

          <div className={clsx(styles.flexRow, styles.flexEnd)} style={{ marginTop: '1rem' }}>
            <Button 
              waiting={isInProgress}
              style={{ 
                background: '#e8e4d9',
                color: '#000',
                borderRadius: 0,
                padding: '14px 32px',
                textTransform: 'uppercase',
                letterSpacing: '0.15em',
                fontSize: '13px',
                fontWeight: 600,
                border: 'none',
              }}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

