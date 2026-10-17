import type {
  ConversationState,
  Health,
  Order,
  Product,
  WorkflowResponse,
} from "./api-types";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
const apiDisplayUrl = new URL(apiBaseUrl, window.location.origin).toString().replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(
      0,
      `Can't reach DukaanVoice API at ${apiDisplayUrl}. Start the backend with the “Start DukaanVoice” task, then retry.`,
    );
  }

  const correlationId = response.headers.get("X-Correlation-ID");
  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const responseText = await response.text();
      try {
        const body: { detail?: string } = JSON.parse(responseText);
        if (body.detail) message = body.detail;
      } catch {
        if (response.status >= 500 && responseText.toLowerCase().includes("proxy error")) {
          message = `Can't reach DukaanVoice backend at ${apiDisplayUrl}. Start the backend with the “Start DukaanVoice” task, then retry.`;
        }
      }
    } catch {
      // Keep the status-based message when the response body cannot be read.
    }
    if (correlationId) message = `${message} (Request ${correlationId})`;
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  products: () => request<Product[]>("/products"),
  product: (id: string) => request<Product>(`/products/${encodeURIComponent(id)}`),
  orders: () => request<Order[]>("/orders"),
  order: (id: string) => request<Order>(`/orders/${encodeURIComponent(id)}`),
  session: (id: string) => request<ConversationState>(`/sessions/${encodeURIComponent(id)}`),
  createTextOrder: (data: { session_id: string; transcript: string; language?: string }) =>
    request<WorkflowResponse>("/orders/text", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(data),
    }),
  clarifyOrder: (data: {
    session_id: string;
    selected_product_id?: string;
    quantity?: number;
    clarification_text?: string;
  }) =>
    request<WorkflowResponse>("/orders/clarify", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  confirmOrder: (id: string) =>
    request<Order>(`/orders/${encodeURIComponent(id)}/confirm`, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
    }),
  cancelOrder: (id: string) =>
    request<Order>(`/orders/${encodeURIComponent(id)}/cancel`, { method: "POST" }),
  updateQuantity: (id: string, productId: string, quantity: number) =>
    request<Order>(`/orders/${encodeURIComponent(id)}/items/${encodeURIComponent(productId)}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  removeItem: (id: string, productId: string) =>
    request<Order>(`/orders/${encodeURIComponent(id)}/items/${encodeURIComponent(productId)}`, {
      method: "DELETE",
    }),
};

export { apiBaseUrl };
