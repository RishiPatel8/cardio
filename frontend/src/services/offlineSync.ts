// Offline-First Synchronization Service for CardioGuard AI

interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  body: any;
  headers?: Record<string, string>;
  timestamp: number;
}

const STORAGE_KEY = "cardioguard_offline_queue";

class OfflineSyncService {
  private queue: QueuedRequest[] = [];
  private statusCallbacks: ((online: boolean, pendingCount: number) => void)[] = [];
  private isProcessing = false;

  constructor() {
    this.loadQueue();
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.handleNetworkStatusChange(true));
      window.addEventListener("offline", () => this.handleNetworkStatusChange(false));
    }
  }

  private loadQueue() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      this.queue = data ? JSON.parse(data) : [];
    } catch (e) {
      console.error("Failed to parse offline sync queue", e);
      this.queue = [];
    }
  }

  private saveQueue() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
      this.notifyStatus();
    } catch (e) {
      console.error("Failed to serialize offline queue storage", e);
    }
  }

  private handleNetworkStatusChange(online: boolean) {
    this.notifyStatus();
    if (online) {
      this.processQueue();
    }
  }

  public registerStatusCallback(callback: (online: boolean, pendingCount: number) => void) {
    this.statusCallbacks.push(callback);
    callback(this.isOnline(), this.queue.length);
    return () => {
      this.statusCallbacks = this.statusCallbacks.filter(cb => cb !== callback);
    };
  }

  private notifyStatus() {
    const online = this.isOnline();
    const count = this.queue.length;
    this.statusCallbacks.forEach(cb => cb(online, count));
  }

  public isOnline(): boolean {
    return typeof navigator !== "undefined" ? navigator.onLine : true;
  }

  public getPendingCount(): number {
    return this.queue.length;
  }

  public queueRequest(url: string, method: string, body: any, headers?: Record<string, string>) {
    const request: QueuedRequest = {
      id: "req_" + Math.random().toString(36).substr(2, 9),
      url,
      method,
      body,
      headers,
      timestamp: Date.now()
    };
    
    this.queue.push(request);
    this.saveQueue();

    if (this.isOnline()) {
      this.processQueue();
    }
  }

  public async processQueue() {
    if (this.isProcessing || this.queue.length === 0 || !this.isOnline()) return;
    this.isProcessing = true;

    console.log(`[OfflineSync] Started processing ${this.queue.length} pending items...`);

    while (this.queue.length > 0 && this.isOnline()) {
      const item = this.queue[0];
      try {
        const fetchOptions: RequestInit = {
          method: item.method,
          headers: {
            "Content-Type": "application/json",
            ...item.headers
          },
          body: item.body ? JSON.stringify(item.body) : undefined
        };

        const res = await fetch(item.url, fetchOptions);
        if (res.ok) {
          // Success! Drop from queue
          this.queue.shift();
          this.saveQueue();
          console.log(`[OfflineSync] Dispatched request: ${item.url}`);
        } else {
          // Server returned non-200. We will keep in queue and retry later, or skip if 4xx client errors
          if (res.status >= 400 && res.status < 500) {
            console.warn(`[OfflineSync] Skipping request due to client error: ${res.status}`);
            this.queue.shift();
            this.saveQueue();
          } else {
            console.error(`[OfflineSync] Server error ${res.status}, aborting sync run`);
            break;
          }
        }
      } catch (err) {
        console.error("[OfflineSync] Sync transmission failure, retrying later", err);
        break;
      }
    }

    this.isProcessing = false;
    this.notifyStatus();
  }
}

export const offlineSync = new OfflineSyncService();
