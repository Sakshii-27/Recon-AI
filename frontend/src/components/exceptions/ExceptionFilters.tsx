import { Search, Filter, ArrowUpDown } from "lucide-react";

export function ExceptionFilters({
  searchTerm,
  setSearchTerm,
  typeFilter,
  setTypeFilter,
  availableTypes,
  statusFilter,
  setStatusFilter,
  availableStatuses,
  sortOrder,
  setSortOrder,
}: any) {
  return (
    <div className="p-4 border-b border-slate-200 bg-white flex flex-col space-y-3 shadow-sm z-10">
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search exceptions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-400 bg-slate-50"
        />
      </div>

      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Filter className="w-3 h-3 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full pl-7 pr-6 py-1.5 text-xs border border-slate-200 rounded-md appearance-none focus:outline-none focus:border-slate-400 bg-white"
          >
            <option value="All">All Types</option>
            {availableTypes.map((t: string) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="relative flex-1">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md appearance-none focus:outline-none focus:border-slate-400 bg-white"
          >
            <option value="All">All Statuses</option>
            {availableStatuses.map((s: string) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="relative flex-1">
          <ArrowUpDown className="w-3 h-3 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="w-full pl-7 pr-2 py-1.5 text-xs border border-slate-200 rounded-md appearance-none focus:outline-none focus:border-slate-400 bg-white"
          >
            <option value="Highest Amount">Highest Amount</option>
            <option value="Lowest Amount">Lowest Amount</option>
          </select>
        </div>
      </div>
    </div>
  );
}
