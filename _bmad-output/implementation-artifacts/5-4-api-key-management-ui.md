# Story 5.4: API Key Management UI

Status: ready-for-dev

## Story

As a developer,
I want to create, view, copy, revoke, and regenerate API keys from the dashboard,
so that I can manage my Resili access without touching the raw API.

## Acceptance Criteria

1. **Given** `/dashboard/keys`, **When** rendered, **Then** it lists all active API keys via `api-key-list.tsx`: each row shows name/id, `created_at`, masked key (e.g. `rsl_****1234`), "Revoke" and "Regenerate" buttons.

2. **Given** clicking "Create new key", **When** the API responds, **Then** the full plaintext key is displayed once in a highlighted `code-window`-styled box with a "Copy to clipboard" button; after dismissing, the key is masked.

3. **Given** clicking "Copy to clipboard" on the creation dialog, **When** clicked, **Then** the key is copied to the clipboard and the button label changes to "Copied ✓" for 2 seconds.

4. **Given** clicking "Revoke" on a key, **When** confirmed, **Then** DELETE `/api/v1/keys/{id}` is called, the key disappears from the list, and a toast notification confirms "Key revoked."

5. **Given** the `api-key-list.tsx` component data loading, **When** loading, **Then** a skeleton loader is shown using TanStack Query's `isLoading` state — no manual `useState(loading)`.

## Tasks / Subtasks

- [ ] Create `api-key-list.tsx` component (AC: 1, 5)
  - [ ] TanStack Query: `useQuery({ queryKey: ['keys'], queryFn: getKeys })`
  - [ ] Skeleton loader when `isLoading`
  - [ ] Render rows with masked key, Revoke/Regenerate buttons

- [ ] Implement key masking (AC: 1)
  - [ ] Show first 4 + last 4 chars: `rsl_****1234`

- [ ] Implement "Create new key" flow (AC: 2, 3)
  - [ ] Dialog/modal with plaintext key display
  - [ ] Copy to clipboard with "Copied ✓" feedback (2 seconds)
  - [ ] After dismiss: key is masked in list

- [ ] Implement revoke with confirmation + toast (AC: 4)
  - [ ] Confirmation dialog before DELETE
  - [ ] Toast notification on success

- [ ] Complete `/dashboard/keys/page.tsx` (AC: 1, 2, 3, 4, 5)

## Dev Notes

### `src/hooks/use-api-keys.ts` — TanStack Query Hook

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getKeys, createKey, revokeKey, regenerateKey } from "@/lib/api/endpoints";

export function useApiKeys() {
  return useQuery({
    queryKey: ["keys"],
    queryFn: getKeys,
  });
}

export function useCreateKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name?: string) => createKey(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["keys"] }),
  });
}

export function useRevokeKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => revokeKey(keyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["keys"] }),
  });
}
```

**NEVER** use `useState(loading)` for data fetching state — always use TanStack Query's `isLoading`.

### Key Masking Utility

```typescript
// src/lib/utils.ts
export function maskApiKey(key: string): string {
  // "rsl_abcdefghij...xyz" → "rsl_****1234"
  if (key.length <= 8) return key;
  const last4 = key.slice(-4);
  return `rsl_****${last4}`;
}
```

### `src/components/dashboard/api-key-list.tsx`

```typescript
"use client";
import { useApiKeys, useRevokeKey } from "@/hooks/use-api-keys";
import { maskApiKey } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { useState } from "react";

export function ApiKeyList() {
  const { data, isLoading } = useApiKeys();
  const revokeKey = useRevokeKey();
  const [revokeConfirm, setRevokeConfirm] = useState<string | null>(null);

  if (isLoading) {
    // Skeleton loader — TanStack Query isLoading (AC: 5)
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-14 bg-surface-card rounded-md animate-pulse border border-hairline" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {data?.items.map(key => (
        <div key={key.id}
          className="flex items-center justify-between p-4 bg-surface-card border border-hairline rounded-md"
        >
          <div>
            <p className="text-ink text-body-sm font-medium">{key.name || "Unnamed key"}</p>
            <p className="text-charcoal text-caption font-mono mt-0.5">{maskApiKey("rsl_" + "x".repeat(20) + key.id.slice(-4))}</p>
            <p className="text-mute text-caption">Created {new Date(key.created_at).toLocaleDateString()}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" className="text-body-sm h-8 px-3"
              onClick={() => setRevokeConfirm(key.id)}>
              Revoke
            </Button>
            <Button variant="outline" className="text-body-sm h-8 px-3">
              Regenerate
            </Button>
          </div>
        </div>
      ))}

      {/* Revoke confirmation */}
      {revokeConfirm && (
        <ConfirmDialog
          message="Revoke this API key? This cannot be undone."
          onConfirm={() => {
            revokeKey.mutate(revokeConfirm);
            setRevokeConfirm(null);
            // Show toast
          }}
          onCancel={() => setRevokeConfirm(null)}
        />
      )}
    </div>
  );
}
```

### Copy to Clipboard (AC: 3)

```typescript
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);  // Reset after 2s
  }

  return (
    <Button variant="ghost" onClick={handleCopy} className="text-body-sm h-8 px-3">
      {copied ? "Copied ✓" : "Copy to clipboard"}
    </Button>
  );
}
```

### New Key Display Dialog (AC: 2)

After creating a key, display in a modal:
```typescript
function NewKeyDialog({ apiKey, onClose }: { apiKey: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-canvas/80 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-hairline-strong rounded-lg p-6 max-w-lg w-full mx-4">
        <h2 className="text-display-xs text-ink font-display mb-2">API Key Created</h2>
        <p className="text-charcoal text-body-sm mb-4">
          Save this key now — it won't be shown again.
        </p>
        {/* code-window styled box */}
        <div className="bg-surface-deep border border-hairline-strong rounded-md p-4 font-mono text-code-md text-accent-green mb-4">
          {apiKey}
        </div>
        <div className="flex gap-3">
          <CopyButton text={apiKey} />
          <Button variant="outline" onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  );
}
```

### Toast Notification

Simple toast (no external library needed for MVP):
```typescript
// src/components/ui/Toast.tsx
export function Toast({ message }: { message: string }) {
  return (
    <div className="fixed bottom-4 right-4 bg-surface-elevated border border-hairline-strong
                    rounded-md px-4 py-3 text-ink text-body-sm z-50 animate-in">
      {message}
    </div>
  );
}
```

### `/dashboard/keys/page.tsx`

```typescript
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { ApiKeyList } from "@/components/dashboard/api-key-list";
import { useCreateKey } from "@/hooks/use-api-keys";

export default function KeysPage() {
  const [newKey, setNewKey] = useState<string | null>(null);
  const createKey = useCreateKey();

  async function handleCreate() {
    const result = await createKey.mutateAsync();
    setNewKey(result.key);  // Show plaintext key once
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-display-sm text-ink font-display">API Keys</h1>
        <Button variant="primary" onClick={handleCreate} disabled={createKey.isPending}>
          {createKey.isPending ? "Creating..." : "Create new key"}
        </Button>
      </div>
      <ApiKeyList />
      {newKey && <NewKeyDialog apiKey={newKey} onClose={() => setNewKey(null)} />}
    </div>
  );
}
```

### References

- [Source: architecture.md#Dec-I-Server-State-Management] — TanStack Query mandatory
- [Source: epics.md#Story-5.4] — acceptance criteria
- [Source: architecture.md#Enforcement-Guidelines] — no manual loading state

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `frontend/src/app/dashboard/keys/page.tsx` — complete implementation

**NEW:**
- `frontend/src/hooks/use-api-keys.ts`
- `frontend/src/components/dashboard/api-key-list.tsx`
- `frontend/src/components/dashboard/api-key-list.test.tsx`
- `frontend/src/components/ui/Toast.tsx`
- `frontend/src/components/ui/ConfirmDialog.tsx`
- `frontend/src/lib/utils.ts` — add maskApiKey
