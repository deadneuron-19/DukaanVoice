import { useMemo, useState } from "react";
import { ArrowUpRight, ClipboardList, Search } from "lucide-react";
import { useRemoteData } from "../hooks/use-remote-data";
import { api } from "../lib/api-client";
import type { Order, OrderStatus } from "../lib/api-types";
import { formatDate, formatMoney } from "../lib/format";
import { Button, EmptyState, ErrorPanel, LoadingPanel, StatusBadge } from "../components/ui";
import { OrderSummary } from "../components/order-summary";

const statuses: Array<"all" | OrderStatus> = ["all", "awaiting_confirmation", "confirmed", "cancelled", "needs_clarification", "draft"];

export function OrdersPage() {
  const { data, loading, error, reload } = useRemoteData(api.orders);
  const { data: products } = useRemoteData(api.products);
  const [status, setStatus] = useState<"all" | OrderStatus>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Order | null>(null);
  const orders = data ?? [];
  const filtered = useMemo(() => orders.filter((order) => {
    const matchesStatus = status === "all" || order.status === status;
    const matchesSearch = !search || order.order_id.toLowerCase().includes(search.toLowerCase()) || order.session_id.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  }), [orders, search, status]);

  return (
    <div className="page-wrap interior-page">
      <div className="page-heading">
        <div><span className="eyebrow">THE PAPER TRAIL</span><h1>Your orders</h1><p>Every order stays yours to review, from first draft to confirmation.</p></div>
        <div className="heading-stamp"><ClipboardList size={19} /><span>{loading ? "…" : error ? "Unavailable" : `${orders.length} orders`}</span></div>
      </div>
      <div className="orders-tools">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search order or session…" aria-label="Search orders" /></label>
        <div className="filter-pills" role="group" aria-label="Filter orders by status">
          {statuses.map((item) => <button key={item} className={status === item ? "filter-pill active" : "filter-pill"} onClick={() => setStatus(item)}>{item === "all" ? "All orders" : item.replaceAll("_", " ")}</button>)}
        </div>
      </div>
      {loading ? <LoadingPanel label="Finding your orders…" /> : error ? <ErrorPanel message={error} retry={() => void reload()} /> : filtered.length ? (
        <div className="order-history-list">
          {filtered.map((order) => (
            <button className="history-row" key={order.order_id} onClick={() => setSelected(order)}>
              <div className="history-main"><span className="history-icon"><ClipboardList size={18} /></span><div><strong>{order.order_id}</strong><small>{formatDate(order.created_at)} · {order.items.length} {order.items.length === 1 ? "item" : "items"}</small></div></div>
              <StatusBadge status={order.status} />
              <strong className="history-total">{formatMoney(order.total)}</strong>
              <ArrowUpRight size={17} className="history-arrow" />
            </button>
          ))}
        </div>
      ) : <EmptyState icon={<ClipboardList size={24} />} title={orders.length ? "No orders match" : "A fresh page"} description={orders.length ? "Try a different status or search term." : "Orders will appear here after customers send a grocery list."} action={orders.length ? <Button variant="secondary" onClick={() => { setSearch(""); setStatus("all"); }}>Clear filters</Button> : undefined} />}
      {selected && <div className="modal-backdrop" role="presentation" onClick={(event) => { if (event.target === event.currentTarget) setSelected(null); }}>
        <div className="detail-modal" role="dialog" aria-modal="true" aria-labelledby="order-detail-title">
          <button className="modal-close" onClick={() => setSelected(null)} aria-label="Close order details">×</button>
          <span className="eyebrow">ORDER DETAILS</span><h2 id="order-detail-title">{selected.order_id}</h2>
          <p className="modal-meta">{formatDate(selected.created_at)} · Session {selected.session_id}</p>
          <OrderSummary order={selected} products={products ?? []} />
        </div>
      </div>}
    </div>
  );
}
