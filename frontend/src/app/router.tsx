import { createBrowserRouter, Navigate } from "react-router-dom";
import { Layout } from "../components/layout";
import { Dashboard } from "../features/dashboard";
import { Projects, ProjectDetail } from "../features/projects";
import { Updates, UpdateDetail } from "../features/updates";
import { Documents, DocumentDetail } from "../features/documents";
import { People, PersonDetail, Settings } from "../features/people";
import { Assistant } from "../features/assistant";
import { Search, Notifications } from "../features/search";
import { Administration } from "../features/administration";
import { Empty } from "../components/ui";
export const router = createBrowserRouter([
  {
    element: <Layout />,
    errorElement: (
      <Empty title="Unable to load this page">
        Refresh the page and try again.
      </Empty>
    ),
    children: [
      { path: "/", element: <Dashboard /> },
      { path: "/login", element: <Navigate to="/" replace /> },
      { path: "/projects", element: <Projects /> },
      { path: "/projects/:id", element: <ProjectDetail /> },
      { path: "/work", element: <Updates /> },
      { path: "/work/:id", element: <UpdateDetail /> },
      { path: "/documents", element: <Documents /> },
      { path: "/documents/:id", element: <DocumentDetail /> },
      { path: "/people", element: <People /> },
      { path: "/people/:id", element: <PersonDetail /> },
      { path: "/settings", element: <Settings /> },
      { path: "/assistant", element: <Assistant /> },
      { path: "/assistant/:id", element: <Assistant /> },
      { path: "/search", element: <Search /> },
      { path: "/notifications", element: <Notifications /> },
      { path: "/admin/users", element: <Administration view="users" /> },
      { path: "/admin/access", element: <Administration view="access" /> },
      { path: "/admin/audit", element: <Administration view="audit" /> },
      {
        path: "*",
        element: (
          <Empty title="Page unavailable">
            This page is unavailable or you no longer have access.
          </Empty>
        ),
      },
    ],
  },
]);
