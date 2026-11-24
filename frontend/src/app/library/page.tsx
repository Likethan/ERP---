import { redirect } from "next/navigation";

export default function LibraryPortalEntryPage() {
  redirect("/login?role=library");
}
