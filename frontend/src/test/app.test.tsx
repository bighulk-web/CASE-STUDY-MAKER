import { render, screen } from "@testing-library/react";
import { HashRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { ThemeProvider } from "@/components/theme-provider";

describe("App shell", () => {
  it("renders sidebar navigation", () => {
    render(
      <ThemeProvider>
        <HashRouter>
          <App />
        </HashRouter>
      </ThemeProvider>,
    );
    expect(screen.getByText("Case Study Maker")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Presentation Builder/i }),
    ).toBeInTheDocument();
    // Dashboard is the default route -> its page header renders.
    expect(
      screen.getByRole("heading", { name: "Dashboard" }),
    ).toBeInTheDocument();
  });
});
