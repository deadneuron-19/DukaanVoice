export interface Product {
  product_id: string;
  canonical_name: string;
  brand: string;
  category: string;
  pack_size: number;
  unit: string;
  price: string;
  available_stock: number;
  alternative_product_ids: string[];
  is_active: boolean;
}

export interface OrderItem {
  product_id: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export type OrderStatus =
  | "draft"
  | "needs_clarification"
  | "awaiting_confirmation"
  | "confirmed"
  | "cancelled"
  | "failed";

export interface Order {
  order_id: string;
  session_id: string;
  items: OrderItem[];
  subtotal: string;
  discount: string;
  total: string;
  status: OrderStatus;
  created_at: string | null;
  updated_at: string | null;
  confirmed_at: string | null;
  idempotency_key: string | null;
  confirmation_idempotency_key?: string | null;
}

export interface ProductOption {
  product_id: string;
  name: string;
  brand: string;
  pack_size: number;
  unit: string;
  price: string;
  available_stock: number;
}

export interface WorkflowResponse {
  status: OrderStatus;
  transcript: string | null;
  order: Order | null;
  clarification_question: string | null;
  candidates: ProductOption[];
  error: string | null;
}

export interface ConversationMessage {
  role: string;
  content: string;
  created_at?: string | null;
}

export interface ConversationState {
  session_id: string;
  current_state: string;
  draft_order_id: string | null;
  pending_clarification: string | null;
  conversation_history: ConversationMessage[];
  last_updated_at: string | null;
  expires_at: string | null;
}

export interface Health {
  status: string;
  app: string;
  environment: string;
}
