import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout";
import { CustomerOrderPage } from "./pages/CustomerOrderPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OrdersPage } from "./pages/OrdersPage";
import { ProductsPage } from "./pages/ProductsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ShopkeeperPage } from "./pages/ShopkeeperPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<CustomerOrderPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="shopkeeper" element={<ShopkeeperPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
