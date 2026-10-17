import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProductsPage } from "../src/pages/ProductsPage";
import { api } from "../src/lib/api-client";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("catalogue browsing", () => {
  it("filters products returned by the API using the search field", async () => {
    vi.spyOn(api, "products").mockResolvedValue([
      {
        product_id: "rice-1",
        canonical_name: "Basmati Rice",
        brand: "Shree",
        category: "Rice",
        pack_size: 5,
        unit: "kg",
        price: "245.00",
        available_stock: 18,
        alternative_product_ids: [],
        is_active: true,
      },
      {
        product_id: "milk-1",
        canonical_name: "Toned Milk",
        brand: "Amul",
        category: "Milk",
        pack_size: 1,
        unit: "litre",
        price: "62.00",
        available_stock: 30,
        alternative_product_ids: [],
        is_active: true,
      },
    ]);

    render(<ProductsPage />);
    expect(await screen.findByRole("heading", { name: "Basmati Rice" })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Search products" }), {
      target: { value: "amul" },
    });

    expect(screen.getByRole("heading", { name: "Toned Milk" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Basmati Rice" })).not.toBeInTheDocument();
  });
});
