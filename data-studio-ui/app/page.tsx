import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { FEEDBACK_ORIGIN } from "@/lib/demo";

export default async function RootPage({
  searchParams,
}: {
  searchParams: Promise<{ oauth_error?: string }>;
}) {
  const host = (await headers()).get("host") || "";
  if (host.startsWith("feedback.")) {
    redirect("/demo/feedback");
  }
  const { oauth_error: err } = await searchParams;
  if (err) {
    redirect(`${FEEDBACK_ORIGIN}/?oauth_error=${encodeURIComponent(err)}`);
  }
  redirect("/login");
}
