import { useMemo, useState } from "react";
import { Boxes, Search, SlidersHorizontal } from "lucide-react";
import { useRemoteData } from "../hooks/use-remote-data";
import { api } from "../lib/api-client";
import type { Product } from "../lib/api-types";
import { formatMoney, packLabel } from "../lib/format";
import { Button, EmptyState, ErrorPanel } from "../components/ui";

function ProductTile({ product }: { product: Product }) {
  const available = product.available_stock > 0;
  return (
    <article className="catalog-product">
      <div className={`catalog-art art-${product.category.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
        <span className="catalog-art-letter">{product.canonical_name.slice(0, 1)}</span>
        <span className="catalog-category">{product.category}</span>
      </div>
      <div className="catalog-info">
        <span className="catalog-brand">{product.brand}</span>
        <h3>{product.canonical_name}</h3>
        <p>{packLabel(product.pack_size, product.unit)}</p>
        <div className="catalog-bottom">
          <strong>{formatMoney(product.price)}</strong>
          <span className={`stock-label ${available ? "in-stock" : "out-stock"}`}>
            <i />{available ? `${product.available_stock} in stock` : "Out of stock"}
          </span>
        </div>
      </div>
    </article>
  );
}

export function ProductsPage() {
  const { data, loading, error, reload } = useRemoteData(api.products);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All shelves");
  const [availability, setAvailability] = useState("all");
  const products = data ?? [];
  const categories = useMemo(() => ["All shelves", ...new Set(products.map((product) => product.category))], [products]);
  const filtered = products.filter((product) => {
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || [product.canonical_name, product.brand, product.category].some((value) => value.toLowerCase().includes(query));
    const matchesCategory = category === "All shelves" || product.category === category;
    const matchesAvailability = availability === "all" || (availability === "available" ? product.available_stock > 0 : product.available_stock <= 0);
    return matchesSearch && matchesCategory && matchesAvailability;
  });

  return (
    <div className="page-wrap interior-page">
      <div className="page-heading">
        <div><span className="eyebrow">STRAIGHT FROM THE SHOP</span><h1>The shelves</h1><p>Real prices and stock, fetched from your neighbourhood shop.</p></div>
        <div className="heading-stamp"><Boxes size={19} /><span>{loading ? "…" : error ? "Unavailable" : `${products.length} products`}</span></div>
      </div>
      <div className="catalog-tools">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find something good…" aria-label="Search products" /></label>
        <label className="filter-field"><SlidersHorizontal size={16} /><select value={category} onChange={(event) => setCategory(event.target.value)} aria-label="Filter by category">{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
        <select className="availability-select" value={availability} onChange={(event) => setAvailability(event.target.value)} aria-label="Filter by availability">
          <option value="all">Any availability</option><option value="available">In stock</option><option value="unavailable">Out of stock</option>
        </select>
      </div>
      {loading ? <div className="catalog-grid">{Array.from({ length: 8 }, (_, index) => <div className="skeleton-card" key={index}><div /><span /><i /></div>)}</div>
        : error ? <ErrorPanel message={error} retry={() => void reload()} />
        : filtered.length ? <div className="catalog-grid">{filtered.map((product) => <ProductTile key={product.product_id} product={product} />)}</div>
        : <EmptyState icon={<Search size={24} />} title="Nothing on this shelf" description={products.length ? "Try another name, category or availability filter." : "The shop has no active catalogue items yet."} action={search || category !== "All shelves" || availability !== "all" ? <Button variant="secondary" onClick={() => { setSearch(""); setCategory("All shelves"); setAvailability("all"); }}>Clear filters</Button> : undefined} />}
    </div>
  );
}
