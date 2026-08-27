import { AuthorizeAgent } from "./AuthorizeAgent";

export default async function McpAuthorizePage({
  searchParams,
}: {
  searchParams: Promise<{ user_code?: string }>;
}) {
  const { user_code: userCode = "" } = await searchParams;
  return (
    <div className="auth-page">
      <AuthorizeAgent userCode={userCode} />
    </div>
  );
}
