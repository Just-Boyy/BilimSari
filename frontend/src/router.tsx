import { Navigate, Route, Routes } from "react-router-dom";

import { Home } from "./pages/Home";
import { Onboarding } from "./pages/Onboarding";
import { Sections } from "./pages/Sections";
import { Splash } from "./pages/Splash";
import { Subjects } from "./pages/Subjects";
import { TopicPage } from "./pages/TopicPage";
import { Topics } from "./pages/Topics";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Splash />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/home" element={<Home />} />
      <Route path="/subjects" element={<Subjects />} />
      <Route path="/subjects/:subjectId/sections" element={<Sections />} />
      <Route path="/sections/:sectionId/topics" element={<Topics />} />
      <Route path="/topics/:topicId" element={<TopicPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
