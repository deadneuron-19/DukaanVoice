import { useMemo, useState } from "react";
import { AlertTriangle, ArrowUpRight, Boxes, ClipboardList, IndianRupee, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useRemoteData } from "../hooks/use-remote-data";
import { api } from "../lib/api-client";
import { formatDate, formatMoney, packLabel } from "../lib/format";
import { EmptyState, ErrorPanel, LoadingPanel, StatusBadge } from "../components/ui";

const LOW_STOCK_LIMIT = 5;

export function ShopkeeperPage() {
  const orders = useRemoteData(api.orders);
  const products = useRemoteData(api.products);
  const [search, setSearch] = useState("");
  const orderList = orders.data ?? [];
  const productList = products.data ?? [];
  const confirmed = orderList.filter((order) => order.status === "confirmed");
  const confirmedValue = confirmed.reduce((total, order) => total + Number(order.total), 0);
  const lowStock = productList.filter((product) => product.available_stock <= LOW_STOCK_LIMIT);
  const recent = useMemo(() => [...orderList].sort((a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime()).slice(0, 5), [orderList]);
  const filteredProducts = productList.filter((product) => [product.canonical_name, product.brand, product.category].some((value) => value.toLowerCase().includes(search.toLowerCase())));
  const error = orders.error || products.error;

  return (
    <div className="page-wrap interior-page shopkeeper-page">
      <div className="page-heading">
        <div><span className="eyebrow">THE COUNTER, AT A GLANCE</span><h1>Good morning.</h1><p>A clear view of what’s happening in your shop, from the data you’ve saved.</p></div>
        <span className="shopkeeper-label">SHOPKEEPER VIEW</span>
      </div>
      {error && <ErrorPanel message={error} retry={() => { void orders.reload(); void products.reload(); }} />}
      {(orders.loading || products.loading) ? <LoadingPanel label="Gathering shop data…" /> : (
        <>
          <div className="metric-grid">
            <article className="metric-card"><span className="metric-icon"><ClipboardList size={19} /></span><span className="metric-label">ALL RECORDED ORDERS</span><strong>{orders.error ? "—" : orderList.length}</strong><small>{orders.error ? "Order feed unavailable" : "Orders stored by the backend"}</small></article>
            <article className="metric-card"><span className="metric-icon"><Boxes size={19} /></span><span className="metric-label">CATALOGUE ITEMS</span><strong>{products.error ? "—" : productList.length}</strong><small>{products.error ? "Catalogue unavailable" : "Active products returned"}</small></article>
            <article className="metric-card metric-attention"><span className="metric-icon"><AlertTriangle size={19} /></span><span className="metric-label">LOW STOCK</span><strong>{products.error ? "—" : lowStock.length}</strong><small>At or below {LOW_STOCK_LIMIT} packs · UI threshold</small></article>
            <article className="metric-card"><span className="metric-icon"><IndianRupee size={19} /></span><span className="metric-label">CONFIRMED ORDER TOTAL</span><strong>{orders.error ? "Unavailable" : formatMoney(confirmedValue)}</strong><small>Recorded order value, not paid sales</small></article>
          </div>
          <div className="shopkeeper-columns">
            <section className="panel-section">
              <div className="panel-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Orders, lately</h2></div><Link to="/orders" className="subtle-link">All orders <ArrowUpRight size={15} /></Link></div>
              {orders.error ? <p className="data-note">Order activity is unavailable until the backend responds.</p> : recent.length ? <div className="recent-orders">{recent.map((order) => <div className="recent-order" key={order.order_id}><span className="recent-order-icon"><ClipboardList size={16} /></span><div className="recent-order-main"><strong>{order.order_id}</strong><small>{formatDate(order.created_at)} · {order.items.length} items</small></div><StatusBadge status={order.status} /><b>{formatMoney(order.total)}</b></div>)}</div> : <EmptyState icon={<ClipboardList size={22} />} title="No orders just yet" description="New customer orders will appear here when saved." /> }
            </section>
            <section className="panel-section inventory-section">
              <div className="panel-heading"><div><span className="eyebrow">WHAT’S ON THE SHELVES</span><h2>Stock watch</h2></div><span className="stock-threshold">Flagged ≤ {LOW_STOCK_LIMIT}</span></div>
              <label className="search-field inventory-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search stock…" aria-label="Search inventory" /></label>
              {products.error ? <p className="data-note">Inventory is unavailable until the backend responds.</p> : filteredProducts.length ? <div className="inventory-table-wrap"><table className="inventory-table"><thead><tr><th>Product</th><th>Pack</th><th>Price</th><th>On hand</th></tr></thead><tbody>{filteredProducts.map((product) => <tr key={product.product_id}><td><strong>{product.canonical_name}</strong><small>{product.brand}</small></td><td>{packLabel(product.pack_size, product.unit)}</td><td>{formatMoney(product.price)}</td><td><span className={product.available_stock <= LOW_STOCK_LIMIT ? "stock-count low" : "stock-count"}>{product.available_stock <= LOW_STOCK_LIMIT && <AlertTriangle size={13} />}{product.available_stock}</span></td></tr>)}</tbody></table></div> : <EmptyState icon={<Boxes size={22} />} title="No matching products" description="Try a different search." />}
            </section>
          </div>
        </>
      )}
      <p className="data-note">Figures above reflect saved API data only. Order totals are not payments or sales. Stock is updated when an order is confirmed.</p>
    </div>
  );
}
