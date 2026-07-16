import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { HashRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { ThemeProvider } from "@/components/theme-provider";

function renderApp() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <ThemeProvider>
      <QueryClientProvider client={qc}>
        <HashRouter>
          <App />
        </HashRouter>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

describe("App shell", () => {
  it("renders sidebar navigation", () => {
    renderApp();
    expect(screen.getByText("Case Study Maker")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Presentation Builder/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });
});
