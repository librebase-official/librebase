import { FeedbackWall } from "./FeedbackWall";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Feedback · Librebase",
  robots: { index: false, follow: false },
};

export default function FeedbackDemoPage() {
  return <FeedbackWall />;
}
