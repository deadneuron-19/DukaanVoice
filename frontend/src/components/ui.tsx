import type { ButtonHTMLAttributes, PropsWithChildren, ReactNode } from "react";
import { AlertCircle, Check, LoaderCircle } from "lucide-react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "normal" | "small";
};

export function Button({
  variant = "primary",
  size = "normal",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button-${variant} ${size === "small" ? "button-small" : ""} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const label = status.replaceAll("_", " ");
  return <span className={`status status-${status.replaceAll("_", "-")}`}>{label}</span>;
}

export function LoadingPanel({ label = "Loading" }: { label?: string }) {
  return (
    <div className="loading-panel" role="status">
      <LoaderCircle className="spin" size={19} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorPanel({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="error-panel" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <div>
        <strong>Something needs attention</strong>
        <p>{message}</p>
        {retry && <Button variant="secondary" size="small" onClick={retry}>Try again</Button>}
      </div>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon" aria-hidden="true">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function Toast({
  message,
  kind = "success",
}: PropsWithChildren<{ message: string; kind?: "success" | "error" }>) {
  return (
    <div className={`toast toast-${kind}`} role="status">
      {kind === "success" ? <Check size={17} /> : <AlertCircle size={17} />}
      {message}
    </div>
  );
}
