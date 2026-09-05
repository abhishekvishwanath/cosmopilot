import { KnowledgeConsole } from "@/components/knowledge-console";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { KnowledgeDocument } from "@/lib/types";

export default async function KnowledgePage() {
  const { accessToken } = await requireSession();
  const documents = await apiFetch<KnowledgeDocument[]>("/knowledge/documents", accessToken);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Knowledge Base</h1>
      <KnowledgeConsole initialDocuments={documents} />
    </div>
  );
}
