import { createBrowserRouter } from "react-router";
import ConversationOverview from "./components/ConversationOverview";
import ConversationDetail from "./components/ConversationDetail";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: ConversationOverview,
  },
  {
    path: "/conversation/:id",
    Component: ConversationDetail,
  },
]);
