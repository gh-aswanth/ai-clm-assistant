<template>
  <!-- Port of graph-ui/src/GraphViewer.tsx (layout + behavior); embedded height for contract page -->
  <div
    v-if="loading"
    class="flex min-h-[45vh] flex-1 items-center justify-center bg-[var(--clm-bg-page)]"
  >
    <div class="flex flex-col items-center gap-4">
      <div class="h-10 w-10 animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 dark:border-[var(--clm-border)] dark:border-t-[var(--clm-brand)]" />
      <p class="text-sm font-medium text-gray-500 dark:text-[var(--clm-text-muted)]">Loading graph...</p>
    </div>
  </div>

  <div
    v-else-if="!graphData"
    class="flex min-h-[45vh] flex-1 flex-col items-center justify-center gap-3 bg-[var(--clm-bg-page)] px-4 py-8"
  >
    <div
      v-if="loadError?.kind === 'not_found'"
      class="max-w-md rounded-xl border border-amber-200/90 bg-amber-50/95 px-6 py-5 text-center shadow-sm dark:border-amber-800/45 dark:bg-amber-950/40"
    >
      <p class="text-[15px] font-semibold text-amber-950 dark:text-amber-100">No knowledge graph for this version yet</p>
      <p class="mt-2 text-[13px] leading-relaxed text-amber-900/90 dark:text-amber-200/90">
        Build your document graph to explore entities and relationships for the selected version. After the document is chunked, use
        <strong class="font-semibold">Build knowledge graph</strong> in the toolbar above.
      </p>
    </div>
    <div
      v-else
      class="max-w-md rounded-xl border border-red-200 bg-red-50 px-6 py-4 dark:border-red-900/50 dark:bg-red-950/40"
    >
      <p class="font-medium text-red-700 dark:text-red-400">
        {{ loadError?.message || 'Failed to load graph data' }}
      </p>
    </div>
  </div>

  <div
    v-else
    ref="layoutRef"
    :class="{ dark: props.forceDark }"
    class="flex h-full min-h-0 flex-1 flex-col bg-[var(--clm-bg-page)] lg:flex-row"
  >
    <!-- Sidebar: Discover / Selection — modern tabbed explorer -->
    <aside
      class="relative flex w-full shrink-0 flex-col overflow-hidden border-b border-[var(--clm-border)] bg-[var(--clm-bg-surface)] transition-[width,border-color] duration-200 ease-out lg:max-w-[min(100%,52%)] lg:border-b-0 lg:border-r"
      :style="sidebarAsideStyle"
      :aria-hidden="sidebarIsCollapsed ? 'true' : 'false'"
    >
      <div
        v-show="!sidebarIsCollapsed"
        class="pointer-events-none absolute bottom-0 left-0 top-0 w-px bg-gradient-to-b from-blue-400/45 via-zinc-200/50 to-transparent dark:from-transparent dark:via-[var(--clm-border)] dark:to-transparent"
        aria-hidden="true"
      />

      <header
        class="sticky top-0 z-30 shrink-0 border-b border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-4 pb-3 pt-3 backdrop-blur-sm"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h1 class="text-lg font-bold tracking-tight text-zinc-900 dark:text-[var(--clm-text)]">Knowledge graph</h1>
            <p class="mt-0.5 text-[11px] leading-relaxed text-zinc-500 dark:text-[var(--clm-text-muted)]">
              Discover nodes, then review connections in one place.
            </p>
          </div>
          <div class="grid shrink-0 grid-cols-2 gap-1.5">
            <div
              class="rounded-lg bg-zinc-900 px-2 py-1 text-center text-[10px] font-bold tabular-nums text-white dark:bg-[var(--clm-brand)] dark:text-white"
            >
              {{ graphData.nodes.length }} nodes
            </div>
            <div
              class="rounded-lg border border-zinc-200 bg-zinc-50 px-2 py-1 text-center text-[10px] font-bold tabular-nums text-zinc-700 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)]"
            >
              {{ graphData.links.length }} links
            </div>
          </div>
        </div>
        <div
          class="mt-3 flex rounded-full bg-zinc-100 p-1 dark:bg-[var(--clm-bg-overlay)]"
          role="tablist"
          aria-label="Panel sections"
        >
          <button
            type="button"
            role="tab"
            class="relative flex-1 rounded-full py-2 text-center text-xs font-semibold transition"
            :class="
              leftSidebarTab === 'discover'
                ? 'bg-white text-zinc-900 shadow-sm dark:bg-[var(--clm-brand-soft)] dark:text-[var(--clm-text)] dark:shadow-sm dark:ring-1 dark:ring-[var(--clm-brand)] dark:ring-opacity-30'
                : 'text-zinc-500 hover:text-zinc-800 dark:text-[var(--clm-text-muted)] dark:hover:text-[var(--clm-text)]'
            "
            :aria-selected="leftSidebarTab === 'discover'"
            @click="leftSidebarTab = 'discover'"
          >
            Discover
          </button>
          <button
            type="button"
            role="tab"
            class="relative flex-1 rounded-full py-2 text-center text-xs font-semibold transition"
            :class="
              leftSidebarTab === 'selection'
                ? 'bg-white text-zinc-900 shadow-sm dark:bg-[var(--clm-brand-soft)] dark:text-[var(--clm-text)] dark:shadow-sm dark:ring-1 dark:ring-[var(--clm-brand)] dark:ring-opacity-30'
                : 'text-zinc-500 hover:text-zinc-800 dark:text-[var(--clm-text-muted)] dark:hover:text-[var(--clm-text)]'
            "
            :aria-selected="leftSidebarTab === 'selection'"
            @click="leftSidebarTab = 'selection'"
          >
            Selection
            <span
              v-if="selectedNode || selectedLink"
              class="absolute right-3 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-[var(--clm-brand)]"
              aria-hidden="true"
            />
          </button>
        </div>
      </header>

      <div id="clm-graph-explorer-panel" class="min-h-0 flex-1 overflow-auto bg-[var(--clm-bg-surface)]">
        <!-- DISCOVER: search, tips, type shortcuts -->
        <div v-show="leftSidebarTab === 'discover'" class="space-y-4 px-4 pb-6 pt-4">
          <div
            v-if="!sidebarTipsDismissed"
            class="relative overflow-hidden rounded-2xl border border-blue-200/80 bg-gradient-to-br from-blue-50 to-white p-3.5 pr-14 dark:border-[var(--clm-brand-strong)] dark:border-opacity-40 dark:from-[var(--clm-brand-soft)] dark:to-[var(--clm-bg-surface)]"
          >
            <button
              type="button"
              class="absolute right-2 top-2 rounded-lg px-2 py-1 text-[10px] font-semibold text-blue-700 transition hover:bg-blue-100/80 dark:text-[var(--clm-brand-soft-text)] dark:hover:bg-[var(--clm-bg-overlay)]"
              @click="dismissSidebarTips"
            >
              Got it
            </button>
            <p class="text-[10px] font-bold uppercase tracking-wider text-blue-700 dark:text-[var(--clm-brand-soft-text)]">How this works</p>
            <ul class="mt-2 space-y-1.5 text-[11px] leading-snug text-zinc-600 dark:text-[var(--clm-text-muted)]">
              <li class="flex gap-2">
                <span class="font-semibold text-blue-600 dark:text-[var(--clm-brand)]">1.</span>
                <span>Search or tap a <strong>type</strong> chip to narrow nodes.</span>
              </li>
              <li class="flex gap-2">
                <span class="font-semibold text-blue-600 dark:text-[var(--clm-brand)]">2.</span>
                <span>Pick a result — the <strong>Selection</strong> tab opens with full detail.</span>
              </li>
              <li class="flex gap-2">
                <span class="font-semibold text-blue-600 dark:text-[var(--clm-brand)]">3.</span>
                <span>Pan and zoom the canvas; use <strong>Fit</strong> anytime to reset the view.</span>
              </li>
            </ul>
          </div>

          <section class="rounded-2xl border border-zinc-200/90 bg-white p-4 shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]">
            <h2 class="text-xs font-bold text-zinc-900 dark:text-[var(--clm-text)]">Canvas &amp; search</h2>
            <p class="mt-0.5 text-[10px] text-zinc-500 dark:text-[var(--clm-text-muted)]">Jump around the graph without losing context.</p>
            <button
              type="button"
              class="mt-3 w-full rounded-xl bg-zinc-900 py-2.5 text-xs font-bold text-white shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-[var(--clm-brand)] dark:text-white dark:hover:bg-[var(--clm-brand-strong)]"
              :disabled="!canvasReady"
              @click="fitView"
            >
              Fit entire graph
            </button>
            <div class="relative mt-4">
              <div class="mb-1.5 flex items-center justify-between gap-2">
                <label class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:text-[var(--clm-text-muted)]" for="clm-graph-search-input">Find a node</label>
                <button
                  v-if="searchQuery.length > 0"
                  type="button"
                  class="text-[10px] font-semibold text-blue-600 hover:underline dark:text-[var(--clm-brand)]"
                  @click="clearGraphSearch"
                >
                  Clear
                </button>
              </div>
              <input
                id="clm-graph-search-input"
                v-model.trim="searchQuery"
                type="search"
                placeholder="Id, label, or type…"
                class="w-full rounded-xl border-0 bg-zinc-50 px-3 py-2.5 text-xs text-zinc-900 ring-1 ring-zinc-200/90 transition placeholder:text-zinc-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-400/35 dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:ring-[var(--clm-border)] dark:placeholder:text-[var(--clm-text-muted)] dark:focus:bg-[var(--clm-bg-surface)] dark:focus:ring-[var(--clm-brand)] dark:focus:ring-opacity-40"
                autocomplete="off"
                @focus="searchOpen = true"
              />
              <div
                v-if="searchOpen && searchQuery.length > 0"
                class="absolute left-0 right-0 top-[calc(100%+0.35rem)] z-20 max-h-60 overflow-auto rounded-xl border border-zinc-200 bg-white p-2 shadow-xl ring-1 ring-black/5 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:ring-white/10"
              >
                <p class="mb-1.5 px-1 text-[10px] font-semibold text-zinc-500 dark:text-[var(--clm-text-muted)]">
                  {{ searchMatchTotal }} match{{ searchMatchTotal === 1 ? '' : 'es'
                  }}<span v-if="searchMatchTotal > 25"> · showing first 25</span>
                </p>
                <button
                  v-for="n in filteredSearchNodes"
                  :key="`search-${n.id}`"
                  type="button"
                  class="w-full rounded-lg px-2 py-1.5 text-left transition hover:bg-blue-50 dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                  @click="onSearchSelect(n)"
                >
                  <div class="truncate text-[11px] font-semibold text-zinc-900 dark:text-[var(--clm-text)]">{{ n.id }}</div>
                  <div class="text-[10px] text-zinc-500 dark:text-[var(--clm-text-muted)]">{{ n.type }}</div>
                </button>
                <p
                  v-if="filteredSearchNodes.length === 0"
                  class="px-2 py-3 text-center text-[11px] text-zinc-500 dark:text-[var(--clm-text-muted)]"
                >
                  No nodes match. Try another word or a type chip below.
                </p>
              </div>
            </div>
            <div class="mt-3 grid grid-cols-2 gap-2">
              <button
                type="button"
                class="flex items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 py-2.5 text-[10px] font-bold text-zinc-800 transition hover:border-zinc-300 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                :disabled="!graphData?.nodes?.length"
                @click="jumpToRandomNode"
              >
                <span aria-hidden="true">↻</span> Random
              </button>
              <button
                type="button"
                class="flex items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 py-2.5 text-[10px] font-bold text-zinc-800 transition hover:border-zinc-300 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                :disabled="!graphData?.nodes?.length || !topConnectedNodes.length"
                @click="jumpToTopConnectedNode"
              >
                <span aria-hidden="true">◎</span> Top hub
              </button>
            </div>
          </section>

          <section
            v-if="graphNodeTypes.length"
            class="rounded-2xl border border-zinc-200/90 bg-white p-4 shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]"
          >
            <h2 class="text-xs font-bold text-zinc-900 dark:text-[var(--clm-text)]">Browse by type</h2>
            <p class="mt-0.5 text-[10px] text-zinc-500 dark:text-[var(--clm-text-muted)]">Tap to search; open a result to inspect it.</p>
            <div class="mt-3 flex flex-wrap gap-1.5">
              <button
                v-for="t in graphNodeTypes"
                :key="`type-chip-${t.type}`"
                type="button"
                class="rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-left text-[10px] font-semibold text-zinc-700 transition hover:border-blue-300 hover:bg-blue-50 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:border-blue-700 dark:hover:bg-blue-950/40"
                :title="`Search ${t.type}`"
                @click="spotlightNodeType(t.type)"
              >
                {{ t.type }}
                <span class="ml-1 tabular-nums text-zinc-400 dark:text-[var(--clm-text-muted)]">{{ t.count }}</span>
              </button>
            </div>
          </section>
        </div>

        <!-- SELECTION: inspector, navigation deck, neighborhood -->
        <div v-show="leftSidebarTab === 'selection'" class="space-y-3 px-4 pb-6 pt-4">
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[10px] font-bold text-zinc-700 shadow-sm transition hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
              @click="leftSidebarTab = 'discover'"
            >
              ← Discover
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[10px] font-bold text-zinc-700 shadow-sm transition hover:bg-zinc-50 disabled:opacity-40 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
              :disabled="!canvasReady"
              @click="fitView"
            >
              Fit view
            </button>
          </div>

        <div v-if="selectedNode && nodeConnections" class="space-y-3">
          <div
            class="overflow-hidden rounded-2xl border border-gray-200/90 bg-white shadow-sm ring-1 ring-black/[0.03] dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)] dark:ring-white/[0.06]"
          >
            <div class="flex min-h-0">
              <div
                class="w-1 shrink-0 self-stretch"
                :style="{ backgroundColor: getNodeColor(selectedNode.type) }"
                aria-hidden="true"
              />
              <div class="min-w-0 flex-1 p-4">
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-[var(--clm-text-muted)]">Inspector</p>
                    <p class="mt-0.5 text-xs font-semibold text-gray-900 dark:text-[var(--clm-text)]">Selected node</p>
                  </div>
                  <button
                    type="button"
                    class="rounded-lg border border-gray-200 px-2.5 py-1 text-[10px] font-bold text-gray-600 transition hover:bg-gray-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="clearSelection"
                  >
                    Clear
                  </button>
                </div>
                <div class="mt-3 flex flex-wrap gap-1.5 rounded-xl bg-zinc-50 p-1.5 dark:bg-[var(--clm-bg-overlay)]">
                  <button
                    type="button"
                    class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                    :class="selectedNodeIsStarred ? 'bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100' : 'text-zinc-600 hover:bg-white dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'"
                    @click="toggleSelectedStarred"
                  >
                    {{ selectedNodeIsStarred ? '★ Saved' : '☆ Save' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold text-zinc-600 transition hover:bg-white dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="centerOnSelectedNode"
                  >
                    Center on map
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold text-zinc-600 transition hover:bg-white dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="copyNodeId"
                  >
                    {{ copiedNodeId ? 'Copied ✓' : 'Copy ID' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold text-zinc-600 transition hover:bg-white dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="copyNeighborhoodSnapshot"
                  >
                    Export JSON
                  </button>
                </div>
                <div class="mt-3 flex flex-wrap items-center gap-1.5">
                  <button
                    type="button"
                    class="rounded-lg border border-gray-200 bg-white px-2 py-1 text-[10px] font-semibold text-gray-700 transition hover:bg-gray-50 disabled:opacity-40 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    :disabled="!canGoToPreviousNode"
                    @click="goToPreviousVisitedNode"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    class="rounded-lg border border-gray-200 bg-white px-2 py-1 text-[10px] font-semibold text-gray-700 transition hover:bg-gray-50 disabled:opacity-40 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    :disabled="!canGoToNextNode"
                    @click="goToNextVisitedNode"
                  >
                    Next →
                  </button>
                  <span
                    class="rounded-lg bg-gray-100 px-2 py-1 text-[10px] font-medium tabular-nums text-gray-600 dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text-muted)]"
                  >
                    {{ visitedNodeCursor + 1 }} / {{ visitedNodeTrail.length }}
                  </span>
                </div>
                <div class="mt-4 flex items-start gap-3 border-t border-gray-100 pt-4 dark:border-[var(--clm-border)] dark:border-opacity-80">
                  <span
                    class="mt-1 h-3 w-3 shrink-0 rounded-full ring-2 ring-gray-200/80 dark:ring-[var(--clm-border)]"
                    :style="{
                      backgroundColor: getNodeColor(selectedNode.type),
                      boxShadow: `0 0 0 3px ${getNodeColor(selectedNode.type)}22`,
                    }"
                  />
                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-semibold text-gray-900 dark:text-[var(--clm-text)]">{{ selectedNode.type }}</div>
                    <div class="break-words font-mono text-[11px] leading-relaxed text-gray-600 dark:text-[var(--clm-text-muted)]">
                      {{ selectedNode.id }}
                    </div>
                  </div>
                </div>
                <div v-if="Object.keys(selectedNode.properties || {}).length" class="mt-3">
                  <button
                    type="button"
                    class="flex w-full items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50/80 px-3 py-2 text-left text-[10px] font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="inspectorPropertiesExpanded = !inspectorPropertiesExpanded"
                  >
                    <span>Raw properties</span>
                    <span class="text-zinc-400">{{ inspectorPropertiesExpanded ? 'Hide' : 'Show' }}</span>
                  </button>
                  <pre
                    v-show="inspectorPropertiesExpanded"
                    class="mt-2 max-h-32 overflow-auto rounded-xl border border-zinc-100 bg-white p-2.5 text-[10px] leading-relaxed text-zinc-600 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-page)] dark:text-[var(--clm-text-muted)]"
                  >{{ JSON.stringify(selectedNode.properties, null, 2) }}</pre>
                </div>
                <div
                  class="mt-3 flex divide-x divide-gray-200 rounded-xl bg-gray-50 text-center dark:divide-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)]"
                >
                  <div class="min-w-0 flex-1 py-2">
                    <p class="text-[9px] font-semibold uppercase tracking-wide text-gray-400 dark:text-[var(--clm-text-muted)]">Out</p>
                    <p class="text-sm font-bold tabular-nums text-gray-900 dark:text-[var(--clm-text)]">{{ neighborhoodStats.outgoingCount }}</p>
                  </div>
                  <div class="min-w-0 flex-1 py-2">
                    <p class="text-[9px] font-semibold uppercase tracking-wide text-gray-400 dark:text-[var(--clm-text-muted)]">In</p>
                    <p class="text-sm font-bold tabular-nums text-gray-900 dark:text-[var(--clm-text)]">{{ neighborhoodStats.incomingCount }}</p>
                  </div>
                  <div class="min-w-0 flex-1 py-2">
                    <p class="text-[9px] font-semibold uppercase tracking-wide text-gray-400 dark:text-[var(--clm-text-muted)]">Degree</p>
                    <p class="text-sm font-bold tabular-nums text-gray-900 dark:text-[var(--clm-text)]">{{ selectedNodeDegree }} / {{ maxNodeDegree }}</p>
                  </div>
                </div>
                <p class="mt-2 text-[10px] text-gray-500 dark:text-[var(--clm-text-muted)]">
                  Connectivity {{ selectedNodeConnectivityPercent }}% vs max degree in graph
                </p>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-zinc-200/90 bg-white p-3.5 shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]">
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-xs font-bold text-zinc-900 dark:text-[var(--clm-text)]">Navigation deck</h3>
              <span class="text-[10px] text-zinc-400 dark:text-[var(--clm-text-muted)]">Jump back quickly</span>
            </div>
            <div class="mt-3">
              <p class="text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:text-[var(--clm-text-muted)]">Recent</p>
              <div
                v-if="visitedNodeTrail.length <= 1"
                class="mt-1.5 rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 px-2 py-2 text-[10px] leading-snug text-zinc-500 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text-muted)]"
              >
                Open a few nodes — your trail shows up here for one-tap return.
              </div>
              <div v-else class="clm-graph-chip-scroll mt-1.5 flex gap-1 overflow-x-auto pb-1">
                <button
                  v-for="(nodeId, idx) in visitedNodeTrail.slice(-10)"
                  :key="`history-${nodeId}-${idx}`"
                  type="button"
                  class="shrink-0 rounded-lg border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-[10px] font-medium text-zinc-700 transition hover:border-blue-300 hover:bg-white dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:border-blue-700 dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                  @click="selectNodeByTrailIndex(Math.max(0, visitedNodeTrail.length - 10) + idx)"
                >
                  {{ nodeId }}
                </button>
              </div>
            </div>
            <div class="mt-3 border-t border-zinc-100 pt-3 dark:border-[var(--clm-border)] dark:border-opacity-80">
              <p class="text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:text-[var(--clm-text-muted)]">Saved</p>
              <div
                v-if="!starredNodeIds.length"
                class="mt-1.5 rounded-lg border border-dashed border-amber-200/70 bg-amber-50/40 px-2 py-2 text-[10px] leading-snug text-amber-900/80 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200/90"
              >
                Use <strong>Save</strong> on any node to pin it here for later.
              </div>
              <div v-else class="clm-graph-chip-scroll mt-1.5 flex gap-1 overflow-x-auto pb-1">
                <button
                  v-for="nodeId in starredNodeIds.slice(0, 10)"
                  :key="`fav-${nodeId}`"
                  type="button"
                  class="shrink-0 rounded-lg border border-amber-200/90 bg-amber-50 px-2.5 py-1 text-[10px] font-semibold text-amber-900 transition hover:bg-amber-100 dark:border-amber-800/50 dark:bg-amber-950/50 dark:text-amber-100 dark:hover:bg-amber-950/70"
                  @click="selectNodeById(nodeId)"
                >
                  ★ {{ nodeId }}
                </button>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-gray-200/90 bg-white p-4 shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]">
            <div class="flex items-end justify-between gap-2 border-b border-gray-100 pb-3 dark:border-[var(--clm-border)] dark:border-opacity-80">
              <div>
                <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-[var(--clm-text-muted)]">Connections</p>
                <p class="mt-0.5 text-xs font-semibold text-gray-900 dark:text-[var(--clm-text)]">Neighborhood</p>
              </div>
              <span
                class="rounded-lg bg-slate-100 px-2 py-1 text-[10px] font-bold tabular-nums text-slate-700 dark:bg-slate-700/50 dark:text-slate-200"
              >
                {{ neighborhoodStats.totalEdges }} edges
              </span>
            </div>
            <div class="mt-4 grid grid-cols-2 gap-3 text-[10px]">
              <div>
                <div class="font-semibold text-zinc-600 dark:text-[var(--clm-text-muted)]">Relation types</div>
                <p class="mt-0.5 text-[9px] text-zinc-400 dark:text-[var(--clm-text-muted)]">Tap to filter the list below</p>
                <div class="mb-1 mt-1.5 flex flex-wrap gap-1">
                  <span
                    v-if="topRelations.length === 0"
                    class="rounded-md border border-dashed border-zinc-200 px-2 py-0.5 text-zinc-400 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)]"
                  >
                    None
                  </span>
                  <button
                    v-for="r in topRelations"
                    :key="`rel-${r.rawType}`"
                    type="button"
                    class="rounded-md bg-zinc-100 px-2 py-0.5 text-left font-medium text-zinc-700 transition hover:bg-blue-100 hover:text-blue-900 dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-brand-soft)] dark:hover:text-[var(--clm-brand-soft-text)]"
                    :title="`Filter by ${r.rawType}`"
                    @click="neighborhoodSearchQuery = r.rawType"
                  >
                    {{ r.label }} ({{ r.count }})
                  </button>
                </div>
              </div>
              <div class="text-right">
                <p class="font-semibold text-zinc-600 dark:text-[var(--clm-text-muted)]">Mix</p>
                <p
                  class="mt-1.5 inline-block rounded-lg border border-zinc-100 bg-zinc-50 px-2.5 py-1.5 text-[11px] font-medium text-zinc-600 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text-muted)]"
                >
                  {{ neighborhoodStats.uniqueRelationCount }} distinct type(s)
                </p>
              </div>
            </div>
            <div class="mt-4">
              <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:text-[var(--clm-text-muted)]" for="clm-neighbor-filter">Filter relationships</label>
              <input
                id="clm-neighbor-filter"
                v-model.trim="neighborhoodSearchQuery"
                type="search"
                placeholder="Match relation, node, or type…"
                class="w-full rounded-xl border-0 bg-zinc-50 px-3 py-2.5 text-[11px] text-zinc-900 ring-1 ring-zinc-200/90 transition placeholder:text-zinc-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-400/35 dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:ring-[var(--clm-border)] dark:focus:bg-[var(--clm-bg-surface)] dark:focus:ring-[var(--clm-brand)] dark:focus:ring-opacity-40"
              />
            </div>
            <button
              type="button"
              class="mt-3 flex w-full items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50/80 px-3 py-2 text-left text-[10px] font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)] dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
              :aria-expanded="neighborhoodAdvancedOpen"
              @click="neighborhoodAdvancedOpen = !neighborhoodAdvancedOpen"
            >
              <span>List options</span>
              <span class="font-normal text-zinc-400">{{ neighborhoodAdvancedOpen ? 'Hide' : 'Sort & direction' }}</span>
            </button>
            <div v-show="neighborhoodAdvancedOpen" class="mt-2 space-y-3">
              <div class="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodSortMode === 'relation' ? 'bg-zinc-800 text-white dark:bg-[var(--clm-brand-strong)] dark:text-white' : 'border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'"
                  @click="neighborhoodSortMode = 'relation'"
                >
                  Sort · relation
                </button>
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodSortMode === 'node' ? 'bg-zinc-800 text-white dark:bg-[var(--clm-brand-strong)] dark:text-white' : 'border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'"
                  @click="neighborhoodSortMode = 'node'"
                >
                  Sort · node
                </button>
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodSortMode === 'direction' ? 'bg-zinc-800 text-white dark:bg-[var(--clm-brand-strong)] dark:text-white' : 'border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'"
                  @click="neighborhoodSortMode = 'direction'"
                >
                  Sort · direction
                </button>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodDirection === 'all' ? 'bg-zinc-800 text-white dark:bg-[var(--clm-brand-strong)] dark:text-white' : 'border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'"
                  @click="neighborhoodDirection = 'all'"
                >
                  All ({{ neighborhoodStats.totalEdges }})
                </button>
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodDirection === 'outgoing' ? 'bg-emerald-600 text-white dark:bg-emerald-700' : 'border border-emerald-200 text-emerald-800 hover:bg-emerald-50 dark:border-emerald-900/50 dark:text-emerald-300 dark:hover:bg-emerald-950/30'"
                  @click="neighborhoodDirection = 'outgoing'"
                >
                  Out ({{ neighborhoodStats.outgoingCount }})
                </button>
                <button
                  type="button"
                  class="rounded-lg px-2.5 py-1.5 text-[10px] font-bold transition"
                  :class="neighborhoodDirection === 'incoming' ? 'bg-indigo-600 text-white dark:bg-indigo-700' : 'border border-indigo-200 text-indigo-800 hover:bg-indigo-50 dark:border-indigo-900/50 dark:text-indigo-300 dark:hover:bg-indigo-950/30'"
                  @click="neighborhoodDirection = 'incoming'"
                >
                  In ({{ neighborhoodStats.incomingCount }})
                </button>
              </div>
            </div>
            <div class="mt-5 space-y-3 text-[11px]">
              <p v-if="neighborhoodRows.length === 0" class="text-center rounded-lg border border-dashed border-gray-200 py-4 text-gray-500 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)]">
                No {{ neighborhoodDirection === 'all' ? 'connected' : neighborhoodDirection }} relationships
              </p>
              <template v-else>
                <p class="text-[10px] text-gray-500 dark:text-[var(--clm-text-muted)]">
                  {{ neighborhoodRows.length }} relationship{{ neighborhoodRows.length === 1 ? '' : 's' }}
                  <span v-if="neighborhoodRows.length > 8"> — scroll the list to see all</span>
                </p>
                <div
                  class="clm-neighborhood-list-scroll max-h-[min(52vh,520px)] space-y-2 overflow-y-auto overscroll-contain rounded-xl border border-gray-100 bg-slate-50/50 p-1.5 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)]"
                >
                  <button
                    v-for="neighbor in neighborhoodRows"
                    :key="`neighbor-row-${neighbor._rowKey}`"
                    type="button"
                    class="w-full rounded-xl border border-gray-100/90 bg-white px-3 py-3 text-left shadow-sm transition hover:border-slate-200 hover:bg-slate-50/80 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)] dark:hover:border-gray-600 dark:hover:bg-[var(--clm-bg-overlay)]"
                    @click="selectNodeById(neighbor.other.id)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div class="min-w-0 flex items-center gap-2.5">
                        <span
                          class="h-2.5 w-2.5 shrink-0 rounded-full"
                          :class="neighbor.direction === 'outgoing' ? 'bg-emerald-500' : 'bg-indigo-500'"
                        />
                        <div class="min-w-0">
                          <div class="truncate font-semibold text-gray-900 dark:text-[var(--clm-text)]">{{ neighbor.other.id }}</div>
                          <p class="truncate text-[10px] text-gray-500 dark:text-[var(--clm-text-muted)]">{{ neighbor.other.type }}</p>
                        </div>
                      </div>
                      <div class="shrink-0 pl-1 text-[10px] text-right leading-snug">
                        <div class="font-mono font-medium text-gray-800 dark:text-[var(--clm-text)]">
                          {{ String(neighbor.relType || 'related').replace(/_/g, ' ') }}
                        </div>
                        <div class="text-gray-400">{{ neighbor.direction === 'outgoing' ? '→ Outbound' : '← Inbound' }}</div>
                      </div>
                    </div>
                  </button>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div
          v-else-if="selectedLink"
          class="overflow-hidden rounded-2xl border border-gray-200/90 bg-white shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]"
        >
          <div class="flex">
            <div class="w-1 shrink-0 self-stretch bg-slate-500 dark:bg-slate-400" aria-hidden="true" />
            <div class="min-w-0 flex-1 p-4">
              <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-[var(--clm-text-muted)]">Edge inspector</p>
              <p class="mt-1 text-xs font-semibold text-gray-900 dark:text-[var(--clm-text)]">Relationship</p>
              <div
                class="mt-3 rounded-xl bg-slate-50 px-3 py-2 font-mono text-xs font-semibold text-slate-800 dark:bg-[var(--clm-bg-overlay)] dark:text-slate-200"
              >
                {{ String(selectedLink.type || '').replace(/_/g, ' ') || '—' }}
              </div>
              <div class="mt-4 space-y-2.5 text-[12px] text-zinc-600 dark:text-[var(--clm-text-muted)]">
                <div class="flex flex-wrap items-start gap-2">
                  <span class="shrink-0 font-medium text-zinc-400">→</span>
                  <span class="min-w-0 flex-1 break-all">{{ nodeIdOf(selectedLink.source) }}</span>
                  <button
                    type="button"
                    class="shrink-0 rounded-lg border border-zinc-200 px-2 py-0.5 text-[10px] font-bold text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="selectNodeById(nodeIdOf(selectedLink.source))"
                  >
                    Open
                  </button>
                </div>
                <div class="flex flex-wrap items-start gap-2">
                  <span class="shrink-0 font-medium text-zinc-400">←</span>
                  <span class="min-w-0 flex-1 break-all">{{ nodeIdOf(selectedLink.target) }}</span>
                  <button
                    type="button"
                    class="shrink-0 rounded-lg border border-zinc-200 px-2 py-0.5 text-[10px] font-bold text-zinc-600 hover:bg-zinc-50 dark:border-[var(--clm-border)] dark:text-[var(--clm-text-muted)] dark:hover:bg-[var(--clm-bg-surface-elevated)]"
                    @click="selectNodeById(nodeIdOf(selectedLink.target))"
                  >
                    Open
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          v-else
          class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-300/90 bg-gradient-to-b from-white to-zinc-50/80 px-5 py-12 text-center dark:border-[var(--clm-border)] dark:from-zinc-900/40 dark:to-zinc-950/60"
        >
          <div
            class="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-xl text-blue-500 dark:bg-[var(--clm-brand-soft)] dark:text-[var(--clm-brand)]"
            aria-hidden="true"
          >
            ◎
          </div>
          <p class="text-sm font-semibold text-zinc-800 dark:text-[var(--clm-text)]">Your inspector is empty</p>
          <p class="mt-2 max-w-[16rem] text-xs leading-relaxed text-zinc-500 dark:text-[var(--clm-text-muted)]">
            Select something on the graph, or go to <strong>Discover</strong> and search for a node — we will jump you here automatically.
          </p>
          <button
            type="button"
            class="mt-4 rounded-full bg-zinc-900 px-4 py-2 text-xs font-bold text-white transition hover:bg-zinc-800 dark:bg-[var(--clm-brand)] dark:text-white dark:hover:bg-[var(--clm-brand-strong)]"
            @click="leftSidebarTab = 'discover'"
          >
            Open Discover
          </button>
        </div>
        </div>
      </div>
    </aside>

    <!-- Drag to widen or narrow the explorer vs. canvas (desktop). -->
    <div
      v-show="isWideLayout && !sidebarCollapsed"
      class="hidden shrink-0 cursor-col-resize select-none lg:block"
      role="separator"
      aria-orientation="vertical"
      :aria-valuenow="sidebarWidthPx"
      tabindex="0"
      title="Drag to resize panel"
      @pointerdown="onSplitPointerDown"
    >
      <div
        class="mx-auto h-full w-1 rounded-full bg-gray-200 transition-colors hover:bg-blue-400 dark:bg-[var(--clm-border)] dark:hover:bg-[var(--clm-brand)]"
        :class="{ 'bg-blue-500 dark:bg-[var(--clm-brand)]': splitDragging }"
      />
    </div>

    <!-- lg:min-h-0 lets the canvas fill the row; min height avoids a collapsed graph on small viewports. -->
    <main
      class="relative min-h-[min(40vh,360px)] w-full min-w-0 flex-1 self-stretch border-t border-[var(--clm-border)] bg-[var(--clm-bg-page)] lg:min-h-0 lg:border-l lg:border-t-0"
    >
      <button
        v-if="isWideLayout"
        type="button"
        class="absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center gap-1.5 rounded-full border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-3 py-2 text-[11px] font-bold text-zinc-700 shadow-lg transition hover:bg-[var(--clm-bg-surface-elevated)] dark:text-[var(--clm-text)]"
        :title="sidebarIsCollapsed ? 'Show Knowledge graph explorer' : 'Hide explorer — maximize canvas'"
        :aria-expanded="!sidebarCollapsed"
        aria-controls="clm-graph-explorer-panel"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        <svg v-if="sidebarIsCollapsed" class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
        <svg v-else class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
        {{ sidebarIsCollapsed ? 'Explorer' : 'Hide' }}
      </button>
      <GraphUiForceCanvas
        ref="canvasRef"
        class="absolute inset-0 h-full w-full"
        :graph-payload="graphData"
        :highlight-node-ids="highlightNodeIdList"
        :highlight-link-keys="highlightLinkKeyList"
        :force-dark="props.forceDark"
        @node-click="onNodeClick"
        @link-click="onLinkClick"
        @background-click="onBackgroundClick"
        @ready="canvasReady = true"
      />
    </main>
  </div>
</template>

<script setup>
/**
 * Vue port of graph-ui GraphViewer + App wiring.
 * Data: fetch(graph_data.json) with Vite base URL, else bundled src/data/graph_data.json
 */
import { ref, shallowRef, computed, watch, onMounted, onUnmounted, markRaw, nextTick } from 'vue'
import GraphUiForceCanvas from './GraphUiForceCanvas.vue'
import { parseGraphData, getNodeColor } from '../../utils/graphData.js'
import { graphDataPublicUrl } from '../../utils/graphDataSource.js'
import bundledGraphChunks from '../../data/graph_data.json'

const props = defineProps({
  dataUrl: { type: String, default: '' },
  forceDark: { type: Boolean, default: false },
})

const SIDEBAR_W_KEY = 'clm-graph-explorer-sidebar-px'
const SIDEBAR_COLLAPSED_KEY = 'clm-graph-explorer-sidebar-collapsed'
const SIDEBAR_MIN = 200
const SIDEBAR_MAX_CAP = 560

let syncWideLayout = () => {}

const layoutRef = ref(null)
const sidebarWidthPx = ref(288)
const sidebarCollapsed = ref(false)
const splitDragging = ref(false)
const isWideLayout = ref(false)

let wideMq = null

const sidebarIsCollapsed = computed(() => isWideLayout.value && sidebarCollapsed.value)

const sidebarAsideStyle = computed(() => {
  if (!isWideLayout.value) return {}
  if (sidebarCollapsed.value) {
    return {
      width: '0px',
      minWidth: '0px',
      maxWidth: '0px',
      borderRightWidth: '0',
      overflow: 'hidden',
    }
  }
  return { width: `${sidebarWidthPx.value}px` }
})

function maxSidebarForLayout() {
  const w = layoutRef.value?.getBoundingClientRect().width ?? 1200
  return Math.min(SIDEBAR_MAX_CAP, Math.floor(w * 0.52))
}

function clampSidebar(w) {
  return Math.min(maxSidebarForLayout(), Math.max(SIDEBAR_MIN, Math.round(w)))
}

function onSplitPointerDown(e) {
  if (!isWideLayout.value || e.button !== 0) return
  e.preventDefault()
  splitDragging.value = true
  try {
    e.currentTarget?.setPointerCapture?.(e.pointerId)
  } catch {
    /* ignore */
  }
  window.addEventListener('pointermove', onSplitPointerMove)
  window.addEventListener('pointerup', onSplitPointerUp)
  window.addEventListener('pointercancel', onSplitPointerUp)
}

function onSplitPointerMove(e) {
  if (!splitDragging.value || !layoutRef.value) return
  const rect = layoutRef.value.getBoundingClientRect()
  sidebarWidthPx.value = clampSidebar(e.clientX - rect.left)
}

function onSplitPointerUp() {
  if (!splitDragging.value) return
  splitDragging.value = false
  window.removeEventListener('pointermove', onSplitPointerMove)
  window.removeEventListener('pointerup', onSplitPointerUp)
  window.removeEventListener('pointercancel', onSplitPointerUp)
  try {
    localStorage.setItem(SIDEBAR_W_KEY, String(sidebarWidthPx.value))
  } catch {
    /* ignore */
  }
  bumpCanvas()
}

function groupNeighborsByRel(entries) {
  const m = new Map()
  for (const e of entries) {
    const list = m.get(e.relType) ?? []
    list.push(e)
    m.set(e.relType, list)
  }
  return [...m.entries()].sort(([a], [b]) => a.localeCompare(b))
}

const loading = ref(true)
const graphData = shallowRef(null)
/** Set when ``dataUrl`` fetch fails or graph cannot be parsed (404 → ``not_found``). */
const loadError = shallowRef(null)
const canvasRef = ref(null)
const canvasReady = ref(false)

const selectedNode = ref(null)
const selectedLink = ref(null)
const highlightNodes = ref(new Set())
const highlightLinks = ref(new Set())
const searchQuery = ref('')
const searchOpen = ref(false)
const neighborhoodDirection = ref('all')
const copiedNodeId = ref(false)
const neighborhoodSearchQuery = ref('')
const neighborhoodSortMode = ref('relation')
const visitedNodeTrail = ref([])
const visitedNodeCursor = ref(-1)
const starredNodeIds = ref([])
const STARRED_NODE_IDS_KEY = 'clm-graph-sidebar-starred-nodes'
const GRAPH_EXPLORER_TIPS_KEY = 'clm-graph-explorer-tips-dismissed'

const leftSidebarTab = ref('discover')
const sidebarTipsDismissed = ref(false)
const inspectorPropertiesExpanded = ref(false)
const neighborhoodAdvancedOpen = ref(false)

const highlightNodeIdList = computed(() => Array.from(highlightNodes.value))
const highlightLinkKeyList = computed(() => Array.from(highlightLinks.value))
const filteredSearchNodes = computed(() => findNodesByQuery(searchQuery.value).slice(0, 25))
const searchMatchTotal = computed(() => findNodesByQuery(searchQuery.value).length)

const graphNodeTypes = computed(() => {
  if (!graphData.value?.nodes?.length) return []
  const m = new Map()
  for (const n of graphData.value.nodes) {
    const t = n?.type != null && String(n.type).trim() !== '' ? String(n.type) : 'Unknown'
    m.set(t, (m.get(t) || 0) + 1)
  }
  return [...m.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 12)
    .map(([type, count]) => ({ type, count }))
})

function normalizeSearchToken(value) {
  return String(value ?? '')
    .replace(/^\s+|\s+$/g, '')
    .toLowerCase()
}

function collectNodeTokens(node) {
  const tokens = new Set()
  const push = (v) => {
    if (v == null) return
    const t = normalizeSearchToken(v)
    if (!t) return
    tokens.add(t)
  }

  push(node.id)
  push(node.type)
  push(node.label)
  if (typeof node.type === 'string' && node.type.toLowerCase() === 'entity' && node.id) {
    push(`entity:${node.id}`)
  }
  const props = node.properties
  if (props && typeof props === 'object') {
    for (const value of Object.values(props)) {
      if (typeof value === 'object' && value !== null) {
        try {
          push(JSON.stringify(value))
        } catch {
          /* ignore */
        }
      } else {
        push(value)
      }
    }
  }

  return Array.from(tokens)
}

function getNodeId(n) {
  return typeof n === 'string' ? n : n.id
}

function getLinkKey(link) {
  return `${getNodeId(link.source)}->${getNodeId(link.target)}`
}

function nodeIdOf(n) {
  return getNodeId(n)
}

const nodeConnections = computed(() => {
  if (!selectedNode.value || !graphData.value) return null
  const nodeById = new Map(graphData.value.nodes.map((n) => [n.id, n]))
  const outgoing = []
  const incoming = []

  graphData.value.links.forEach((link, edgeIndex) => {
    const sId = getNodeId(link.source)
    const tId = getNodeId(link.target)
    const src = typeof link.source === 'object' ? link.source : nodeById.get(sId)
    const tgt = typeof link.target === 'object' ? link.target : nodeById.get(tId)
    if (!src || !tgt) return

    if (sId === selectedNode.value.id) {
      outgoing.push({ other: tgt, relType: link.type, edgeIndex })
    }
    if (tId === selectedNode.value.id) {
      incoming.push({ other: src, relType: link.type, edgeIndex })
    }
  })

  const sortEntries = (a, b) =>
    String(a.relType ?? '').localeCompare(String(b.relType ?? '')) || a.other.id.localeCompare(b.other.id)
  outgoing.sort(sortEntries)
  incoming.sort(sortEntries)

  return {
    outgoing,
    incoming,
    outgoingGrouped: groupNeighborsByRel(outgoing),
    incomingGrouped: groupNeighborsByRel(incoming),
  }
})

const nodeDegreeMap = computed(() => {
  const map = new Map()
  if (!graphData.value?.nodes?.length) return map
  for (const n of graphData.value.nodes) {
    map.set(n.id, 0)
  }
  for (const link of graphData.value.links) {
    const srcId = getNodeId(link.source)
    const tgtId = getNodeId(link.target)
    if (!map.has(srcId)) map.set(srcId, 0)
    if (!map.has(tgtId)) map.set(tgtId, 0)
    map.set(srcId, (map.get(srcId) || 0) + 1)
    map.set(tgtId, (map.get(tgtId) || 0) + 1)
  }
  return map
})

const selectedNodeDegree = computed(() => {
  if (!selectedNode.value) return 0
  return nodeDegreeMap.value.get(selectedNode.value.id) || 0
})

const maxNodeDegree = computed(() => {
  let max = 0
  for (const degree of nodeDegreeMap.value.values()) {
    if (degree > max) max = degree
  }
  return max
})

const selectedNodeConnectivityPercent = computed(() => {
  if (!maxNodeDegree.value) return 0
  return Math.round((selectedNodeDegree.value / maxNodeDegree.value) * 100)
})

const topConnectedNodes = computed(() => {
  if (!nodeDegreeMap.value.size) return []
  return [...nodeDegreeMap.value.entries()]
    .map(([id, degree]) => ({ id, degree }))
    .sort((a, b) => b.degree - a.degree || a.id.localeCompare(b.id))
    .slice(0, 20)
})

const canGoToPreviousNode = computed(() => visitedNodeCursor.value > 0)
const canGoToNextNode = computed(() => visitedNodeCursor.value >= 0 && visitedNodeCursor.value < visitedNodeTrail.value.length - 1)
const selectedNodeIsStarred = computed(() => {
  if (!selectedNode.value?.id) return false
  return starredNodeIds.value.includes(String(selectedNode.value.id))
})

const neighborhoodStats = computed(() => {
  if (!nodeConnections.value) {
    return {
      outgoingCount: 0,
      incomingCount: 0,
      totalEdges: 0,
      uniqueNeighborCount: 0,
      uniqueRelationCount: 0,
    }
  }

  const relTypeSet = new Set()
  const neighbors = new Set()
  for (const e of nodeConnections.value.outgoing) {
    neighbors.add(e.other.id)
    relTypeSet.add(e.relType)
  }
  for (const e of nodeConnections.value.incoming) {
    neighbors.add(e.other.id)
    relTypeSet.add(e.relType)
  }

  return {
    outgoingCount: nodeConnections.value.outgoing.length,
    incomingCount: nodeConnections.value.incoming.length,
    totalEdges: nodeConnections.value.outgoing.length + nodeConnections.value.incoming.length,
    uniqueNeighborCount: neighbors.size,
    uniqueRelationCount: relTypeSet.size,
  }
})

const neighborhoodRows = computed(() => {
  if (!nodeConnections.value) return []
  const rows = []
  if (neighborhoodDirection.value === 'all' || neighborhoodDirection.value === 'outgoing') {
    for (const e of nodeConnections.value.outgoing) {
      rows.push({
        direction: 'outgoing',
        relType: e.relType,
        other: e.other,
        _rowKey: `o-${e.edgeIndex}`,
      })
    }
  }
  if (neighborhoodDirection.value === 'all' || neighborhoodDirection.value === 'incoming') {
    for (const e of nodeConnections.value.incoming) {
      rows.push({
        direction: 'incoming',
        relType: e.relType,
        other: e.other,
        _rowKey: `i-${e.edgeIndex}`,
      })
    }
  }

  const filtered = rows.filter((neighbor) => {
    const q = neighborhoodSearchQuery.value.trim().toLowerCase()
    if (!q) return true
    const rel = String(neighbor.relType ?? '').toLowerCase()
    return (
      rel.includes(q) ||
      neighbor.other.id.toLowerCase().includes(q) ||
      String(neighbor.other.type).toLowerCase().includes(q)
    )
  })

  filtered.sort((a, b) => {
    const relA = String(a.relType ?? '')
    const relB = String(b.relType ?? '')
    if (neighborhoodSortMode.value === 'node') {
      return a.other.id.localeCompare(b.other.id) || relA.localeCompare(relB)
    }
    if (neighborhoodSortMode.value === 'direction') {
      return a.direction.localeCompare(b.direction) || a.other.id.localeCompare(b.other.id)
    }
    return relA.localeCompare(relB) || a.other.id.localeCompare(b.other.id)
  })

  return filtered
})

const topRelations = computed(() => {
  if (!nodeConnections.value) return []
  const relMap = new Map()
  const bump = (type) => {
    const value = relMap.get(type) || 0
    relMap.set(type, value + 1)
  }
  if (neighborhoodDirection.value === 'all' || neighborhoodDirection.value === 'outgoing') {
    nodeConnections.value.outgoing.forEach((edge) => bump(edge.relType))
  }
  if (neighborhoodDirection.value === 'all' || neighborhoodDirection.value === 'incoming') {
    nodeConnections.value.incoming.forEach((edge) => bump(edge.relType))
  }

  return [...relMap.entries()]
    .map(([relType, count]) => ({
      label: String(relType ?? 'related').replace(/_/g, ' '),
      rawType: String(relType ?? 'related'),
      count,
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
    .slice(0, 6)
})

async function copyNodeId() {
  if (!selectedNode.value?.id) return
  const value = String(selectedNode.value.id)
  try {
    await navigator.clipboard.writeText(value)
  } catch {
    const el = document.createElement('textarea')
    el.value = value
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.focus()
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copiedNodeId.value = true
  window.setTimeout(() => {
    copiedNodeId.value = false
  }, 1400)
}

async function copyNeighborhoodSnapshot() {
  if (!selectedNode.value) return
  const payload = {
    node: {
      id: selectedNode.value.id,
      type: selectedNode.value.type,
      properties: selectedNode.value.properties || {},
      degree: selectedNodeDegree.value,
    },
    neighborhood: neighborhoodRows.value.map(({ _rowKey, ...rest }) => rest),
  }
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2))
  } catch {
    const el = document.createElement('textarea')
    el.value = JSON.stringify(payload, null, 2)
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.focus()
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
}

function bumpCanvas() {
  nextTick(() => canvasRef.value?.nudgeRedraw?.())
}

function openSelectionSidebar() {
  leftSidebarTab.value = 'selection'
}

function dismissSidebarTips() {
  sidebarTipsDismissed.value = true
  try {
    localStorage.setItem(GRAPH_EXPLORER_TIPS_KEY, '1')
  } catch {
    /* ignore */
  }
}

function clearGraphSearch() {
  searchQuery.value = ''
  searchOpen.value = false
}

function spotlightNodeType(typeLabel) {
  searchQuery.value = typeLabel
  searchOpen.value = true
}

function centerOnSelectedNode() {
  if (!selectedNode.value?.id) return
  canvasRef.value?.focusNodeById?.(selectedNode.value.id)
}

function onNodeClick(node, options = {}) {
  const { trackHistory = true } = options
  selectedNode.value = node
  selectedLink.value = null
  const connectedIds = new Set([node.id])
  const linkIds = new Set()
  graphData.value?.links.forEach((link) => {
    const srcId = getNodeId(link.source)
    const tgtId = getNodeId(link.target)
    if (srcId === node.id || tgtId === node.id) {
      connectedIds.add(srcId)
      connectedIds.add(tgtId)
      linkIds.add(getLinkKey(link))
    }
  })
  highlightNodes.value = connectedIds
  highlightLinks.value = linkIds
  if (trackHistory) {
    const nodeId = String(node.id)
    const trail = visitedNodeTrail.value.slice(0, visitedNodeCursor.value + 1)
    if (visitedNodeCursor.value < 0 || trail[trail.length - 1] !== nodeId) {
      trail.push(nodeId)
      if (trail.length > 100) trail.shift()
      visitedNodeTrail.value = trail
      visitedNodeCursor.value = trail.length - 1
    }
  }
  bumpCanvas()
  openSelectionSidebar()
}

function onLinkClick(link) {
  selectedNode.value = null
  selectedLink.value = link
  highlightNodes.value = new Set([getNodeId(link.source), getNodeId(link.target)])
  highlightLinks.value = new Set([getLinkKey(link)])
  bumpCanvas()
  openSelectionSidebar()
}

function onBackgroundClick() {
  selectedNode.value = null
  selectedLink.value = null
  highlightNodes.value = new Set()
  highlightLinks.value = new Set()
  bumpCanvas()
}

function clearSelection() {
  onBackgroundClick()
}

function jumpToRandomNode() {
  if (!graphData.value?.nodes?.length) return
  const n = graphData.value.nodes[Math.floor(Math.random() * graphData.value.nodes.length)]
  if (n) selectNodeById(n.id)
}

function jumpToTopConnectedNode() {
  if (!topConnectedNodes.value.length) return
  selectNodeById(topConnectedNodes.value[0].id)
}

function toggleSelectedStarred() {
  if (!selectedNode.value?.id) return
  const id = String(selectedNode.value.id)
  const exists = starredNodeIds.value.includes(id)
  if (exists) {
    starredNodeIds.value = starredNodeIds.value.filter((x) => x !== id)
  } else {
    starredNodeIds.value = [id, ...starredNodeIds.value.filter((x) => x !== id)].slice(0, 60)
  }
}

function selectNodeByTrailIndex(index) {
  const total = visitedNodeTrail.value.length
  if (total <= 0 || index < 0 || index >= total) return
  const nodeId = visitedNodeTrail.value[index]
  if (!nodeId) return
  visitedNodeCursor.value = index
  selectNodeById(nodeId, { zoomFirst: true, trackHistory: false })
}

function goToPreviousVisitedNode() {
  if (!canGoToPreviousNode.value) return
  const nextIndex = visitedNodeCursor.value - 1
  const nodeId = visitedNodeTrail.value[nextIndex]
  if (!nodeId) return
  visitedNodeCursor.value = nextIndex
  selectNodeById(nodeId, { zoomFirst: true, trackHistory: false })
}

function goToNextVisitedNode() {
  if (!canGoToNextNode.value) return
  const nextIndex = visitedNodeCursor.value + 1
  const nodeId = visitedNodeTrail.value[nextIndex]
  if (!nodeId) return
  visitedNodeCursor.value = nextIndex
  selectNodeById(nodeId, { zoomFirst: true, trackHistory: false })
}

function selectNodeById(id, options = {}) {
  const n = graphData.value?.nodes.find((x) => x.id === id)
  if (!n) return false
  const { zoomFirst = true, trackHistory = true } = options
  if (zoomFirst) {
    canvasRef.value?.focusNodeById?.(n.id)
    window.setTimeout(() => onNodeClick(n, { trackHistory }), 140)
    return true
  }
  onNodeClick(n, { trackHistory })
  canvasRef.value?.focusNodeById?.(n.id)
  return true
}

function findNodesByQuery(rawQuery) {
  const q = String(rawQuery || '').trim().toLowerCase()
  if (!q || !graphData.value?.nodes?.length) return []
  const exact = []
  const prefix = []
  const partial = []
  for (const n of graphData.value.nodes) {
    const tokens = collectNodeTokens(n)
    const exactHit = tokens.some((token) => token === q)
    const prefixHit = tokens.some((token) => token.startsWith(q))
    const partialHit = tokens.some((token) => token.includes(q))

    if (exactHit) {
      exact.push(n)
    } else if (prefixHit) {
      prefix.push(n)
    } else if (partialHit) {
      partial.push(n)
    }
  }
  return [...exact, ...prefix, ...partial]
}

function selectNodeByQuery(rawQuery, options = {}) {
  const matches = findNodesByQuery(rawQuery)
  if (!matches.length) return []
  const { populateSearch = false, zoomFirst = false } = options
  if (populateSearch) {
    searchQuery.value = String(rawQuery || '').trim()
  }
  selectNodeById(matches[0].id, { zoomFirst })
  return matches.map((n) => n.id)
}

function onSearchSelect(node) {
  searchQuery.value = node.id
  openSelectionSidebar()
  selectNodeById(node.id)
  nextTick(() => {
    searchOpen.value = false
  })
}

watch(
  () => selectedNode.value?.id,
  () => {
    neighborhoodDirection.value = 'all'
    neighborhoodSearchQuery.value = ''
    neighborhoodSortMode.value = 'relation'
    inspectorPropertiesExpanded.value = false
    neighborhoodAdvancedOpen.value = false
  }
)

function fitView() {
  canvasRef.value?.fitView?.()
}

const resolvedFetchUrl = computed(() =>
  props.dataUrl && props.dataUrl.length > 0 ? props.dataUrl : graphDataPublicUrl()
)

async function load() {
  canvasReady.value = false
  loading.value = true
  loadError.value = null
  let chunks = null
  const useCustomUrl = !!(props.dataUrl && String(props.dataUrl).trim().length > 0)

  try {
    try {
      const res = await fetch(resolvedFetchUrl.value, { cache: 'no-store' })
      if (res.ok) {
        chunks = await res.json()
      } else if (useCustomUrl) {
        loadError.value =
          res.status === 404
            ? { kind: 'not_found' }
            : {
                kind: 'failed',
                message: `Could not load graph (HTTP ${res.status}).`,
              }
        graphData.value = null
        return
      }
    } catch (e) {
      if (useCustomUrl) {
        loadError.value = { kind: 'failed', message: e?.message || 'Network error' }
        graphData.value = null
        return
      }
      console.warn('Graph fetch failed, using bundled graph_data.json:', e?.message || e)
    }

    if (!useCustomUrl && (!Array.isArray(chunks) || chunks.length === 0)) {
      chunks = bundledGraphChunks
    }

    try {
      const data = parseGraphData(chunks || [])
      if (!data.nodes.length) throw new Error('No nodes')
      graphData.value = markRaw(data)
      loadError.value = null
    } catch (e) {
      console.error('Failed to parse graph data:', e)
      graphData.value = null
      if (useCustomUrl) {
        loadError.value = loadError.value || {
          kind: 'failed',
          message: 'The graph could not be displayed. Try building the knowledge graph again.',
        }
      }
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  try {
    const v = Number(localStorage.getItem(SIDEBAR_W_KEY))
    if (Number.isFinite(v)) sidebarWidthPx.value = clampSidebar(v)
  } catch {
    /* ignore */
  }

  try {
    if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') sidebarCollapsed.value = true
  } catch {
    /* ignore */
  }

  try {
    const savedStarred = JSON.parse(localStorage.getItem(STARRED_NODE_IDS_KEY) || '[]')
    if (Array.isArray(savedStarred)) {
      starredNodeIds.value = [...new Set(savedStarred.map((id) => String(id)).filter(Boolean))]
    }
  } catch {
    /* ignore */
  }

  try {
    if (localStorage.getItem(GRAPH_EXPLORER_TIPS_KEY) === '1') sidebarTipsDismissed.value = true
  } catch {
    /* ignore */
  }

  wideMq = typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)') : null
  if (wideMq) {
    syncWideLayout = () => {
      isWideLayout.value = wideMq.matches
      if (wideMq.matches) sidebarWidthPx.value = clampSidebar(sidebarWidthPx.value)
    }
    syncWideLayout()
    wideMq.addEventListener('change', syncWideLayout)
  }

  load()
})

onUnmounted(() => {
  if (wideMq) wideMq.removeEventListener('change', syncWideLayout)
  window.removeEventListener('pointermove', onSplitPointerMove)
  window.removeEventListener('pointerup', onSplitPointerUp)
  window.removeEventListener('pointercancel', onSplitPointerUp)
})

watch(
  () => props.dataUrl,
  () => load()
)

watch(
  () => searchQuery.value,
  (q) => {
    searchOpen.value = q.trim().length > 0
  }
)

watch(
  starredNodeIds,
  (ids) => {
    try {
      localStorage.setItem(STARRED_NODE_IDS_KEY, JSON.stringify(ids))
    } catch {
      /* ignore */
    }
  },
  { deep: true }
)

watch(sidebarCollapsed, (c) => {
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, c ? '1' : '0')
  } catch {
    /* ignore */
  }
  nextTick(() => bumpCanvas())
})

defineExpose({
  selectNodeById,
  selectNodeByQuery,
  reload: load,
})
</script>

<style scoped>
.clm-neighborhood-list-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
}
.dark .clm-neighborhood-list-scroll {
  scrollbar-color: rgb(75 85 99) transparent;
}
.clm-neighborhood-list-scroll::-webkit-scrollbar {
  width: 6px;
}
.clm-neighborhood-list-scroll::-webkit-scrollbar-thumb {
  border-radius: 9999px;
  background-color: rgb(203 213 225);
}
.dark .clm-neighborhood-list-scroll::-webkit-scrollbar-thumb {
  background-color: rgb(75 85 99);
}

.clm-graph-chip-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
  -webkit-overflow-scrolling: touch;
}
.dark .clm-graph-chip-scroll {
  scrollbar-color: rgb(75 85 99) transparent;
}
.clm-graph-chip-scroll::-webkit-scrollbar {
  height: 5px;
}
.clm-graph-chip-scroll::-webkit-scrollbar-thumb {
  border-radius: 9999px;
  background-color: rgb(203 213 225);
}
.dark .clm-graph-chip-scroll::-webkit-scrollbar-thumb {
  background-color: rgb(75 85 99);
}
</style>
