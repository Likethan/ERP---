export default function WorkspaceLoading() {
  return (
    <div className="space-y-6 animate-pulse p-2">
      <div className="h-8 w-64 rounded-lg bg-slate-200" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="h-28 rounded-xl bg-slate-200" />
        <div className="h-28 rounded-xl bg-slate-200" />
        <div className="h-28 rounded-xl bg-slate-200" />
        <div className="h-28 rounded-xl bg-slate-200" />
      </div>
      <div className="h-80 rounded-xl bg-slate-200" />
    </div>
  );
}
