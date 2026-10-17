import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, AudioLines, CheckCircle2, MicOff, PackageCheck, Send, ShieldCheck, ShoppingBasket, Sparkles, Volume2 } from "lucide-react";
import { api } from "../lib/api-client";
import type { Order, ProductOption, WorkflowResponse } from "../lib/api-types";
import { formatMoney, packLabel } from "../lib/format";
import { useRemoteData } from "../hooks/use-remote-data";
import { OrderSummary } from "../components/order-summary";
import { Button, EmptyState, ErrorPanel, LoadingPanel } from "../components/ui";

interface ConversationLine {
  kind: "customer" | "assistant";
  text: string;
}

const sessionStorageKey = "dukaanvoice-session";
const sessionId = (() => {
  const saved = localStorage.getItem(sessionStorageKey);
  if (saved) return saved;
  const id = `customer-${crypto.randomUUID()}`;
  localStorage.setItem(sessionStorageKey, id);
  return id;
})();

export function CustomerOrderPage() {
  const { data: products, loading: productsLoading, error: productsError, reload } = useRemoteData(api.products);
  const [transcript, setTranscript] = useState("");
  const [conversation, setConversation] = useState<ConversationLine[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [candidates, setCandidates] = useState<ProductOption[]>([]);
  const [clarification, setClarification] = useState<string | null>(null);
  const [clarificationText, setClarificationText] = useState("");
  const [quantityText, setQuantityText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const transcriptRef = useRef<HTMLTextAreaElement>(null);
  const productList = products ?? [];
  const confirmed = order?.status === "confirmed";
  const applyWorkflowResponse = (result: WorkflowResponse) => {
    if (result.transcript) setTranscript(result.transcript);
    if (result.order) setOrder(result.order);
    setCandidates(result.candidates);
    setClarification(result.clarification_question);
    if (result.status === "needs_clarification" && result.clarification_question) {
      setConversation((items) => [...items, { kind: "assistant", text: result.clarification_question! }]);
    } else if (result.order && result.status === "awaiting_confirmation") {
      setConversation((items) => [...items, { kind: "assistant", text: "I’ve put together your order. Please review each item and confirm when it looks right." }]);
      setNotice("Order summary ready for your review");
    }
  };

  const submitOrder = async () => {
    const clean = transcript.trim();
    if (clean.length < 3 || busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    setOrder(null);
    setCandidates([]);
    setClarification(null);
    setConversation((items) => [...items, { kind: "customer", text: clean }]);
    try {
      const result = await api.createTextOrder({
        session_id: sessionId,
        transcript: clean,
        language: localStorage.getItem("dukaanvoice-language") || "English",
      });
      applyWorkflowResponse(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "We couldn't process this order.");
    } finally {
      setBusy(false);
    }
  };

  const answerClarification = async (selection?: ProductOption) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    const clarificationValue = clarificationText.trim();
    try {
      const result = await api.clarifyOrder({
        session_id: sessionId,
        ...(selection ? { selected_product_id: selection.product_id } : {}),
        ...(selection && quantityText ? { quantity: Number(quantityText) } : {}),
        ...(!selection && clarificationValue ? { clarification_text: clarificationValue } : {}),
      });
      if (selection) setConversation((items) => [...items, { kind: "customer", text: `Choose ${selection.brand} ${selection.name}` }]);
      else if (clarificationValue) setConversation((items) => [...items, { kind: "customer", text: clarificationValue }]);
      setClarificationText("");
      setQuantityText("");
      applyWorkflowResponse(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "We couldn't use that clarification.");
    } finally {
      setBusy(false);
    }
  };

  const confirmOrder = async () => {
    if (!order || busy || !window.confirm("Confirm this order? Current stock will be updated.")) return;
    setBusy(true);
    setError(null);
    try {
      const confirmedOrder = await api.confirmOrder(order.order_id);
      setOrder(confirmedOrder);
      setNotice("Your order is confirmed");
      setConversation((items) => [...items, { kind: "assistant", text: "Order confirmed. Your shop has received it." }]);
      await reload();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Order could not be confirmed.");
    } finally {
      setBusy(false);
    }
  };

  const cancelOrder = async () => {
    if (!order || busy || !window.confirm("Cancel this order? This cannot be undone.")) return;
    setBusy(true);
    setError(null);
    try {
      const cancelled = await api.cancelOrder(order.order_id);
      setOrder(cancelled);
      setNotice("Order cancelled");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Order could not be cancelled.");
    } finally {
      setBusy(false);
    }
  };

  const changeQuantity = async (productId: string, quantity: number) => {
    if (!order) return;
    setBusy(true);
    setError(null);
    try {
      setOrder(await api.updateQuantity(order.order_id, productId, quantity));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Quantity could not be updated.");
    } finally {
      setBusy(false);
    }
  };

  const removeItem = async (productId: string) => {
    if (!order || !window.confirm("Remove this item from the order?")) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.removeItem(order.order_id, productId);
      setOrder(updated);
      if (!updated.items.length) setNotice("The order is now empty and cancelled.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Item could not be removed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-wrap customer-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow"><span className="eyebrow-dot" /> YOUR LOCAL SHOP, A LITTLE CLOSER</span>
          <h1>Good things,<br /><em>on your list.</em></h1>
          <p>Say what you need, just like you’d tell your shopkeeper. We’ll make sure the order is right before it goes through.</p>
          <div className="hero-assurance"><ShieldCheck size={17} /> Nothing is ordered until you say so.</div>
          <div className="hero-actions">
            <button className="button button-primary" onClick={() => transcriptRef.current?.focus()}>
              Start my list <ArrowDown size={16} />
            </button>
            <Link className="button button-secondary" to="/products">Explore the shop <ArrowRight size={16} /></Link>
          </div>
        </div>
        <div className="voice-panel voice-unavailable">
          <div className="voice-panel-top">
            <span className="voice-spark"><AudioLines size={17} /></span>
            <span>VOICE ORDERING</span>
          </div>
          <div className="mic-stage">
            <div className="mic-orbit orbit-one" /><div className="mic-orbit orbit-two" />
            <div className="mic-button mic-disabled" aria-hidden="true"><MicOff size={27} /></div>
          </div>
          <strong>Voice is coming soon</strong>
          <span className="voice-hint">Your microphone won’t be activated</span>
          <p className="voice-warning">Type your list below for now. We’ll only enable recording when voice upload is supported.</p>
        </div>
        <div className="hero-decoration" aria-hidden="true"><span>नमस्ते</span><span>from your kirana</span></div>
      </section>

      {productsError && <ErrorPanel message={productsError} retry={() => void reload()} />}

      <div className="order-workspace">
        <section className="order-compose">
          <div className="section-title"><div><span className="eyebrow">START WITH WHAT YOU NEED</span><h2>Tell us your list</h2></div><span className="step-label">01 <i /> 02 <i /> 03</span></div>
          <label className="field-label" htmlFor="order-transcript">Your grocery list</label>
          <textarea ref={transcriptRef} id="order-transcript" className="order-input" rows={3} value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="For example: 2 packets of Amul milk and one kilo of sugar…" maxLength={5000} />
          <div className="compose-footer">
            <span>{transcript.length}/5000 · You can edit this before sending</span>
            <Button onClick={() => void submitOrder()} disabled={busy || transcript.trim().length < 3}>
              {busy ? "Working…" : "Make my order"} <Send size={16} />
            </Button>
          </div>
          {error && <ErrorPanel message={error} />}
          {notice && <p className="inline-success"><CheckCircle2 size={17} />{notice}</p>}

          {conversation.length > 0 && (
            <div className="conversation" aria-live="polite">
              <div className="conversation-heading"><Sparkles size={16} /><span>YOUR ORDER, TAKING SHAPE</span></div>
              {conversation.map((line, index) => (
                <div key={`${index}-${line.kind}`} className={`conversation-line ${line.kind}`}>
                  <span className="conversation-avatar">{line.kind === "customer" ? "You" : "d."}</span>
                  <p>{line.text}</p>
                </div>
              ))}
            </div>
          )}

          {clarification && (
            <div className="clarification-card">
              <div className="clarification-title"><span className="clarification-mark">?</span><div><span className="eyebrow">ONE QUICK QUESTION</span><h3>{clarification}</h3></div></div>
              {candidates.length > 0 && (
                <div className="candidate-list">
                  <label className="candidate-quantity">
                    Quantity in packs
                    <input type="number" min="1" max="999" value={quantityText} onChange={(event) => setQuantityText(event.target.value)} placeholder="Use what you said" />
                  </label>
                  {candidates.map((candidate) => (
                    <button className="candidate-option" key={candidate.product_id} disabled={busy} onClick={() => void answerClarification(candidate)}>
                      <span><strong>{candidate.name}</strong><small>{candidate.brand} · {packLabel(candidate.pack_size, candidate.unit)} · {candidate.available_stock} in stock</small></span>
                      <span className="candidate-price">{formatMoney(candidate.price)} <ArrowRight size={16} /></span>
                    </button>
                  ))}
                </div>
              )}
              <form className="clarification-form" onSubmit={(event) => { event.preventDefault(); void answerClarification(); }}>
                <input value={clarificationText} onChange={(event) => setClarificationText(event.target.value)} placeholder="Or tell us what you meant…" aria-label="Clarification response" />
                <Button size="small" type="submit" disabled={busy || !clarificationText.trim()}>Send</Button>
              </form>
            </div>
          )}
        </section>

        <aside className="order-aside">
          {productsLoading ? <LoadingPanel label="Getting the shop’s list…" /> : productsError ? (
            <EmptyState icon={<ShoppingBasket size={24} />} title="The catalogue is offline" description="Reconnect using the notice above, then your shop’s list will appear here." />
          ) : !products?.length ? (
            <EmptyState icon={<ShoppingBasket size={24} />} title="The shelves are quiet" description="There are no products in the catalogue yet." />
          ) : order ? (
            <div className="summary-wrap">
              {confirmed && <div className="confirmation-banner"><CheckCircle2 size={20} /><div><strong>Order is confirmed</strong><small>Reference {order.order_id}</small></div></div>}
              <OrderSummary order={order} products={productList} onQuantity={(id, quantity) => void changeQuantity(id, quantity)} onRemove={(id) => void removeItem(id)} onConfirm={() => void confirmOrder()} onCancel={() => void cancelOrder()} busy={busy} />
              {confirmed && <div className="audio-unavailable"><Volume2 size={16} /><span>Spoken confirmation is not available because the speech service is not connected.</span></div>}
            </div>
          ) : (
            <div className="order-aside-intro">
              <span className="aside-counter">A GOOD LITTLE HABIT</span>
              <h3>Easy ordering.<br /><em>Nothing guessed.</em></h3>
              <p>We look up the real catalogue and check every item with you before confirming.</p>
              <div className="assurance-list">
                <div><span className="assurance-check">✓</span><span>Real shop prices</span></div>
                <div><span className="assurance-check">✓</span><span>Stock checked before confirmation</span></div>
                <div><span className="assurance-check">✓</span><span>You stay in control</span></div>
              </div>
              <div className="aside-note"><PackageCheck size={18} /><span>{productList.length} products currently in this shop’s catalogue</span></div>
            </div>
          )}
        </aside>
      </div>

      <section className="popular-products">
        <div className="section-title"><div><span className="eyebrow">FROM THE SHOP’S CATALOGUE</span><h2>A few neighbourhood favourites</h2></div><Link to="/products" className="text-link">Browse everything <ArrowRight size={16} /></Link></div>
        {productsLoading ? <LoadingPanel label="Loading catalogue…" /> : productsError ? null : (
          <div className="favourites-grid">
            {productList.slice(0, 4).map((product, index) => (
              <div className="favourite-card" key={product.product_id}>
                <span className={`favourite-number favourite-${index + 1}`}>0{index + 1}</span>
                <div><span className="favourite-brand">{product.brand}</span><strong>{product.canonical_name}</strong><small>{packLabel(product.pack_size, product.unit)}</small></div>
                <span className="favourite-price">{formatMoney(product.price)}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
