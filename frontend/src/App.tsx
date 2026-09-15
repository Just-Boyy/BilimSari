import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";

import { AppRouter } from "./router";
import { initTelegramTheme } from "./lib/telegram";

export function App() {
  useEffect(() => {
    initTelegramTheme();
  }, []);

  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
}
