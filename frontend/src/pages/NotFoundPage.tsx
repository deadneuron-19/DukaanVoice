import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export function NotFoundPage() {
  return <div className="not-found"><span className="eyebrow">A WRONG TURN, THAT’S ALL</span><h1>That page isn’t<br /><em>on these shelves.</em></h1><Link to="/" className="button button-primary"><ArrowLeft size={16} /> Back to your list</Link></div>;
}
