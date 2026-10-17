import { Minus, Plus, Trash2 } from "lucide-react";
import type { Order, Product } from "../lib/api-types";
import { formatMoney, packLabel } from "../lib/format";
import { Button, StatusBadge } from "./ui";

export function OrderSummary({
  order,
  products,
  onQuantity,
  onRemove,
  onConfirm,
  onCancel,
  busy = false,
}: {
  order: Order;
  products: Product[];
  onQuantity?: (productId: string, quantity: number) => void;
  onRemove?: (productId: string) => void;
  onConfirm?: () => void;
  onCancel?: () => void;
  busy?: boolean;
}) {
  const productById = new Map(products.map((product) => [product.product_id, product]));
  const editable = order.status === "awaiting_confirmation";
  return (
    <section className="order-card">
      <div className="order-card-heading">
        <div><span className="eyebrow">ORDER SUMMARY</span><h2>Your basket</h2></div>
        <StatusBadge status={order.status} />
      </div>
      <div className="summary-items">
        {order.items.map((item) => {
          const product = productById.get(item.product_id);
          return (
            <div className="summary-row" key={item.product_id}>
              <div className="summary-product">
                <span className="product-dot">{product?.canonical_name.slice(0, 1) ?? "G"}</span>
                <div><strong>{product?.canonical_name ?? item.product_id}</strong><small>{product ? `${product.brand} · ${packLabel(product.pack_size, product.unit)}` : item.product_id}</small></div>
              </div>
              <div className="summary-price">
                <strong>{formatMoney(item.line_total)}</strong>
                <small>{formatMoney(item.unit_price)} each</small>
              </div>
              {editable && onQuantity && onRemove ? (
                <div className="quantity-actions">
                  <button aria-label={`Decrease ${product?.canonical_name ?? item.product_id} quantity`} disabled={busy || item.quantity <= 1} onClick={() => onQuantity(item.product_id, item.quantity - 1)}><Minus size={14} /></button>
                  <span>{item.quantity}</span>
                  <button aria-label={`Increase ${product?.canonical_name ?? item.product_id} quantity`} disabled={busy || (product !== undefined && item.quantity >= product.available_stock)} onClick={() => onQuantity(item.product_id, item.quantity + 1)}><Plus size={14} /></button>
                  <button aria-label={`Remove ${product?.canonical_name ?? item.product_id}`} className="remove-button" disabled={busy} onClick={() => onRemove(item.product_id)}><Trash2 size={15} /></button>
                </div>
              ) : <span className="quantity-readonly">× {item.quantity}</span>}
            </div>
          );
        })}
      </div>
      <div className="order-totals">
        <div><span>Subtotal</span><span>{formatMoney(order.subtotal)}</span></div>
        {Number(order.discount) > 0 && <div><span>Discount</span><span>− {formatMoney(order.discount)}</span></div>}
        <div className="grand-total"><strong>Total</strong><strong>{formatMoney(order.total)}</strong></div>
      </div>
      {editable && (
        <div className="order-actions">
          {onConfirm && <Button onClick={onConfirm} disabled={busy}>Confirm this order</Button>}
          {onCancel && <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel order</Button>}
        </div>
      )}
      {order.status === "confirmed" && <p className="confirmed-note">Order confirmed. Your shop has received it.</p>}
    </section>
  );
}
