/**
 * Vitest setup — ensures jsdom's localStorage is available.
 *
 * Node.js 22+ ships a built-in localStorage that can shadow jsdom's
 * implementation when the --localstorage-file flag isn't set, causing
 * methods like clear() to be missing. This setup patches it.
 */

if (
  typeof globalThis.localStorage !== "undefined" &&
  typeof globalThis.localStorage.clear !== "function"
) {
  const store = new Map<string, string>();

  const storage: Storage = {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return [...store.keys()][index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };

  Object.defineProperty(globalThis, "localStorage", {
    value: storage,
    writable: true,
    configurable: true,
  });
}
