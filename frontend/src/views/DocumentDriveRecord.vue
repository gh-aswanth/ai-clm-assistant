<template>
  <div class="ddr-shell">

    <!-- ── Preview slide-over ──────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="preview-backdrop">
        <div v-if="previewFile" class="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-[2px]" @click="closePreview"></div>
      </Transition>
      <Transition name="preview-slide">
        <div v-if="previewFile"
          class="fixed top-0 right-0 z-[9999] h-full flex flex-col bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 transition-[width] duration-300 ease-in-out"
          :style="{ width: totalPanelWidth + 'px', maxWidth: '100vw' }">
          <div class="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-sky-400/30 active:bg-sky-400/50 transition z-10" @mousedown="startResize"></div>
          <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 bg-white dark:bg-gray-900">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="fileIconClass(previewFile.content_type)">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
              </div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-[var(--clm-text)] truncate">{{ previewFile.original_filename }}</p>
                <p class="text-[10px] text-gray-400 mt-0.5">{{ formatBytes(previewFile.size_bytes) }} &middot; {{ fileExtLabel(previewFile.original_filename) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <button @click="navigatePreview(-1)" :disabled="!canNavigatePrev" class="ddr-icon-btn" title="Previous"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg></button>
              <button @click="navigatePreview(1)" :disabled="!canNavigateNext" class="ddr-icon-btn" title="Next"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg></button>
              <div class="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-1"></div>
              <a :href="`/api/document-drive-files/${previewFile.id}/download`" target="_blank" class="ddr-icon-btn" title="Download"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg></a>
              <button @click="startRename(previewFile)" class="ddr-icon-btn" title="Rename"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>
              <div class="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-1"></div>
              <button @click="toggleChunksDrawer" class="ddr-chunks-toggle" :class="chunksDrawerOpen ? 'ddr-chunks-toggle-active' : ''" title="Document Chunks">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                <span class="text-[11px] font-semibold">Chunks</span>
                <span v-if="fileChunks.length" class="ddr-chunks-badge">{{ fileChunks.length }}</span>
              </button>
              <button @click="closePreview" class="ddr-icon-btn" title="Close"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
            </div>
          </div>
          <div class="px-5 py-2 border-b border-gray-100 dark:border-gray-800 flex items-center gap-5 text-[11px] text-gray-400 flex-shrink-0">
            <span>Type: <strong class="text-[var(--clm-text)]">{{ fileExtLabel(previewFile.original_filename) }}</strong></span>
            <span>Size: <strong class="text-[var(--clm-text)]">{{ formatBytes(previewFile.size_bytes) }}</strong></span>
            <span v-if="previewFile.content_type">MIME: <strong class="text-[var(--clm-text)]">{{ previewFile.content_type }}</strong></span>
          </div>
          <!-- ── Split content: preview + chunks drawer ──────────────── -->
          <div class="ddr-split-container flex-1 overflow-hidden">
            <!-- Document preview (always visible) -->
            <div class="ddr-preview-pane">
              <!-- PDF.js renderer -->
              <div v-if="isPdfPreview" ref="pdfScrollContainer" class="ddr-pdf-scroll">
                <div ref="pdfPagesContainer" class="ddr-pdf-pages"></div>
              </div>
              <!-- iframe for DOCX HTML / images / text -->
              <iframe v-else-if="previewUrl" ref="previewIframe" :src="previewUrl" class="w-full h-full border-0 bg-white" @load="onIframeLoad"></iframe>
              <div v-else class="flex flex-col items-center justify-center h-full text-center p-8">
                <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                  <svg class="w-8 h-8 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                </div>
                <p class="text-sm font-medium text-gray-400">Preview not available</p>
                <a :href="`/api/document-drive-files/${previewFile.id}/download`" target="_blank" class="mt-4 ddr-btn-primary text-xs">Download Instead</a>
              </div>
            </div>

            <!-- Chunks drawer -->
            <Transition name="drawer-slide">
              <aside v-if="chunksDrawerOpen" class="ddr-chunks-drawer" :style="{ width: chunksDrawerWidth + 'px' }">
                <!-- Drawer resize handle -->
                <div class="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-sky-400/40 active:bg-sky-400/60 transition z-10" @mousedown="startDrawerResize"></div>

                <!-- Drawer header -->
                <div class="ddr-drawer-header ddr-drawer-header-stacked">
                  <div class="flex items-start justify-between gap-2 w-full">
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-7 h-7 rounded-lg bg-[var(--clm-primary)]/10 flex items-center justify-center flex-shrink-0">
                        <svg class="w-3.5 h-3.5 text-[var(--clm-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                      </div>
                      <div class="min-w-0">
                        <p class="text-[12px] font-bold text-[var(--clm-text)]">Document Chunks</p>
                        <p class="text-[10px] text-gray-400">{{ fileChunks.length }} section{{ fileChunks.length !== 1 ? 's' : '' }} from drive indexing</p>
                      </div>
                    </div>
                    <button @click="chunksDrawerOpen = false" class="ddr-icon-btn !p-1.5 flex-shrink-0" title="Close drawer">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                  </div>
                </div>

                <!-- Drawer body -->
                <div class="ddr-drawer-body">
                  <!-- Loading -->
                  <div v-if="chunksLoading" class="flex flex-col items-center justify-center py-16 gap-3">
                    <svg class="animate-spin h-5 w-5 text-[var(--clm-primary)]" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                    <p class="text-xs text-gray-400 font-medium">Extracting chunks...</p>
                  </div>

                  <!-- Empty state -->
                  <div v-else-if="!fileChunks.length" class="flex flex-col items-center justify-center py-16 px-5 text-center">
                    <div class="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-3">
                      <svg class="w-6 h-6 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                    </div>
                    <p class="text-[12px] font-semibold text-gray-400">No chunks yet</p>
                    <p class="text-[11px] text-gray-300 dark:text-gray-600 mt-1 max-w-[200px]">Chunking may still be processing or this file type isn't supported.</p>
                  </div>

                  <!-- Chunk list -->
                  <div v-else class="ddr-drawer-list">
                    <div v-for="chunk in fileChunks" :key="chunk.id"
                      class="ddr-chunk-card" :class="activeChunkId === chunk.id ? 'ddr-chunk-active' : ''">
                      <div class="ddr-chunk-header">
                        <button @click="toggleChunkExpand(chunk.id)" class="flex items-center gap-2 min-w-0 flex-1">
                          <span class="ddr-chunk-index">#{{ chunk.chunk_index + 1 }}</span>
                          <p class="text-[11px] text-[var(--clm-text)] truncate leading-snug">{{ chunk.content.substring(0, 80) }}{{ chunk.content.length > 80 ? '...' : '' }}</p>
                        </button>
                        <div class="flex items-center gap-0.5 flex-shrink-0">
                          <button
                            @click="scrollToChunkInPreview(chunk)"
                            class="ddr-eye-btn"
                            :class="activeChunkId === chunk.id ? 'ddr-eye-btn-active' : ''"
                            title="Locate in preview"
                          >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                          </button>
                          <button @click="toggleChunkExpand(chunk.id)" class="ddr-expand-toggle">
                            <svg class="w-3.5 h-3.5 transition-transform duration-200" :class="isChunkExpanded(chunk.id) ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/></svg>
                          </button>
                        </div>
                      </div>
                      <Transition name="chunk-expand">
                        <div v-if="isChunkExpanded(chunk.id)" class="ddr-chunk-body">
                          <pre class="ddr-chunk-text">{{ chunk.content }}</pre>
                          <div class="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-gray-800">
                            <span class="text-[10px] text-gray-400 tabular-nums">{{ chunk.content.length }} chars</span>
                            <button @click="copyChunk(chunk.content)" class="ddr-copy-btn">
                              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                              Copy
                            </button>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
              </aside>
            </Transition>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Rename modal ──────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="renameTarget" class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="renameTarget = null">
          <div class="ddr-card p-6 w-full max-w-md space-y-4 shadow-2xl animate-modal-in">
            <h3 class="text-base font-bold text-[var(--clm-text)]">Rename File</h3>
            <input v-model="renameValue" type="text" class="ddr-input" @keyup.enter="confirmRename" />
            <div class="flex justify-end gap-2 pt-1">
              <button @click="renameTarget = null" class="ddr-btn-ghost text-sm">Cancel</button>
              <button @click="confirmRename" class="ddr-btn-primary text-sm">Save</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Page header ───────────────────────────────────────────────── -->
    <header class="ddr-header">
      <div class="flex items-center gap-2 text-[13px]">
        <router-link to="/document-drive" class="text-gray-400 hover:text-[var(--clm-primary)] transition font-medium">Drives</router-link>
        <svg class="w-3.5 h-3.5 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
        <span class="font-bold text-[var(--clm-text)] truncate">{{ drive?.name || '...' }}</span>
      </div>
      <div class="flex items-center gap-6 text-[12px] text-gray-400 tabular-nums">
        <span><strong class="text-[var(--clm-text)] font-semibold">{{ folders.length }}</strong> folder{{ folders.length !== 1 ? 's' : '' }}</span>
        <span><strong class="text-[var(--clm-text)] font-semibold">{{ totalFiles }}</strong> file{{ totalFiles !== 1 ? 's' : '' }}</span>
        <span class="font-semibold text-[var(--clm-text)]">{{ formatBytes(totalSize) }}</span>
      </div>
    </header>

    <!-- Drive background-task activity banner -->
    <Transition name="ddr-bg-task-banner">
      <div v-if="driveBgTasks.length" class="flex flex-col gap-2 mb-4">
        <div
          v-for="task in driveBgTasks"
          :key="task.id"
          class="flex items-center gap-3 rounded-xl border px-4 py-2.5 text-sm font-medium shadow-sm"
          :class="task.status === 'running'
            ? 'border-blue-300/50 bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300'
            : task.status === 'done'
              ? 'border-emerald-300/50 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
              : 'border-red-300/50 bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300'"
        >
          <span v-if="task.status === 'running'" class="shrink-0">
            <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </span>
          <span v-else-if="task.status === 'done'" class="shrink-0">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
          </span>
          <span v-else class="shrink-0">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
          </span>
          <span class="truncate">
            <template v-if="task.status === 'running'">Indexing <strong>{{ task.filename }}</strong>…</template>
            <template v-else-if="task.status === 'done'">Indexing complete: <strong>{{ task.filename }}</strong></template>
            <template v-else>Indexing failed: <strong>{{ task.filename }}</strong></template>
          </span>
        </div>
      </div>
    </Transition>

    <!-- ── Main layout ───────────────────────────────────────────────── -->
    <div class="ddr-layout">

      <!-- ── Sidebar ─────────────────────────────────────────────────── -->
      <aside class="ddr-sidebar">
        <div class="ddr-sidebar-section">
          <div class="flex items-center gap-2">
            <input v-model="folderDraftName" type="text" placeholder="New folder..." @keyup.enter="createFolder"
              class="ddr-input flex-1 !py-2" />
            <button @click="createFolder" :disabled="folderCreating || !folderDraftName.trim()"
              class="ddr-btn-primary !p-2 flex-shrink-0 !rounded-lg">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
            </button>
          </div>
        </div>

        <nav v-if="folders.length" class="ddr-folder-nav">
          <!-- Root drop zone for moving folders to top level -->
          <div v-if="draggedFolder && draggedFolder.parent_id"
            class="ddr-root-drop-zone"
            :class="dragOverFolderId === -1 ? 'ddr-root-drop-active' : ''"
            @dragover.prevent="dragOverFolderId = -1"
            @dragleave="dragOverFolderId === -1 && (dragOverFolderId = null)"
            @drop.prevent="moveToRoot">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
            <span class="text-[11px] font-medium">Move to root</span>
          </div>
          <TransitionGroup name="folder-item">
            <template v-for="item in flatFolderList" :key="item.folder.id">
              <div
                class="ddr-folder-item"
                :class="[
                  activeFolderId === item.folder.id ? 'ddr-folder-active' : 'ddr-folder-idle',
                  dragOverFolderId === item.folder.id ? 'ddr-folder-drop-target' : ''
                ]"
                :style="{ paddingLeft: (12 + item.depth * 18) + 'px' }"
                draggable="true"
                @dragstart.stop="onFolderDragStart($event, item.folder)"
                @dragend="onFolderDragEnd"
                @dragover.prevent="onFolderDragOver(item.folder)"
                @dragleave="onFolderDragLeave(item.folder)"
                @drop.prevent="onFolderDrop($event, item.folder)"
              >
                <button v-if="item.hasChildren" @click.stop="toggleExpand(item.folder.id)" class="ddr-expand-btn">
                  <svg class="w-3 h-3 transition-transform duration-200" :class="item.isExpanded ? 'rotate-90' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
                </button>
                <span v-else class="w-[16px] flex-shrink-0"></span>
                <div class="flex-1 min-w-0 flex items-center gap-2 cursor-pointer" @click="openFolder(item.folder)">
                  <svg v-if="activeFolderId === item.folder.id" class="w-[16px] h-[16px] text-[var(--clm-primary)] flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/></svg>
                  <svg v-else class="w-[16px] h-[16px] text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                  <span class="text-[12px] font-medium truncate">{{ item.folder.name }}</span>
                </div>
                <span class="ddr-badge">{{ totalFolderFileCount(item.folder.id) }}</span>
                <div class="ddr-folder-actions">
                  <button @click.stop="startSubfolderCreate(item.folder.id)" class="ddr-folder-action-btn" title="New subfolder">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
                  </button>
                  <button @click.stop="deleteFolder(item.folder)" class="ddr-folder-action-btn ddr-folder-action-danger" title="Delete folder">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </div>
              </div>
              <!-- Inline subfolder creation input -->
              <div v-if="subfolderParentId === item.folder.id && item.isExpanded"
                class="ddr-subfolder-input" :style="{ paddingLeft: (12 + (item.depth + 1) * 18) + 'px' }">
                <input v-model="subfolderDraftName" type="text" placeholder="Subfolder name..."
                  class="ddr-input !py-1.5 !text-[12px] flex-1" @keyup.enter="createSubfolder" @keyup.escape="cancelSubfolderCreate" ref="subfolderInput" autofocus />
                <button @click="createSubfolder" :disabled="!subfolderDraftName.trim()" class="ddr-btn-primary !p-1.5 !rounded-md flex-shrink-0">
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                </button>
                <button @click="cancelSubfolderCreate" class="ddr-icon-btn !p-1.5 flex-shrink-0">
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
            </template>
          </TransitionGroup>
        </nav>
        <div v-else class="ddr-sidebar-empty">
          <svg class="w-8 h-8 text-gray-200 dark:text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
          <p class="text-xs text-gray-400 mt-2">Create your first folder</p>
        </div>

        <!-- Folder settings (collapsible) -->
        <details v-if="activeFolder" class="ddr-sidebar-section group/det">
          <summary class="ddr-details-summary">
            <svg class="w-3.5 h-3.5 transition-transform group-open/det:rotate-90 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            Folder Settings
          </summary>
          <div class="mt-3 space-y-2.5">
            <input v-model="activeFolder.name" type="text" class="ddr-input" placeholder="Folder name" />
            <input v-model="activeFolder.description" type="text" class="ddr-input" placeholder="Description..." />
            <button @click="saveActiveFolder" :disabled="savingFolder"
              class="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold disabled:opacity-40 transition-all duration-200">
              {{ savingFolder ? 'Saving...' : 'Save changes' }}
            </button>
          </div>
        </details>
      </aside>

      <!-- ── Main content ────────────────────────────────────────────── -->
      <main v-if="activeFolder" class="ddr-main"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <!-- Breadcrumbs -->
        <div v-if="breadcrumbs.length > 1" class="ddr-breadcrumbs">
          <template v-for="(bc, idx) in breadcrumbs" :key="bc.id">
            <button @click="openFolder(bc)" class="ddr-breadcrumb-item" :class="idx === breadcrumbs.length - 1 ? 'ddr-breadcrumb-current' : ''">
              <svg v-if="idx === 0" class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
              {{ bc.name }}
            </button>
            <svg v-if="idx < breadcrumbs.length - 1" class="w-3 h-3 text-gray-300 dark:text-gray-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
          </template>
        </div>

        <!-- Toolbar -->
        <div class="ddr-toolbar">
          <div class="ddr-toolbar-left">
            <div class="ddr-search">
              <svg class="ddr-search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
              <input v-model="searchQuery" type="text" placeholder="Search files..." class="ddr-search-input" />
            </div>
            <select v-model="typeFilter" class="ddr-select">
              <option value="">All types</option>
              <option value="pdf">PDF</option>
              <option value="image">Images</option>
              <option value="word">Word</option>
              <option value="excel">Excel</option>
              <option value="other">Other</option>
            </select>
            <select v-model="sortBy" class="ddr-select">
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="name">A-Z</option>
              <option value="name_desc">Z-A</option>
              <option value="size_desc">Largest</option>
              <option value="size_asc">Smallest</option>
            </select>
            <div class="ddr-view-toggle">
              <button @click="viewMode = 'grid'" class="ddr-view-btn" :class="viewMode === 'grid' ? 'ddr-view-active' : ''">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              </button>
              <button @click="viewMode = 'list'" class="ddr-view-btn" :class="viewMode === 'list' ? 'ddr-view-active' : ''">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/></svg>
              </button>
            </div>
          </div>
          <div class="ddr-toolbar-right">
            <Transition name="fade-scale">
              <button v-if="selectedFileIds.size" @click="bulkDelete" class="ddr-btn-danger text-xs">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                Delete ({{ selectedFileIds.size }})
              </button>
            </Transition>
            <label class="ddr-btn-primary text-xs cursor-pointer">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
              Add files
              <input ref="widgetFileInput" type="file" multiple class="hidden" @change="handleWidgetSelect" />
            </label>
          </div>
        </div>

        <!-- Drop overlay -->
        <Transition name="drop-overlay">
          <div v-if="isDragging" class="ddr-drop-overlay">
            <div class="ddr-drop-inner">
              <svg class="w-12 h-12 text-[var(--clm-primary)] animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <p class="text-base font-semibold text-[var(--clm-primary)] mt-3">Drop to upload to "{{ activeFolder.name }}"</p>
              <p class="text-xs text-gray-400 mt-1">Release files to add them to the upload queue</p>
            </div>
          </div>
        </Transition>

        <!-- Upload queue tray -->
        <Transition name="tray-slide">
          <div v-if="(widgetQueue.length || widgetUploadJobs.length) && !isDragging" class="ddr-upload-tray">
            <div class="ddr-upload-tray-header">
              <div class="flex items-center gap-3 min-w-0">
                <div class="ddr-upload-tray-icon" :class="widgetUploading ? 'ddr-uploading' : ''">
                  <svg v-if="!widgetUploading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                  <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                </div>
                <div>
                  <p class="text-[13px] font-semibold text-[var(--clm-text)]">
                    {{ widgetUploading ? 'Uploading files...' : `${widgetQueue.length} file(s) ready` }}
                  </p>
                  <p class="text-[11px] text-gray-400">{{ formatBytes(widgetQueueSize) }} total</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button v-if="!widgetUploading && widgetQueue.length" @click="widgetQueue = []" class="ddr-btn-ghost text-xs">Clear</button>
                <button v-if="!widgetUploading && widgetQueue.length" @click="uploadFromWidget" class="ddr-btn-primary text-xs">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                  Upload All
                </button>
              </div>
            </div>

            <!-- File list -->
            <div class="ddr-upload-tray-body">
              <template v-if="!widgetUploading">
                <div v-for="(item, idx) in widgetQueue" :key="'q-'+idx" class="ddr-queue-item group/qi">
                  <div class="ddr-queue-icon" :class="fileIconClass(item.file?.type)">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                  </div>
                  <span class="ddr-queue-name">{{ item.name }}</span>
                  <span class="ddr-queue-size">{{ formatBytes(item.size) }}</span>
                  <button @click="widgetQueue.splice(idx, 1)" class="ddr-queue-remove">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                  </button>
                </div>
              </template>
              <template v-if="widgetUploadJobs.length">
                <div v-for="job in widgetUploadJobs" :key="job.key" class="ddr-progress-item">
                  <div class="ddr-progress-icon" :class="job.progress === 100 ? 'ddr-done' : 'ddr-active'">
                    <svg v-if="job.progress === 100" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                    <svg v-else class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  </div>
                  <span class="ddr-queue-name">{{ job.name }}</span>
                  <div class="ddr-progress-bar">
                    <div class="ddr-progress-fill" :class="job.progress === 100 ? 'ddr-fill-done' : 'ddr-fill-active'" :style="{ width: `${job.progress}%` }"></div>
                  </div>
                  <span class="ddr-progress-pct" :class="job.progress === 100 ? 'text-emerald-600' : 'text-[var(--clm-primary)]'">{{ job.progress }}%</span>
                </div>
              </template>
            </div>
          </div>
        </Transition>

        <!-- File area -->
        <div v-if="!isDragging" class="ddr-files-area">
          <!-- Empty state -->
          <div v-if="!filteredFiles.length && !activeFolder.files?.length && !widgetQueue.length && !widgetUploadJobs.length"
            class="ddr-empty-state" @click="$refs.widgetFileInput.click()">
            <div class="ddr-empty-icon">
              <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            </div>
            <h3 class="text-base font-semibold text-gray-400 mt-4 group-hover:text-[var(--clm-primary)] transition">No documents yet</h3>
            <p class="text-xs text-gray-400 mt-1.5 max-w-xs mx-auto">Drag and drop files here, or click to browse. Supports any file type with up to 5 parallel uploads.</p>
          </div>

          <!-- No search results -->
          <div v-else-if="!filteredFiles.length && !widgetQueue.length && !widgetUploadJobs.length" class="py-12 text-center">
            <svg class="mx-auto w-8 h-8 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
            <p class="text-sm text-gray-400 mt-3">No files match your filters</p>
          </div>

          <!-- Grid view -->
          <TransitionGroup v-else-if="viewMode === 'grid'" name="file-card" tag="div" class="ddr-grid">
            <div v-for="file in filteredFiles" :key="file.id" class="ddr-file-card group"
              draggable="true" @dragstart="onFileDragStart($event, file)" @dragend="onFileDragEnd">
              <div class="ddr-file-thumb" @click="previewOrSelect(file, $event)">
                <img v-if="isImage(file.content_type)" :src="`/api/document-drive-files/${file.id}/preview`" class="w-full h-full object-cover" loading="lazy" />
                <div v-else class="flex flex-col items-center gap-1.5">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="fileIconClass(file.content_type)">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                  </div>
                  <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ fileExtLabel(file.original_filename) }}</span>
                </div>
                <div class="absolute top-2 left-2 z-10">
                  <input type="checkbox" :checked="selectedFileIds.has(file.id)" @click.stop="toggleSelect(file.id)" class="ddr-checkbox" />
                </div>
                <div v-if="canPreview(file)" class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
                  <button @click.stop="openPreview(file)" class="w-7 h-7 rounded-lg bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition backdrop-blur-sm">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                  </button>
                </div>
                <div class="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
              </div>
              <div class="ddr-file-info">
                <p class="text-[12px] font-medium text-[var(--clm-text)] truncate" :title="file.original_filename">{{ file.original_filename }}</p>
                <div class="flex items-center justify-between mt-1.5">
                  <span class="text-[11px] text-gray-400 tabular-nums">{{ formatBytes(file.size_bytes) }}</span>
                  <div class="ddr-file-actions">
                    <button v-if="canPreview(file)" @click.stop="openPreview(file)" class="ddr-file-action" title="Preview"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg></button>
                    <button @click.stop="startRename(file)" class="ddr-file-action" title="Rename"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>
                    <a :href="`/api/document-drive-files/${file.id}/download`" target="_blank" class="ddr-file-action" title="Download"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg></a>
                    <button @click.stop="deleteSingleFile(file)" class="ddr-file-action ddr-file-action-danger" title="Delete"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <!-- List view -->
          <div v-else class="ddr-list">
            <div class="ddr-list-header">
              <span class="w-6"></span>
              <span class="flex-1">Name</span>
              <span class="w-20 text-center">Type</span>
              <span class="w-20 text-right">Size</span>
              <span class="w-28"></span>
            </div>
            <TransitionGroup name="file-row" tag="div">
              <div v-for="file in filteredFiles" :key="file.id" class="ddr-list-row group"
                :class="selectedFileIds.has(file.id) ? 'ddr-list-row-selected' : ''"
                draggable="true" @dragstart="onFileDragStart($event, file)" @dragend="onFileDragEnd">
                <input type="checkbox" :checked="selectedFileIds.has(file.id)" @change="toggleSelect(file.id)" class="ddr-checkbox" />
                <div class="flex items-center gap-3 min-w-0 flex-1">
                  <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" :class="fileIconClass(file.content_type)">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                  </div>
                  <p class="text-[12px] font-medium text-[var(--clm-text)] truncate" :title="file.original_filename">{{ file.original_filename }}</p>
                </div>
                <span class="w-20 text-center text-[11px] font-semibold uppercase text-gray-400 tracking-wide">{{ fileExtLabel(file.original_filename) }}</span>
                <span class="w-20 text-right text-[11px] text-gray-400 tabular-nums">{{ formatBytes(file.size_bytes) }}</span>
                <div class="w-28 flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <button v-if="canPreview(file)" @click="openPreview(file)" class="ddr-file-action" title="Preview"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg></button>
                  <button @click="startRename(file)" class="ddr-file-action" title="Rename"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>
                  <a :href="`/api/document-drive-files/${file.id}/download`" target="_blank" class="ddr-file-action" title="Download"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg></a>
                  <button @click="deleteSingleFile(file)" class="ddr-file-action ddr-file-action-danger" title="Delete"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button>
                </div>
              </div>
            </TransitionGroup>
          </div>

          <!-- Persistent upload drop zone (always visible when files exist) -->
          <div v-if="filteredFiles.length || widgetQueue.length || widgetUploadJobs.length"
            class="ddr-upload-zone"
            :class="widgetDragging ? 'ddr-upload-zone-active' : ''"
            @click="$refs.widgetFileInput.click()"
            @dragover.prevent="widgetDragging = true"
            @dragleave.prevent="widgetDragging = false"
            @drop.prevent="handleWidgetDrop"
          >
            <div class="ddr-upload-zone-icon" :class="widgetDragging ? 'ddr-uploading' : ''">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            </div>
            <div>
              <p class="text-[12px] font-medium" :class="widgetDragging ? 'text-[var(--clm-primary)]' : 'text-gray-500'">
                {{ widgetDragging ? 'Release to add files' : 'Drop files here or click to upload' }}
              </p>
              <p class="text-[10px] text-gray-400 mt-0.5">Drag & drop &middot; Multiple files &middot; Up to 5 parallel uploads</p>
            </div>
          </div>
        </div>
      </main>

      <!-- No folder selected -->
      <div v-else class="ddr-no-folder">
        <div class="ddr-empty-icon">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
        </div>
        <p class="text-sm font-medium text-gray-400 mt-4">Select a folder to manage documents</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">Or create a new folder from the sidebar</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { swalError, toast } from '../utils/swal.js'
import { injectHighlightStylesIntoDocument } from '../utils/chunkTextLocate.js'
import { startNotifications, stopNotifications, onNotification } from '../utils/notificationSocket.js'

const route = useRoute()
const CHUNK_SIZE_BYTES = 5 * 1024 * 1024
const MAX_PARALLEL_FILES = 5

const driveId = Number(route.params.driveId)
const drive = ref(null)
const folders = ref([])
const activeFolderId = ref(null)
const activeFolder = ref(null)
const folderDraftName = ref('')
const folderCreating = ref(false)
const savingFolder = ref(false)
const selectedFiles = ref([])
const uploading = ref(false)
const uploadJobs = ref([])

const searchQuery = ref('')
const typeFilter = ref('')
const sortBy = ref('newest')
const viewMode = ref('grid')
const selectedFileIds = ref(new Set())
const isDragging = ref(false)

const previewFile = ref(null)
const previewUrl = ref(null)
const previewWidth = ref(1000)
const renameTarget = ref(null)
const renameValue = ref('')
const moveTarget = ref(null)
const movingFile = ref(false)
const draggedFile = ref(null)
const draggedFolder = ref(null)
const dragOverFolderId = ref(null)

const expandedFolderIds = ref(new Set())
const subfolderParentId = ref(null)
const subfolderDraftName = ref('')

const widgetDragging = ref(false)
const widgetQueue = ref([])
const widgetUploading = ref(false)
const widgetUploadJobs = ref([])

const chunksDrawerOpen = ref(false)
const chunksDrawerWidth = ref(360)
const fileChunks = ref([])
const chunksLoading = ref(false)
const expandedChunkIds = ref(new Set())
const expandAllChunks = ref(false)
const activeChunkId = ref(null)
const previewIframe = ref(null)
const pdfScrollContainer = ref(null)
const pdfPagesContainer = ref(null)

const isPdfPreview = computed(() => {
  const ct = (previewFile.value?.content_type || '').toLowerCase()
  return ct.includes('pdf')
})

let _pdfjsLibPromise = null
const _loadPdfJsLib = async () => {
  if (!_pdfjsLibPromise) _pdfjsLibPromise = import('pdfjs-dist')
  const lib = await _pdfjsLibPromise
  lib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
  return lib
}

const totalPanelWidth = computed(() => {
  const base = previewWidth.value
  return chunksDrawerOpen.value ? base + chunksDrawerWidth.value : base
})

const totalFiles = computed(() => folders.value.reduce((a, f) => a + (f.files?.length || 0), 0))
const totalSize = computed(() => folders.value.reduce((a, f) => a + (f.files || []).reduce((s, file) => s + (file.size_bytes || 0), 0), 0))

const folderMap = computed(() => {
  const m = {}
  for (const f of folders.value) m[f.id] = f
  return m
})

const flatFolderList = computed(() => {
  const roots = folders.value.filter(f => !f.parent_id)
  const result = []
  const walk = (parentId, depth) => {
    const children = folders.value.filter(f => f.parent_id === parentId)
    children.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
    for (const folder of children) {
      const hasChildren = folders.value.some(f => f.parent_id === folder.id)
      const isExpanded = expandedFolderIds.value.has(folder.id)
      result.push({ folder, depth, hasChildren, isExpanded })
      if (hasChildren && isExpanded) walk(folder.id, depth + 1)
    }
  }
  roots.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
  for (const root of roots) {
    const hasChildren = folders.value.some(f => f.parent_id === root.id)
    const isExpanded = expandedFolderIds.value.has(root.id)
    result.push({ folder: root, depth: 0, hasChildren, isExpanded })
    if (hasChildren && isExpanded) walk(root.id, 1)
  }
  return result
})

const breadcrumbs = computed(() => {
  if (!activeFolderId.value) return []
  const path = []
  let current = folderMap.value[activeFolderId.value]
  while (current) {
    path.unshift(current)
    current = current.parent_id ? folderMap.value[current.parent_id] : null
  }
  return path
})

const totalFolderFileCount = (folderId) => {
  let count = 0
  const folder = folderMap.value[folderId]
  if (folder) count += (folder.files?.length || 0)
  for (const f of folders.value) {
    if (f.parent_id === folderId) count += totalFolderFileCount(f.id)
  }
  return count
}

const toggleExpand = (folderId) => {
  const s = new Set(expandedFolderIds.value)
  s.has(folderId) ? s.delete(folderId) : s.add(folderId)
  expandedFolderIds.value = s
}

const expandParents = (folderId) => {
  const s = new Set(expandedFolderIds.value)
  let current = folderMap.value[folderId]
  while (current?.parent_id) {
    s.add(current.parent_id)
    current = folderMap.value[current.parent_id]
  }
  expandedFolderIds.value = s
}

const startSubfolderCreate = (parentId) => {
  subfolderParentId.value = parentId
  subfolderDraftName.value = ''
  const s = new Set(expandedFolderIds.value)
  s.add(parentId)
  expandedFolderIds.value = s
}

const cancelSubfolderCreate = () => {
  subfolderParentId.value = null
  subfolderDraftName.value = ''
}

const createSubfolder = async () => {
  if (!subfolderDraftName.value.trim() || !subfolderParentId.value) return
  folderCreating.value = true
  try {
    const { data } = await axios.post(`/api/document-drives/${driveId}/folders`, {
      name: subfolderDraftName.value.trim(),
      description: null,
      parent_id: subfolderParentId.value,
    })
    folders.value = [...folders.value, data]
    subfolderDraftName.value = ''
    subfolderParentId.value = null
    toast('Subfolder created')
    await openFolder(data)
  } catch (e) {
    swalError('Could not create subfolder')
  } finally {
    folderCreating.value = false
  }
}

const fileExtLabel = (name) => {
  if (!name) return '?'
  const ext = name.split('.').pop()
  return ext && ext.length <= 5 ? ext.toUpperCase() : '?'
}

const isImage = (ct) => ct && ct.startsWith('image/')
const isPdf = (ct) => ct && ct.includes('pdf')
const isWord = (ct) => ct && (ct.includes('word') || ct.includes('document'))
const isExcel = (ct) => ct && (ct.includes('sheet') || ct.includes('excel'))
const isText = (ct) => ct && ct.startsWith('text/')

const canPreview = (file) => {
  const ct = (file.content_type || '').toLowerCase()
  return isImage(ct) || isPdf(ct) || isWord(ct) || isText(ct)
}

const openPreview = async (file) => {
  previewFile.value = file
  const ct = (file.content_type || '').toLowerCase()
  if (ct.includes('pdf')) {
    previewUrl.value = null
    await nextTick()
    renderPdfPreview(file.id)
  } else {
    previewUrl.value = canPreview(file) ? `/api/document-drive-files/${file.id}/preview` : null
  }
  loadChunks(file.id)
}

const closePreview = () => {
  previewFile.value = null
  previewUrl.value = null
  chunksDrawerOpen.value = false
  fileChunks.value = []
  expandedChunkIds.value = new Set()
  activeChunkId.value = null
  _destroyPdfPages()
}

const _destroyPdfPages = () => {
  if (pdfPagesContainer.value) pdfPagesContainer.value.innerHTML = ''
}

const _safeGetTextContent = async (page) => {
  try {
    return await page.getTextContent()
  } catch { /* for-await on ReadableStream unsupported — use reader fallback */ }
  try {
    const stream = page.streamTextContent()
    const reader = stream.getReader()
    const items = []
    const styles = Object.create(null)
    let lang = null
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (value) {
        lang = lang || value.lang
        Object.assign(styles, value.styles)
        items.push(...value.items)
      }
    }
    return { items, styles, lang }
  } catch (e) {
    console.warn('streamTextContent fallback failed:', e)
    return { items: [], styles: {}, lang: null }
  }
}

const _matMul = (m, v) => [
  m[0]*v[0]+m[2]*v[1], m[1]*v[0]+m[3]*v[1],
  m[0]*v[2]+m[2]*v[3], m[1]*v[2]+m[3]*v[3],
  m[0]*v[4]+m[2]*v[5]+m[4], m[1]*v[4]+m[3]*v[5]+m[5],
]

const renderPdfPreview = async (fileId) => {
  try {
    const pdfjsLib = await _loadPdfJsLib()
    const url = `/api/document-drive-files/${fileId}/preview`
    const pdfDoc = await pdfjsLib.getDocument(url).promise
    const container = pdfPagesContainer.value
    if (!container) return
    container.innerHTML = ''

    const dpr = Math.min(window.devicePixelRatio || 1, 2.5)

    for (let i = 1; i <= pdfDoc.numPages; i++) {
      const page = await pdfDoc.getPage(i)
      const baseViewport = page.getViewport({ scale: 1 })
      const containerWidth = pdfScrollContainer.value?.clientWidth || 800
      const scale = (containerWidth - 48) / baseViewport.width
      const cssViewport = page.getViewport({ scale })
      const hiresViewport = page.getViewport({ scale: scale * dpr })
      const w = Math.floor(cssViewport.width)
      const h = Math.floor(cssViewport.height)

      const pageDiv = document.createElement('div')
      pageDiv.className = 'ddr-pdf-page'
      pageDiv.style.cssText = `width:${w}px;height:${h}px;position:relative;`

      const canvas = document.createElement('canvas')
      canvas.width = Math.floor(hiresViewport.width)
      canvas.height = Math.floor(hiresViewport.height)
      canvas.style.cssText = `width:${w}px;height:${h}px;display:block;`
      pageDiv.appendChild(canvas)

      const ctx = canvas.getContext('2d', { alpha: false })
      await page.render({ canvasContext: ctx, viewport: hiresViewport }).promise
      container.appendChild(pageDiv)

      const textContent = await _safeGetTextContent(page)
      if (!textContent.items.length) continue

      const textDiv = document.createElement('div')
      textDiv.className = 'ddr-pdf-text-layer'
      textDiv.style.cssText = `position:absolute;left:0;top:0;width:${w}px;height:${h}px;overflow:hidden;`

      const vt = cssViewport.transform
      for (const item of textContent.items) {
        if (!item.str) continue
        const tx = _matMul(vt, item.transform)
        const fh = Math.hypot(tx[2], tx[3])
        const ascent = fh * 0.8
        const angle = Math.atan2(tx[1], tx[0])

        const span = document.createElement('span')
        span.textContent = _normalizeText(item.str)
        let css = `position:absolute;left:${tx[4].toFixed(1)}px;top:${(tx[5] - ascent).toFixed(1)}px;font-size:${fh.toFixed(1)}px;font-family:sans-serif;color:transparent;white-space:pre;`
        if (Math.abs(angle) > 0.001) css += `transform:rotate(${(angle * 180 / Math.PI).toFixed(2)}deg);transform-origin:0% 0%;`
        span.style.cssText = css
        textDiv.appendChild(span)
        textDiv.appendChild(document.createTextNode(' '))
      }

      pageDiv.appendChild(textDiv)
    }
  } catch (e) {
    console.error('PDF render failed:', e)
  }
}

const toggleChunksDrawer = () => {
  chunksDrawerOpen.value = !chunksDrawerOpen.value
}

const loadChunks = async (fileId) => {
  chunksLoading.value = true
  fileChunks.value = []
  expandedChunkIds.value = new Set()
  activeChunkId.value = null
  try {
    const { data } = await axios.get(`/api/document-drive-files/${fileId}/chunks`)
    fileChunks.value = data
  } catch (e) {
    console.error('Failed to load chunks:', e)
  } finally {
    chunksLoading.value = false
  }
}

const toggleChunkExpand = (chunkId) => {
  const s = new Set(expandedChunkIds.value)
  s.has(chunkId) ? s.delete(chunkId) : s.add(chunkId)
  expandedChunkIds.value = s
}

const isChunkExpanded = (chunkId) => {
  return expandAllChunks.value || expandedChunkIds.value.has(chunkId)
}

const copyChunk = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    toast('Copied to clipboard')
  } catch {
    /* fallback: not critical */
  }
}

const onIframeLoad = () => {
  injectHighlightStyles()
}

const injectHighlightStyles = () => {
  const iframe = previewIframe.value
  if (!iframe) return
  try {
    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (!doc) return
    injectHighlightStylesIntoDocument(doc)
  } catch { /* cross-origin */ }
}

const clearHighlights = (el) => {
  try {
    const marks = el.querySelectorAll('.ddr-chunk-hl')
    marks.forEach(mark => {
      const parent = mark.parentNode
      while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
      parent.removeChild(mark)
      parent.normalize()
    })
  } catch { /* ignore */ }
}

const SMART_SINGLE = '\u2018\u2019\u201A\u201B\u2032\u2035`'
const SMART_DOUBLE = '\u201C\u201D\u201E\u201F\u2033\u2036\u00AB\u00BB'
const DASHES       = '\u2013\u2014\u2015\u2212'
const NBSP_CHARS   = '\u00A0\u202F\u205F\u3000\uFEFF'

const _LIGATURE_MAP = {
  '\ufb00': 'ff', '\ufb01': 'fi', '\ufb02': 'fl',
  '\ufb03': 'ffi', '\ufb04': 'ffl', '\ufb05': 'ft', '\ufb06': 'st',
}

const _normalizeText = (text) => {
  for (const [lig, repl] of Object.entries(_LIGATURE_MAP)) {
    text = text.replaceAll(lig, repl)
  }
  text = text.replace(/(?<=[a-zA-Z])P(?=[a-z])/g, 'ff')
  return text
}

const _replaceChar = (ch) => {
  if (_LIGATURE_MAP[ch]) return _LIGATURE_MAP[ch]
  if (SMART_SINGLE.includes(ch)) return "'"
  if (SMART_DOUBLE.includes(ch)) return '"'
  if (DASHES.includes(ch)) return '-'
  if (ch === '\u2026') return '...'
  if (NBSP_CHARS.includes(ch)) return ' '
  const c = ch.charCodeAt(0)
  if (c >= 0x2000 && c <= 0x200B) return ' '
  return ch.toLowerCase()
}

const _scrub = (s) => {
  let out = ''
  for (let i = 0; i < s.length; i++) out += _replaceChar(s[i])
  return out.replace(/\s+/g, ' ').trim()
}

const _buildTextMap = (doc, root) => {
  const walkRoot = root || doc.body
  const walker = doc.createTreeWalker(walkRoot, NodeFilter.SHOW_TEXT, null)
  const entries = []
  let raw = ''
  let node
  while ((node = walker.nextNode())) {
    const start = raw.length
    raw += node.textContent
    entries.push({ node, start, end: raw.length })
  }

  const expanded = []
  for (let i = 0; i < raw.length; i++) {
    const rep = _replaceChar(raw[i])
    for (let j = 0; j < rep.length; j++) expanded.push({ ch: rep[j], rawIdx: i })
  }

  let scrubbed = ''
  const scrubToRaw = []
  let prevSpace = true
  for (const item of expanded) {
    if (/\s/.test(item.ch)) {
      if (!prevSpace) {
        scrubbed += ' '
        scrubToRaw.push(item.rawIdx)
        prevSpace = true
      }
    } else {
      scrubbed += item.ch
      scrubToRaw.push(item.rawIdx)
      prevSpace = false
    }
  }
  if (scrubbed.endsWith(' ')) {
    scrubbed = scrubbed.slice(0, -1)
    scrubToRaw.pop()
  }

  return { entries, raw, scrubbed, scrubToRaw }
}

const _findSpan = (textMap, needle) => {
  const sNeedle = _scrub(needle)
  if (!sNeedle || sNeedle.length < 2) return null

  const _rawSpan = (scrubIdx, scrubLen) => {
    const s = Math.min(scrubIdx, textMap.scrubToRaw.length - 1)
    const e = Math.min(scrubIdx + scrubLen - 1, textMap.scrubToRaw.length - 1)
    return { rawStart: textMap.scrubToRaw[s], rawEnd: textMap.scrubToRaw[e] + 1 }
  }

  let idx = textMap.scrubbed.indexOf(sNeedle)
  if (idx !== -1) return _rawSpan(idx, sNeedle.length)

  // Progressively shorten the needle until we find a match (handles minor
  // text differences between backend extraction and pdf.js rendering).
  for (const ratio of [0.9, 0.8, 0.65, 0.5]) {
    const trimLen = Math.max(10, Math.floor(sNeedle.length * ratio))
    const sub = sNeedle.substring(0, trimLen)
    const i = textMap.scrubbed.indexOf(sub)
    if (i !== -1) {
      // We matched the head; try to find where the tail ends to cover the
      // full chunk.  Walk forward in scrubbed to find the tail anchor.
      const tail = sNeedle.substring(sNeedle.length - Math.min(40, Math.floor(sNeedle.length * 0.25)))
      const tailSearch = tail.length >= 6 ? textMap.scrubbed.indexOf(tail, i) : -1
      if (tailSearch !== -1) {
        return _rawSpan(i, (tailSearch + tail.length) - i)
      }
      // No tail found — use head position + original needle length as estimate
      const estEnd = Math.min(i + sNeedle.length, textMap.scrubbed.length)
      return _rawSpan(i, estEnd - i)
    }
  }

  // Last resort: anchor-only search with head and tail fragments
  const headFrag = sNeedle.substring(0, Math.min(60, Math.floor(sNeedle.length * 0.35)))
  const tailFrag = sNeedle.substring(Math.max(sNeedle.length - 60, Math.ceil(sNeedle.length * 0.65)))

  const hIdx = headFrag.length >= 6 ? textMap.scrubbed.indexOf(headFrag) : -1
  const tIdx = tailFrag.length >= 6 ? textMap.scrubbed.indexOf(tailFrag, Math.max(0, hIdx)) : -1

  if (hIdx !== -1 && tIdx !== -1) {
    return _rawSpan(hIdx, (tIdx + tailFrag.length) - hIdx)
  }
  if (hIdx !== -1) {
    const estEnd = Math.min(hIdx + sNeedle.length, textMap.scrubbed.length)
    return _rawSpan(hIdx, estEnd - hIdx)
  }
  if (tIdx !== -1) {
    const estStart = Math.max(0, tIdx + tailFrag.length - sNeedle.length)
    return _rawSpan(estStart, (tIdx + tailFrag.length) - estStart)
  }

  return null
}

const _collectSegments = (textMap, rawStart, rawEnd) => {
  const segments = []
  for (const entry of textMap.entries) {
    if (entry.end <= rawStart) continue
    if (entry.start >= rawEnd) break
    const segStart = Math.max(rawStart, entry.start) - entry.start
    const segEnd = Math.min(rawEnd, entry.end) - entry.start
    if (segEnd > segStart) {
      segments.push({ node: entry.node, offset: segStart, length: segEnd - segStart })
    }
  }
  return segments
}

const _wrapSegments = (doc, segments) => {
  const marks = []
  for (let i = segments.length - 1; i >= 0; i--) {
    const seg = segments[i]
    try {
      if (!seg.node.parentNode) continue
      const nodeLen = seg.node.textContent.length
      const off = Math.min(seg.offset, nodeLen)
      const end = Math.min(seg.offset + seg.length, nodeLen)
      if (end <= off) continue

      const mark = doc.createElement('mark')
      mark.className = 'ddr-chunk-hl'

      if (off === 0 && end >= nodeLen) {
        seg.node.parentNode.replaceChild(mark, seg.node)
        mark.appendChild(seg.node)
      } else {
        const range = doc.createRange()
        range.setStart(seg.node, off)
        range.setEnd(seg.node, end)
        try {
          range.surroundContents(mark)
        } catch {
          const fragment = range.extractContents()
          mark.appendChild(fragment)
          range.insertNode(mark)
        }
      }
      marks.unshift(mark)
    } catch { /* skip node if wrapping fails */ }
  }
  return marks
}

const _getHighlightRoot = () => {
  if (isPdfPreview.value) {
    return pdfPagesContainer.value || null
  }
  const iframe = previewIframe.value
  if (!iframe) return null
  try {
    return iframe.contentDocument?.body || iframe.contentWindow?.document?.body || null
  } catch { return null }
}

const _cleanChunkForSearch = (text) =>
  _normalizeText(text.replace(/---\s*Page\s+\d+\s*---/gi, '').trim())

const _HL_STYLE = 'background:rgba(253,224,71,0.5)!important;border-bottom:2px solid #facc15;border-radius:2px;padding:1px 0;color:transparent;'

const scrollToChunkInPreview = (chunk) => {
  activeChunkId.value = chunk.id

  const root = _getHighlightRoot()
  if (!root) return

  try {
    const ownerDoc = root.ownerDocument || document
    clearHighlights(root)

    if (!isPdfPreview.value) {
      injectHighlightStyles()
    }

    const searchText = _cleanChunkForSearch(chunk.content)
    if (!searchText || searchText.length < 3) return

    const textMap = _buildTextMap(ownerDoc, root)
    const span = _findSpan(textMap, searchText)
    if (!span) return

    const segments = _collectSegments(textMap, span.rawStart, span.rawEnd)
    if (!segments.length) return

    const marks = _wrapSegments(ownerDoc, segments)
    if (isPdfPreview.value) {
      marks.forEach((m) => { m.style.cssText = _HL_STYLE })
    }
    if (marks.length) {
      const first = marks[0]
      if (isPdfPreview.value && pdfScrollContainer.value) {
        const rect = first.getBoundingClientRect()
        const cRect = pdfScrollContainer.value.getBoundingClientRect()
        pdfScrollContainer.value.scrollTo({
          top: pdfScrollContainer.value.scrollTop + rect.top - cRect.top - 60,
          behavior: 'smooth',
        })
      } else {
        first.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
    if (!isPdfPreview.value) {
      previewIframe.value?.contentWindow?.getSelection()?.removeAllRanges()
    }
  } catch (e) {
    console.warn('scrollToChunkInPreview:', e)
  }
}

const startDrawerResize = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startW = chunksDrawerWidth.value
  const onMove = (ev) => {
    const delta = startX - ev.clientX
    chunksDrawerWidth.value = Math.max(280, Math.min(600, startW + delta))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

const previewableFiles = computed(() => (activeFolder.value?.files || []).filter(canPreview))
const currentPreviewIndex = computed(() => {
  if (!previewFile.value) return -1
  return previewableFiles.value.findIndex((f) => f.id === previewFile.value.id)
})
const canNavigatePrev = computed(() => currentPreviewIndex.value > 0)
const canNavigateNext = computed(() => currentPreviewIndex.value >= 0 && currentPreviewIndex.value < previewableFiles.value.length - 1)
const navigatePreview = (dir) => {
  const idx = currentPreviewIndex.value + dir
  if (idx >= 0 && idx < previewableFiles.value.length) {
    openPreview(previewableFiles.value[idx])
  }
}

const startResize = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startW = previewWidth.value
  const drawerExtra = chunksDrawerOpen.value ? chunksDrawerWidth.value : 0
  const onMove = (ev) => {
    const delta = startX - ev.clientX
    previewWidth.value = Math.max(360, Math.min(window.innerWidth - drawerExtra, startW + delta))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

const fileTypeCategory = (ct) => {
  if (!ct) return 'other'
  if (isPdf(ct)) return 'pdf'
  if (isImage(ct)) return 'image'
  if (isWord(ct)) return 'word'
  if (isExcel(ct)) return 'excel'
  return 'other'
}

const filteredFiles = computed(() => {
  let files = [...(activeFolder.value?.files || [])]
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    files = files.filter((f) => f.original_filename.toLowerCase().includes(q))
  }
  if (typeFilter.value) {
    files = files.filter((f) => fileTypeCategory(f.content_type) === typeFilter.value)
  }
  switch (sortBy.value) {
    case 'oldest': files.sort((a, b) => a.id - b.id); break
    case 'name': files.sort((a, b) => a.original_filename.localeCompare(b.original_filename)); break
    case 'name_desc': files.sort((a, b) => b.original_filename.localeCompare(a.original_filename)); break
    case 'size_desc': files.sort((a, b) => (b.size_bytes || 0) - (a.size_bytes || 0)); break
    case 'size_asc': files.sort((a, b) => (a.size_bytes || 0) - (b.size_bytes || 0)); break
    default: files.sort((a, b) => b.id - a.id)
  }
  return files
})

const toggleSelect = (id) => {
  const s = new Set(selectedFileIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedFileIds.value = s
}

const previewOrSelect = (file, event) => {
  if (event.shiftKey || event.ctrlKey || event.metaKey) {
    toggleSelect(file.id)
  } else if (canPreview(file)) {
    openPreview(file)
  }
}

const fileIconClass = (contentType) => {
  if (!contentType) return 'bg-gray-100 dark:bg-gray-800 text-gray-400'
  if (contentType.includes('pdf')) return 'bg-red-50 dark:bg-red-900/30 text-red-500'
  if (contentType.includes('image')) return 'bg-amber-50 dark:bg-amber-900/30 text-amber-500'
  if (contentType.includes('word') || contentType.includes('document')) return 'bg-blue-50 dark:bg-blue-900/30 text-blue-500'
  if (contentType.includes('sheet') || contentType.includes('excel')) return 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-500'
  return 'bg-gray-100 dark:bg-gray-800 text-gray-400'
}

const formatBytes = (value) => {
  const v = Number(value || 0)
  if (v === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = v
  let idx = 0
  while (size >= 1024 && idx < units.length - 1) { size /= 1024; idx++ }
  return `${size.toFixed(size >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`
}

const startRename = (file) => {
  renameTarget.value = file
  renameValue.value = file.original_filename
}
const confirmRename = async () => {
  if (!renameTarget.value || !renameValue.value.trim()) return
  try {
    const { data } = await axios.patch(`/api/document-drive-files/${renameTarget.value.id}/rename`, { original_filename: renameValue.value.trim() })
    if (activeFolder.value?.files) {
      activeFolder.value.files = activeFolder.value.files.map((f) => f.id === data.id ? data : f)
    }
    toast('File renamed')
  } catch (e) {
    swalError('Could not rename file')
  }
  renameTarget.value = null
}

const onFileDragStart = (event, file) => {
  draggedFile.value = file
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/x-ddr-file-id', String(file.id))
  event.target.style.opacity = '0.5'
}

const onFileDragEnd = (event) => {
  draggedFile.value = null
  dragOverFolderId.value = null
  if (event.target) event.target.style.opacity = ''
}

const onFolderDragStart = (event, folder) => {
  draggedFolder.value = folder
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/x-ddr-folder-id', String(folder.id))
  event.target.style.opacity = '0.5'
}

const onFolderDragEnd = (event) => {
  draggedFolder.value = null
  dragOverFolderId.value = null
  if (event.target) event.target.style.opacity = ''
}

const moveToRoot = async () => {
  dragOverFolderId.value = null
  const folder = draggedFolder.value
  draggedFolder.value = null
  if (!folder || !folder.parent_id) return
  try {
    await axios.patch(`/api/document-drive-folders/${folder.id}/move`, { parent_id: null })
    const idx = folders.value.findIndex(f => f.id === folder.id)
    if (idx !== -1) {
      folders.value[idx] = { ...folders.value[idx], parent_id: null }
      folders.value = [...folders.value]
    }
    toast(`Moved "${folder.name}" to root`)
  } catch (e) {
    swalError('Could not move folder')
  }
}

const onFolderDragOver = (folder) => {
  if (draggedFile.value) {
    if (folder.id === activeFolderId.value) return
    dragOverFolderId.value = folder.id
  } else if (draggedFolder.value) {
    if (folder.id === draggedFolder.value.id) return
    if (getDescendantIds(draggedFolder.value.id).includes(folder.id)) return
    dragOverFolderId.value = folder.id
  }
}

const onFolderDragLeave = (folder) => {
  if (dragOverFolderId.value === folder.id) {
    dragOverFolderId.value = null
  }
}

const onFolderDrop = async (event, folder) => {
  dragOverFolderId.value = null

  if (draggedFolder.value) {
    const movedFolder = draggedFolder.value
    draggedFolder.value = null
    if (movedFolder.id === folder.id) return
    if (getDescendantIds(movedFolder.id).includes(folder.id)) return

    try {
      await axios.patch(`/api/document-drive-folders/${movedFolder.id}/move`, { parent_id: folder.id })
      const idx = folders.value.findIndex(f => f.id === movedFolder.id)
      if (idx !== -1) {
        folders.value[idx] = { ...folders.value[idx], parent_id: folder.id }
        folders.value = [...folders.value]
      }
      const s = new Set(expandedFolderIds.value)
      s.add(folder.id)
      expandedFolderIds.value = s
      toast(`Moved "${movedFolder.name}" into "${folder.name}"`)
    } catch (e) {
      swalError('Could not move folder')
    }
    return
  }

  const file = draggedFile.value
  draggedFile.value = null
  if (!file || folder.id === activeFolderId.value) return

  movingFile.value = true
  try {
    await axios.patch(`/api/document-drive-files/${file.id}/move`, { folder_id: folder.id })
    if (activeFolder.value?.files) {
      activeFolder.value.files = activeFolder.value.files.filter((f) => f.id !== file.id)
      syncFolderFiles()
    }
    const targetIdx = folders.value.findIndex((f) => f.id === folder.id)
    if (targetIdx !== -1) {
      const target = folders.value[targetIdx]
      target.files = [...(target.files || []), { ...file, folder_id: folder.id }]
      folders.value = [...folders.value]
    }
    toast(`Moved to "${folder.name}"`)
  } catch (e) {
    swalError('Could not move file')
  } finally {
    movingFile.value = false
  }
}

const deleteSingleFile = async (file) => {
  if (!confirm(`Delete "${file.original_filename}"?`)) return
  try {
    await axios.delete(`/api/document-drive-files/${file.id}`)
    if (activeFolder.value?.files) {
      activeFolder.value.files = activeFolder.value.files.filter((f) => f.id !== file.id)
    }
    syncFolderFiles()
    toast('File deleted')
  } catch (e) {
    swalError('Could not delete file')
  }
}

const bulkDelete = async () => {
  const ids = [...selectedFileIds.value]
  if (!ids.length) return
  if (!confirm(`Delete ${ids.length} file(s)?`)) return
  let deleted = 0
  for (const id of ids) {
    try {
      await axios.delete(`/api/document-drive-files/${id}`)
      deleted++
      if (activeFolder.value?.files) {
        activeFolder.value.files = activeFolder.value.files.filter((f) => f.id !== id)
      }
    } catch { /* skip */ }
  }
  selectedFileIds.value = new Set()
  syncFolderFiles()
  toast(`Deleted ${deleted} file(s)`)
}

const syncFolderFiles = () => {
  if (!activeFolder.value) return
  const fi = folders.value.findIndex((f) => f.id === activeFolderId.value)
  if (fi !== -1) {
    folders.value[fi] = { ...folders.value[fi], files: activeFolder.value.files }
    folders.value = [...folders.value]
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files?.length) {
    const items = Array.from(files).map((f) => ({ name: f.name, size: f.size, file: f }))
    widgetQueue.value = [...widgetQueue.value, ...items]
  }
}

const FOLDER_STORAGE_KEY = `ddr-active-folder-${driveId}`

const findBestFolder = (allFolders, startFromId = null) => {
  const byParent = {}
  for (const f of allFolders) {
    const pid = f.parent_id || 0
    if (!byParent[pid]) byParent[pid] = []
    byParent[pid].push(f)
  }
  const sortChildren = (arr) => [...arr].sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))

  const walk = (parentId) => {
    const children = sortChildren(byParent[parentId] || [])
    for (const folder of children) {
      if (folder.files?.length > 0) return folder
      const deeper = walk(folder.id)
      if (deeper) return deeper
    }
    return null
  }

  // If starting from a specific folder, check it first then its subtree
  if (startFromId !== null) {
    const startFolder = allFolders.find(f => f.id === startFromId)
    if (startFolder?.files?.length > 0) return startFolder
    return walk(startFromId)
  }

  // Global search: walk every root-level folder
  return walk(0)
}

const loadDrive = async () => {
  try {
    const [driveResponse, foldersResponse] = await Promise.all([
      axios.get(`/api/document-drives/${driveId}`),
      axios.get(`/api/document-drives/${driveId}/folders`),
    ])
    drive.value = driveResponse.data || {}
    const folderData = foldersResponse.data || []
    folders.value = folderData.length ? folderData : (drive.value.folders || [])

    if (folders.value.length && !activeFolderId.value) {
      const savedId = Number(localStorage.getItem(FOLDER_STORAGE_KEY))
      const savedFolder = savedId ? folders.value.find((f) => f.id === savedId) : null

      let best = null
      if (savedFolder) {
        // Saved folder has files → use it directly
        // Saved folder has no files → drill into its subtree for the first child with files
        // If subtree also empty → use saved folder as-is (user was here last)
        best = findBestFolder(folders.value, savedFolder.id) || savedFolder
      } else {
        // No saved state: global DFS for first folder with files, else first root
        best = findBestFolder(folders.value)
          || folders.value.find(f => !f.parent_id)
          || folders.value[0]
      }

      if (best) await openFolder(best)
    }
  } catch (e) {
    console.error('Failed to load drive:', e)
    swalError('Could not load drive')
  }
}

const openFolder = async (folder) => {
  try {
    const { data } = await axios.get(`/api/document-drive-folders/${folder.id}`)
    activeFolder.value = data
    activeFolderId.value = folder.id
    selectedFileIds.value = new Set()
    searchQuery.value = ''
    typeFilter.value = ''
    expandParents(folder.id)
    localStorage.setItem(FOLDER_STORAGE_KEY, String(folder.id))
  } catch (e) {
    swalError('Could not open folder')
  }
}

const createFolder = async () => {
  if (!folderDraftName.value.trim()) return
  folderCreating.value = true
  try {
    const { data } = await axios.post(`/api/document-drives/${driveId}/folders`, {
      name: folderDraftName.value.trim(),
      description: null,
    })
    folders.value = [...folders.value, data]
    folderDraftName.value = ''
    toast('Folder created')
    await openFolder(data)
  } catch (e) {
    swalError('Could not create folder')
  } finally {
    folderCreating.value = false
  }
}

const getDescendantIds = (folderId) => {
  const ids = [folderId]
  const children = folders.value.filter(f => f.parent_id === folderId)
  for (const child of children) ids.push(...getDescendantIds(child.id))
  return ids
}

const deleteFolder = async (folder) => {
  const descendantIds = getDescendantIds(folder.id)
  const subfolderCount = descendantIds.length - 1
  const fileCount = totalFolderFileCount(folder.id)
  let msg = `Delete folder "${folder.name}"`
  if (subfolderCount > 0) msg += `, ${subfolderCount} subfolder(s)`
  if (fileCount > 0) msg += ` and ${fileCount} file(s)`
  msg += '? This cannot be undone.'
  if (!confirm(msg)) return
  try {
    await axios.delete(`/api/document-drive-folders/${folder.id}`)
    folders.value = folders.value.filter((f) => !descendantIds.includes(f.id))
    if (descendantIds.includes(activeFolderId.value)) {
      activeFolder.value = null
      activeFolderId.value = null
      closePreview()
    }
    toast('Folder deleted')
  } catch (e) {
    swalError('Could not delete folder')
  }
}

const saveActiveFolder = async () => {
  if (!activeFolder.value?.name?.trim()) { swalError('Name required'); return }
  savingFolder.value = true
  try {
    const { data } = await axios.patch(`/api/document-drive-folders/${activeFolderId.value}`, {
      name: activeFolder.value.name.trim(),
      description: activeFolder.value.description || '',
    })
    activeFolder.value = data
    folders.value = folders.value.map((f) => (f.id === data.id ? data : f))
    toast('Saved')
  } catch (e) {
    swalError('Could not save')
  } finally {
    savingFolder.value = false
  }
}

const widgetQueueSize = computed(() => widgetQueue.value.reduce((a, f) => a + (f.size || 0), 0))

const handleWidgetDrop = (event) => {
  widgetDragging.value = false
  const files = event.dataTransfer?.files
  if (files?.length) {
    const items = Array.from(files).map((f) => ({ name: f.name, size: f.size, file: f }))
    widgetQueue.value = [...widgetQueue.value, ...items]
  }
}

const handleWidgetSelect = (event) => {
  const files = event.target.files
  if (files?.length) {
    const items = Array.from(files).map((f) => ({ name: f.name, size: f.size, file: f }))
    widgetQueue.value = [...widgetQueue.value, ...items]
  }
}

const uploadFromWidget = async () => {
  if (!activeFolderId.value || !widgetQueue.value.length) return
  widgetUploading.value = true
  uploading.value = true

  const targetId = activeFolderId.value
  const queue = widgetQueue.value.map((item, i) => ({
    name: item.name, file: item.file, order: i,
    key: `w-${item.name}-${item.size}-${i}-${Date.now()}`,
    progress: 0, status: 'queued',
  }))
  widgetUploadJobs.value = queue

  try {
    let cursor = 0
    const total = queue.length
    const runWorker = async () => {
      while (cursor < total) {
        const idx = cursor++
        const job = queue[idx]
        job.status = 'uploading'
        widgetUploadJobs.value = [...widgetUploadJobs.value]
        try {
          const chunks = chunkFile(job.file)
          const uploadId = `${Date.now()}-${Math.random().toString(16).slice(2)}-${job.order}`
          let responseFile = null
          for (const chunk of chunks) {
            const body = new FormData()
            body.append('upload_id', uploadId)
            body.append('chunk_index', String(chunk.index))
            body.append('total_chunks', String(chunks.length))
            body.append('filename', job.name)
            body.append('mime_type', job.file.type || 'application/octet-stream')
            body.append('chunk', chunk.blob, `${job.name}.part`)
            const { data } = await axios.post(`/api/document-drive-folders/${targetId}/files/chunks`, body)
            job.progress = Math.round(((chunk.index + 1) / chunks.length) * 100)
            if (data.complete) { job.status = 'done'; responseFile = data.file }
          }
          if (responseFile && activeFolder.value) {
            activeFolder.value.files = [responseFile, ...(activeFolder.value.files || [])]
            syncFolderFiles()
          }
        } catch {
          job.status = 'failed'; job.progress = 0
          widgetUploadJobs.value = [...widgetUploadJobs.value]
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(MAX_PARALLEL_FILES, total) }, () => runWorker()))
    const ok = widgetUploadJobs.value.filter((j) => j.progress === 100).length
    toast(`Uploaded ${ok} of ${total} file(s)`)
    widgetQueue.value = []
    if (ok === total) { widgetUploadJobs.value = [] }
  } catch { /* handled per-file */ } finally {
    uploading.value = false
    widgetUploading.value = false
  }
}

const chunkFile = (file) => {
  const total = Math.max(1, Math.ceil(file.size / CHUNK_SIZE_BYTES))
  const chunks = []
  for (let i = 0; i < total; i++) {
    chunks.push({ index: i, blob: file.slice(i * CHUNK_SIZE_BYTES, Math.min(file.size, (i + 1) * CHUNK_SIZE_BYTES)) })
  }
  return chunks
}

const onKeydown = (e) => {
  if (!previewFile.value) return
  if (e.key === 'Escape') closePreview()
  if (e.key === 'ArrowLeft' && canNavigatePrev.value) navigatePreview(-1)
  if (e.key === 'ArrowRight' && canNavigateNext.value) navigatePreview(1)
}

// ── Background-task notifications (drive chunking) ───────────────────────────
/** Active background tasks keyed by file_id */
const driveBgTasks = ref([])
let _unsubDriveNotifications = null

function handleDriveNotification(msg) {
  // Only handle chunking events for files that belong to this drive
  // (folder_id is non-null for drive files; we check via the drive's folder tree)
  if (msg.folder_id == null) return

  const key = `chunking-${msg.file_id}`
  const isStart = msg.type === 'chunking_started'
  const isDone  = msg.type === 'chunking_done'
  const isFail  = msg.type === 'chunking_failed'

  if (!isStart && !isDone && !isFail) return

  if (isStart) {
    driveBgTasks.value = driveBgTasks.value.filter(t => t.id !== key)
    driveBgTasks.value.push({ id: key, file_id: msg.file_id, filename: msg.filename, status: 'running' })
    return
  }

  driveBgTasks.value = driveBgTasks.value.map(t =>
    t.id === key ? { ...t, status: isDone ? 'done' : 'failed' } : t
  )

  if (isDone) {
    toast(`Indexing complete: ${msg.filename}`)
    // If the file is currently previewed, reload its chunks
    if (previewFile.value && previewFile.value.id === msg.file_id) {
      loadChunks(msg.file_id)
    }
  } else if (isFail) {
    swalError(msg.message || 'Chunking failed.')
  }

  setTimeout(() => {
    driveBgTasks.value = driveBgTasks.value.filter(t => t.id !== key)
  }, 4000)
}

watch(() => route.params.driveId, () => { if (route.params.driveId) loadDrive() })
onMounted(() => {
  loadDrive()
  window.addEventListener('keydown', onKeydown)
  startNotifications()
  _unsubDriveNotifications = onNotification(handleDriveNotification)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  _unsubDriveNotifications?.()
  stopNotifications()
})
</script>

<style scoped>
/* ── Design tokens ─────────────────────────────────────────────────── */
.ddr-shell {
  --ddr-radius: 10px;
  --ddr-radius-lg: 14px;
  --ddr-border: #e5e7eb;
  --ddr-bg-card: #ffffff;
  --ddr-bg-subtle: #f9fafb;
  min-height: 100vh;
  padding: 20px 24px;
}
:root.dark .ddr-shell {
  --ddr-border: #374151;
  --ddr-bg-card: #111827;
  --ddr-bg-subtle: #0f172a;
}

/* ── Page header ───────────────────────────────────────────────────── */
.ddr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ddr-border);
}

/* ── Layout ────────────────────────────────────────────────────────── */
.ddr-layout {
  display: grid;
  gap: 24px;
  grid-template-columns: 260px 1fr;
}
@media (max-width: 1023px) {
  .ddr-layout { grid-template-columns: 1fr; }
}

/* ── Sidebar ───────────────────────────────────────────────────────── */
.ddr-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.ddr-sidebar-section {
  padding: 0;
}
.ddr-sidebar-empty {
  padding: 40px 16px;
  text-align: center;
}

/* ── Folder navigation ─────────────────────────────────────────────── */
.ddr-folder-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: calc(100vh - 340px);
  overflow-y: auto;
}
.ddr-folder-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--ddr-radius);
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
  position: relative;
  width: 100%;
  text-align: left;
}
.ddr-folder-idle {
  color: var(--clm-text);
}
.ddr-folder-idle:hover {
  background: var(--ddr-bg-subtle);
  border-color: var(--ddr-border);
}
.ddr-folder-active {
  background: color-mix(in srgb, var(--clm-primary) 8%, transparent);
  border-color: color-mix(in srgb, var(--clm-primary) 20%, transparent);
  color: var(--clm-primary);
}
.ddr-expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 4px;
  color: #9ca3af;
  transition: all 0.15s;
}
.ddr-expand-btn:hover { background: rgba(0,0,0,0.06); color: #6b7280; }

.ddr-folder-actions {
  display: flex;
  align-items: center;
  gap: 1px;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.ddr-folder-item:hover .ddr-folder-actions { opacity: 1; }
.ddr-folder-action-btn {
  padding: 3px;
  border-radius: 5px;
  color: #9ca3af;
  transition: all 0.15s;
}
.ddr-folder-action-btn:hover { background: rgba(0,0,0,0.06); color: #6b7280; }
.ddr-folder-action-danger:hover { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

.ddr-subfolder-input {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-right: 12px;
  padding-top: 2px;
  padding-bottom: 2px;
}

.ddr-root-drop-zone {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1.5px dashed #d1d5db;
  border-radius: var(--ddr-radius);
  margin-bottom: 4px;
  color: #9ca3af;
  transition: all 0.2s;
}
.ddr-root-drop-active {
  border-color: var(--clm-primary);
  background: color-mix(in srgb, var(--clm-primary) 8%, transparent);
  color: var(--clm-primary);
}
.ddr-folder-drop-target {
  background: color-mix(in srgb, var(--clm-primary) 12%, transparent) !important;
  border-color: var(--clm-primary) !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--clm-primary) 20%, transparent);
  transform: scale(1.02);
}

.ddr-badge {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  min-width: 20px;
  text-align: center;
  tabular-nums: true;
}

.ddr-details-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  cursor: pointer;
  user-select: none;
  padding: 8px 0;
  list-style: none;
}
.ddr-details-summary::-webkit-details-marker { display: none; }

/* ── Breadcrumbs ──────────────────────────────────────────────────── */
.ddr-breadcrumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  padding: 6px 0;
}
.ddr-breadcrumb-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  padding: 3px 8px;
  border-radius: 6px;
  transition: all 0.15s;
}
.ddr-breadcrumb-item:hover {
  background: var(--ddr-bg-subtle);
  color: var(--clm-primary);
}
.ddr-breadcrumb-current {
  color: var(--clm-text);
  font-weight: 600;
}

/* ── Main content ──────────────────────────────────────────────────── */
.ddr-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* ── Toolbar ───────────────────────────────────────────────────────── */
.ddr-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.ddr-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.ddr-toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ddr-search {
  position: relative;
  flex: 1;
  min-width: 140px;
  max-width: 260px;
}
.ddr-search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 15px;
  height: 15px;
  color: #9ca3af;
  pointer-events: none;
}
.ddr-search-input {
  width: 100%;
  padding: 7px 12px 7px 32px;
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius);
  background: var(--ddr-bg-subtle);
  font-size: 12px;
  color: var(--clm-text);
  outline: none;
  transition: all 0.2s;
}
.ddr-search-input:focus {
  border-color: var(--clm-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--clm-primary) 12%, transparent);
}

.ddr-select {
  padding: 7px 10px;
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius);
  background: var(--ddr-bg-subtle);
  font-size: 12px;
  color: var(--clm-text);
  outline: none;
  cursor: pointer;
}

.ddr-view-toggle {
  display: flex;
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius);
  overflow: hidden;
}
.ddr-view-btn {
  padding: 6px 8px;
  color: #9ca3af;
  transition: all 0.15s;
}
.ddr-view-active {
  background: var(--clm-primary);
  color: white;
}

/* ── Shared components ─────────────────────────────────────────────── */
.ddr-card {
  background: var(--ddr-bg-card);
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius-lg);
}
.ddr-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius);
  background: var(--ddr-bg-card);
  font-size: 13px;
  color: var(--clm-text);
  outline: none;
  transition: all 0.2s;
}
.ddr-input:focus {
  border-color: var(--clm-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--clm-primary) 12%, transparent);
}
.ddr-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: var(--clm-primary, #0284c7);
  color: white;
  font-weight: 600;
  border-radius: var(--ddr-radius);
  transition: all 0.2s;
}
.ddr-btn-primary:hover { filter: brightness(1.1); }
.ddr-btn-primary:disabled { opacity: 0.4; pointer-events: none; }
.ddr-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  color: #6b7280;
  font-weight: 500;
  border-radius: var(--ddr-radius);
  transition: all 0.15s;
}
.ddr-btn-ghost:hover { background: var(--ddr-bg-subtle); }
.ddr-btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #fef2f2;
  color: #dc2626;
  font-weight: 600;
  border-radius: var(--ddr-radius);
  transition: all 0.15s;
}
.ddr-btn-danger:hover { background: #fee2e2; }

.ddr-icon-btn {
  padding: 6px;
  border-radius: 8px;
  color: #6b7280;
  transition: all 0.15s;
}
.ddr-icon-btn:hover { background: var(--ddr-bg-subtle); }
.ddr-icon-btn:disabled { opacity: 0.3; pointer-events: none; }

.ddr-checkbox {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1.5px solid #d1d5db;
  accent-color: var(--clm-primary);
  cursor: pointer;
}

/* ── File grid ─────────────────────────────────────────────────────── */
.ddr-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}
.ddr-file-card {
  background: var(--ddr-bg-card);
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius-lg);
  overflow: hidden;
  cursor: grab;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.ddr-file-card:active { cursor: grabbing; }
.ddr-file-card:hover {
  border-color: color-mix(in srgb, var(--clm-primary) 40%, transparent);
  box-shadow: 0 4px 12px -2px rgba(0,0,0,0.08), 0 2px 6px -2px rgba(0,0,0,0.04);
  transform: translateY(-2px);
}
.ddr-file-thumb {
  position: relative;
  height: 120px;
  background: var(--ddr-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.ddr-file-info {
  padding: 10px 12px 12px;
}
.ddr-file-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}
.ddr-file-card:hover .ddr-file-actions { opacity: 1; }
.ddr-file-action {
  padding: 4px;
  border-radius: 6px;
  color: #9ca3af;
  transition: all 0.15s;
}
.ddr-file-action:hover { background: var(--ddr-bg-subtle); color: #6b7280; }
.ddr-file-action-danger:hover { background: #fef2f2; color: #ef4444; }

/* ── File list ─────────────────────────────────────────────────────── */
.ddr-list {
  background: var(--ddr-bg-card);
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius-lg);
  overflow: hidden;
}
.ddr-list-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  background: var(--ddr-bg-subtle);
  border-bottom: 1px solid var(--ddr-border);
}
.ddr-list-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--ddr-border) 50%, transparent);
  transition: background 0.1s;
}
.ddr-list-row:last-child { border-bottom: none; }
.ddr-list-row:hover { background: var(--ddr-bg-subtle); }
.ddr-list-row-selected { background: color-mix(in srgb, var(--clm-primary) 5%, transparent); }

/* ── Upload tray ───────────────────────────────────────────────────── */
.ddr-upload-tray {
  background: var(--ddr-bg-card);
  border: 1px solid var(--ddr-border);
  border-radius: var(--ddr-radius-lg);
  overflow: hidden;
}
.ddr-upload-tray-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--ddr-border) 50%, transparent);
}
.ddr-upload-tray-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--ddr-bg-subtle);
  color: #6b7280;
  transition: all 0.3s;
}
.ddr-upload-tray-icon.ddr-uploading {
  background: color-mix(in srgb, var(--clm-primary) 12%, transparent);
  color: var(--clm-primary);
}
.ddr-upload-tray-body {
  max-height: 200px;
  overflow-y: auto;
  padding: 4px 0;
}

.ddr-queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  transition: background 0.1s;
}
.ddr-queue-item:hover { background: var(--ddr-bg-subtle); }
.ddr-queue-icon {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ddr-queue-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--clm-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.ddr-queue-size {
  font-size: 11px;
  color: #9ca3af;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.ddr-queue-remove {
  padding: 2px;
  border-radius: 4px;
  color: #d1d5db;
  opacity: 0;
  transition: all 0.15s;
}
.group\/qi:hover .ddr-queue-remove { opacity: 1; }
.ddr-queue-remove:hover { color: #ef4444; background: #fef2f2; }

.ddr-progress-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
}
.ddr-progress-icon {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ddr-progress-icon.ddr-done {
  background: #ecfdf5;
  color: #10b981;
}
.ddr-progress-icon.ddr-active {
  background: color-mix(in srgb, var(--clm-primary) 12%, transparent);
  color: var(--clm-primary);
}
.ddr-progress-bar {
  width: 80px;
  height: 4px;
  border-radius: 4px;
  background: #e5e7eb;
  overflow: hidden;
  flex-shrink: 0;
}
.ddr-progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease-out;
}
.ddr-fill-done { background: #10b981; }
.ddr-fill-active { background: var(--clm-primary); }
.ddr-progress-pct {
  font-size: 11px;
  font-weight: 600;
  width: 32px;
  text-align: right;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* ── Upload zone ───────────────────────────────────────────────────── */
.ddr-upload-zone {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border: 1.5px dashed #d1d5db;
  border-radius: var(--ddr-radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}
.ddr-upload-zone:hover {
  border-color: var(--clm-primary);
  background: color-mix(in srgb, var(--clm-primary) 4%, transparent);
}
.ddr-upload-zone-active {
  border-color: var(--clm-primary);
  background: color-mix(in srgb, var(--clm-primary) 6%, transparent);
}
.ddr-upload-zone-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--ddr-bg-subtle);
  color: #9ca3af;
  transition: all 0.2s;
}
.ddr-upload-zone:hover .ddr-upload-zone-icon {
  background: color-mix(in srgb, var(--clm-primary) 12%, transparent);
  color: var(--clm-primary);
}
.ddr-upload-zone-icon.ddr-uploading {
  background: color-mix(in srgb, var(--clm-primary) 12%, transparent);
  color: var(--clm-primary);
}

/* ── Empty states ──────────────────────────────────────────────────── */
.ddr-empty-state {
  padding: 60px 20px;
  text-align: center;
  border: 2px dashed var(--ddr-border);
  border-radius: var(--ddr-radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}
.ddr-empty-state:hover {
  border-color: var(--clm-primary);
  background: color-mix(in srgb, var(--clm-primary) 3%, transparent);
}
.ddr-empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--ddr-bg-subtle);
  border: 1px solid var(--ddr-border);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  color: #d1d5db;
  transition: all 0.2s;
}
.ddr-empty-state:hover .ddr-empty-icon {
  color: var(--clm-primary);
  background: color-mix(in srgb, var(--clm-primary) 8%, transparent);
  border-color: color-mix(in srgb, var(--clm-primary) 20%, transparent);
}
.ddr-no-folder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}
.ddr-files-area {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Drop overlay ──────────────────────────────────────────────────── */
.ddr-drop-overlay {
  border: 2px dashed var(--clm-primary);
  border-radius: var(--ddr-radius-lg);
  background: color-mix(in srgb, var(--clm-primary) 5%, transparent);
  backdrop-filter: blur(4px);
  padding: 48px 20px;
}
.ddr-drop-inner {
  text-align: center;
}

/* ── Transitions ───────────────────────────────────────────────────── */
.preview-slide-enter-active,
.preview-slide-leave-active { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.preview-slide-enter-from,
.preview-slide-leave-to { transform: translateX(100%); }

.preview-backdrop-enter-active,
.preview-backdrop-leave-active { transition: opacity 0.25s ease; }
.preview-backdrop-enter-from,
.preview-backdrop-leave-to { opacity: 0; }

.drop-overlay-enter-active,
.drop-overlay-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.drop-overlay-enter-from,
.drop-overlay-leave-to { opacity: 0; transform: scale(0.97); }

.tray-slide-enter-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.tray-slide-leave-active { transition: all 0.2s ease; }
.tray-slide-enter-from,
.tray-slide-leave-to { opacity: 0; transform: translateY(-8px); }

.fade-scale-enter-active,
.fade-scale-leave-active { transition: all 0.2s ease; }
.fade-scale-enter-from,
.fade-scale-leave-to { opacity: 0; transform: scale(0.95); }

.modal-fade-enter-active { transition: opacity 0.2s ease; }
.modal-fade-leave-active { transition: opacity 0.15s ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }

.file-card-enter-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.file-card-leave-active { transition: all 0.2s ease; }
.file-card-enter-from { opacity: 0; transform: scale(0.9); }
.file-card-leave-to { opacity: 0; transform: scale(0.9); }
.file-card-move { transition: transform 0.3s ease; }

.file-row-enter-active { transition: all 0.25s ease; }
.file-row-leave-active { transition: all 0.15s ease; }
.file-row-enter-from { opacity: 0; transform: translateX(-8px); }
.file-row-leave-to { opacity: 0; transform: translateX(8px); }
.file-row-move { transition: transform 0.3s ease; }

.folder-item-enter-active { transition: all 0.25s ease; }
.folder-item-leave-active { transition: all 0.15s ease; }
.folder-item-enter-from { opacity: 0; transform: translateY(-4px); }
.folder-item-leave-to { opacity: 0; height: 0; padding: 0; margin: 0; overflow: hidden; }
.folder-item-move { transition: transform 0.25s ease; }

@keyframes modal-in {
  from { opacity: 0; transform: scale(0.95) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.animate-modal-in { animation: modal-in 0.2s ease-out; }

/* ── Chunks toggle button ──────────────────────────────────────────── */
.ddr-chunks-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 8px;
  color: #6b7280;
  font-weight: 500;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.ddr-chunks-toggle:hover {
  background: var(--ddr-bg-subtle);
  color: var(--clm-primary);
}
.ddr-chunks-toggle-active {
  background: color-mix(in srgb, var(--clm-primary) 8%, transparent);
  border-color: color-mix(in srgb, var(--clm-primary) 20%, transparent);
  color: var(--clm-primary);
}
.ddr-chunks-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--clm-primary);
  color: white;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

/* ── Split layout ──────────────────────────────────────────────────── */
.ddr-split-container {
  display: flex;
  position: relative;
  min-height: 0;
}
.ddr-preview-pane {
  flex: 1;
  min-width: 0;
  overflow: auto;
  background: #fff;
}

/* ── PDF.js rendering ──────────────────────────────────────────────── */
.ddr-pdf-scroll {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #f3f4f6;
}
.ddr-pdf-pages {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 12px;
}
.ddr-pdf-page {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.10);
  overflow: hidden;
}
.ddr-pdf-page canvas {
  display: block;
}
:deep(.ddr-chunk-hl) {
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.11) 0%, rgba(37, 99, 235, 0.16) 100%) !important;
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.22);
  border-radius: 4px;
  padding: 0.08em 0.14em;
  outline: none !important;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
  color: transparent;
}

/* ── Chunks drawer ─────────────────────────────────────────────────── */
.ddr-chunks-drawer {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--ddr-border);
  background: var(--ddr-bg-card);
  box-shadow: -4px 0 24px -8px rgba(0, 0, 0, 0.06);
}
.ddr-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--ddr-border);
  flex-shrink: 0;
  background: var(--ddr-bg-subtle);
}
.ddr-drawer-header-stacked {
  flex-direction: column;
  align-items: stretch;
}
.ddr-chunk-hl-option {
  user-select: none;
}
.ddr-drawer-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}
.ddr-drawer-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ── Chunk cards ───────────────────────────────────────────────────── */
.ddr-chunk-card {
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
  border: 1px solid transparent;
  border-left: 3px solid transparent;
}
.ddr-chunk-card:hover {
  background: var(--ddr-bg-subtle);
  border-color: var(--ddr-border);
  border-left-color: var(--ddr-border);
}
.ddr-chunk-active {
  background: color-mix(in srgb, var(--clm-primary) 5%, transparent) !important;
  border-color: color-mix(in srgb, var(--clm-primary) 20%, transparent) !important;
  border-left-color: var(--clm-primary) !important;
}
.ddr-chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 8px 10px;
  width: 100%;
  text-align: left;
}
.ddr-chunk-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 20px;
  padding: 0 5px;
  border-radius: 5px;
  background: color-mix(in srgb, var(--clm-primary) 10%, transparent);
  color: var(--clm-primary);
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}
.ddr-chunk-active .ddr-chunk-index {
  background: var(--clm-primary);
  color: #fff;
}
.ddr-chunk-body {
  padding: 0 10px 10px;
}
.ddr-chunk-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 11px;
  line-height: 1.65;
  color: var(--clm-text);
  background: var(--ddr-bg-subtle);
  border: 1px solid color-mix(in srgb, var(--ddr-border) 50%, transparent);
  border-radius: 6px;
  padding: 10px 12px;
  max-height: 220px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
}

/* ── Eye button ────────────────────────────────────────────────────── */
.ddr-eye-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  color: #9ca3af;
  transition: all 0.2s;
  flex-shrink: 0;
}
.ddr-eye-btn:hover {
  background: color-mix(in srgb, var(--clm-primary) 10%, transparent);
  color: var(--clm-primary);
  transform: scale(1.1);
}
.ddr-eye-btn-active {
  background: var(--clm-primary) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px -2px color-mix(in srgb, var(--clm-primary) 40%, transparent);
}

.ddr-expand-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  color: #d1d5db;
  transition: all 0.15s;
}
.ddr-expand-toggle:hover { color: #9ca3af; background: rgba(0,0,0,0.04); }

.ddr-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--clm-primary);
  padding: 3px 8px;
  border-radius: 5px;
  transition: all 0.15s;
}
.ddr-copy-btn:hover { background: color-mix(in srgb, var(--clm-primary) 8%, transparent); }

/* ── Drawer transition ─────────────────────────────────────────────── */
.drawer-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-enter-from {
  opacity: 0;
  transform: translateX(40px);
  width: 0 !important;
  min-width: 0 !important;
}
.drawer-slide-leave-to {
  opacity: 0;
  transform: translateX(40px);
  width: 0 !important;
  min-width: 0 !important;
}

.chunk-expand-enter-active { transition: all 0.25s ease; }
.chunk-expand-leave-active { transition: all 0.15s ease; }
.chunk-expand-enter-from,
.chunk-expand-leave-to { opacity: 0; max-height: 0; padding-top: 0; padding-bottom: 0; }

.ddr-bg-task-banner-enter-active,
.ddr-bg-task-banner-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.ddr-bg-task-banner-enter-from,
.ddr-bg-task-banner-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
