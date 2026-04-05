// Minimal plans page client logic
(function () {
    window.plansPage = function () {
        return {
            // Data arrays (PlansResponse)
            submitted: [],
            inProgress: [],
            pending: [],
            completed: [],
            failed: [],
            expired: [],
            postponed: [],
            canceled: [],
            deleted: [],

            canManagePlans:  false,
            canSubmitPlans:  false,
            canExecutePlans: false,
            currentUserUid:  null,
            activeTab:       'pending',

            // ── scraping data (populated from PlansResponse.scraping_results) ─
            availableOwners:          [],   // [{name, uuid}]
            availableClassifications: [],   // list[str]
            availableUnits:           [],   // list[str]

            // ── per-tab filter state ─────────────────────────────────────────
            // Each entry: { open, active, criteria: { approved, autofocus, too,
            //   owners, classifications, units, meritOp, meritVal,
            //   timeFrom, timeTo } }
            _mkFilter() {
                return {
                    open: false,
                    criteria: {
                        approved:        { enabled: false, value: true },
                        autofocus:       { enabled: false, value: true },
                        too:             { enabled: false, value: true },
                        notValid:        { enabled: false },
                        owners:          { enabled: false, values: [] },
                        classifications: { enabled: false, values: [] },
                        units:           { enabled: false, values: [] },
                        merit:           { enabled: false, op: '>=', val: 1 },
                        timeFrom:        { enabled: false, value: '' },
                        timeTo:          { enabled: false, value: '' },
                    },
                };
            },
            filters: {},    // keyed by tab name, populated in init()

            // ── per-tab selection state ──────────────────────────────────────
            selected: {},   // keyed by tab name → Array of ulids

            ownerName(uid) {
                if (!uid) return 'n/a';
                const o = ((window.__PLANS_INIT || {}).owners || {})[uid];
                return o ? o.name : uid;
            },
            ownerUrl(uid) {
                if (!uid) return '#';
                const o = ((window.__PLANS_INIT || {}).owners || {})[uid];
                return o ? o.url : '#';
            },

            init() {
                // initialize capability from server-provided object
                try {
                    this.canManagePlans  = window.__PLANS_INIT && window.__PLANS_INIT.canManagePlans  === true;
                    this.canSubmitPlans  = window.__PLANS_INIT && window.__PLANS_INIT.canSubmitPlans  === true;
                    this.canExecutePlans = window.__PLANS_INIT && window.__PLANS_INIT.canExecutePlans === true;
                    this.currentUserUid  = (window.__PLANS_INIT || {}).currentUserUid || null;
                } catch (e) {
                    this.canManagePlans = false;
                    this.canSubmitPlans = false;
                }
                // Pre-populate filter options from server-embedded scraping results
                const sr = (window.__PLANS_INIT || {}).scrapingResults || {};
                this.availableOwners          = sr.owners               || [];
                this.availableClassifications = sr.known_classifications || sr.classifications || [];
                this.availableUnits           = sr.requested_units       || [];

                const TABS = ['submitted','pending','completed','postponed','expired','failed','canceled','deleted'];
                TABS.forEach(t => {
                    this.filters[t]  = this._mkFilter();
                    this.selected[t] = [];
                });
                // track active tab for funnel visibility
                document.getElementById('plansTabs')?.addEventListener('shown.bs.tab', (e) => {
                    const target = e.target.getAttribute('data-bs-target') || '';
                    this.activeTab = target.replace('#pane-', '');
                });
                this.fetchPlans();
            },

            async fetchPlans() {
                try {
                    console.log('Fetching plans...');
                    const r = await ControlApi('/plans/get');
                    const data = await r;
                    console.log('Plans data received:', data);
                    // Expect data shaped like PlansResponse
                    this.submitted = data.submitted || [];
                    this.inProgress = data.in_progress || data.inProgress || [];
                    this.pending = data.pending || [];
                    this.completed = data.completed || [];
                    this.failed = data.failed || [];
                    this.expired = data.expired || [];
                    this.postponed = data.postponed || [];
                    this.canceled = data.canceled || [];
                    this.deleted = data.deleted || [];
                    this.inProgress.forEach(p => p._tab = this.findTabForUlid(p.ulid));

                    // refresh scraping data from live API response
                    const sr = data.scraping_results || {};
                    if (sr.owners)                                        this.availableOwners          = sr.owners;
                    if (sr.known_classifications || sr.classifications)   this.availableClassifications = sr.known_classifications || sr.classifications;
                    if (sr.requested_units)                               this.availableUnits           = sr.requested_units;

                    // reset selection on every load
                    Object.keys(this.selected).forEach(t => this.selected[t] = []);
                } catch (err) {
                    console.error('Failed to fetch plans:', err);
                    this.submitted = this.inProgress = this.pending = this.completed = this.failed = this.expired = this.postponed = this.canceled = this.deleted = [];
                }
            },

            /**
             * Render a collapsible JSON tree into element `el` for object `obj`.
             * Called from the template via x-init="renderJsonTree($el, p)".
             */
            renderJsonTree(el, obj) {
                // clear
                el.innerHTML = '';
                try {
                    const root = this._createTreeNode(null, obj);
                    el.appendChild(root);
                } catch (e) {
                    // fallback to preformatted JSON
                    const pre = document.createElement('pre');
                    pre.textContent = JSON.stringify(obj, null, 2);
                    el.appendChild(pre);
                }
            },

            _createTreeNode(key, value) {
                const wrapper = document.createElement('div');
                wrapper.className = 'json-node';

                const isObj = value && typeof value === 'object' && !Array.isArray(value);
                const isArr = Array.isArray(value);

                if (isObj || isArr) {
                    // collapsible node
                    const header = document.createElement('div');
                    header.style.display = 'flex';
                    header.style.alignItems = 'center';

                    const toggle = document.createElement('span');
                    toggle.className = 'json-toggle';
                    toggle.tabIndex = 0;
                    toggle.textContent = '▸'; // closed

                    const keySpan = document.createElement('span');
                    keySpan.className = 'json-key';
                    keySpan.textContent = key !== null ? key + ': ' : '';

                    const typeSpan = document.createElement('span');
                    typeSpan.className = 'json-type';
                    typeSpan.textContent = isArr ? `[${value.length}]` : '{ }';

                    header.appendChild(toggle);
                    header.appendChild(keySpan);
                    header.appendChild(typeSpan);

                    const children = document.createElement('div');
                    children.className = 'json-children';
                    // populate children
                    if (isArr) {
                        for (let i = 0; i < value.length; i++) {
                            children.appendChild(this._createTreeNode(i, value[i]));
                        }
                    } else {
                        for (const k of Object.keys(value)) {
                            children.appendChild(this._createTreeNode(k, value[k]));
                        }
                    }

                    // initial collapsed
                    const container = document.createElement('div');
                    container.className = 'json-collapsed';
                    container.appendChild(header);
                    container.appendChild(children);

                    const toggleFn = () => {
                        const opened = toggle.textContent === '▾';
                        toggle.textContent = opened ? '▸' : '▾';
                        if (container.classList.contains('json-collapsed')) {
                            container.classList.remove('json-collapsed');
                        } else {
                            container.classList.add('json-collapsed');
                        }
                    };
                    toggle.addEventListener('click', toggleFn);
                    toggle.addEventListener('keydown', (ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); toggleFn(); }
                    });

                    wrapper.appendChild(container);
                } else {
                    // leaf node
                    const line = document.createElement('div');
                    const k = document.createElement('span');
                    k.className = 'json-key';
                    k.textContent = key !== null ? (key + ': ') : '';
                    const v = document.createElement('span');
                    const t = typeof value;
                    v.className = 'json-value ' + (t === 'string' ? 'string' : t === 'number' ? 'number' : t === 'boolean' ? 'boolean' : '');
                    v.textContent = (value === null) ? 'null' : String(value);
                    line.appendChild(k);
                    line.appendChild(v);
                    wrapper.appendChild(line);
                }
                return wrapper;
            },

            // Attempt to locate the tab that contains a given ULID
            findTabForUlid(ulid) {
                // search arrays
                if ((this.submitted || []).some(p => p.ulid === ulid)) return 'submitted';
                if ((this.pending || []).some(p => p.ulid === ulid)) return 'pending';
                if ((this.completed || []).some(p => p.ulid === ulid)) return 'completed';
                if ((this.postponed || []).some(p => p.ulid === ulid)) return 'postponed';
                if ((this.expired || []).some(p => p.ulid === ulid)) return 'expired';
                if ((this.failed || []).some(p => p.ulid === ulid)) return 'failed';
                if ((this.canceled || []).some(p => p.ulid === ulid)) return 'canceled';
                if ((this.deleted || []).some(p => p.ulid === ulid)) return 'deleted';
                return 'pending';
            },

            // ── plan validation ──────────────────────────────────────────────

            planErrors(p) {
                const meta = (window.__PLANS_INIT || {}).fieldMeta || {};
                const ctx = { ...planCardsMixin(), plan: p, openCards: {} };
                const cards = ctx._buildCards.call(ctx, meta);
                const errors = [];
                for (const card of cards) {
                    for (const field of card.fields) {
                        if (field._isSectionHeader || !field.required) continue;
                        const v = ctx.getFieldValue.call(ctx, card.key, field.name, field._groupKey);
                        if (v === null || v === undefined || v === '')
                            errors.push(`<span style="font-weight:700;font-style:italic">${field.label}</span> is required`);
                    }
                }
                return errors;
            },

            planValid(p) { return this.planErrors(p).length === 0; },

            planValidTooltip(p) {
                const errs = this.planErrors(p);
                return errs.length
                    ? '<ul class="mb-0 ps-3">' + errs.map(e => `<li>${e}</li>`).join('') + '</ul>'
                    : 'Valid';
            },

            isOwner(plan) {
                return this.currentUserUid && plan.owner === this.currentUserUid;
            },

            editPlan(ulid) {
                const base = ((window.__PLANS_INIT || {}).editPlanUrl || '').replace('ULID_PLACEHOLDER', ulid);
                window.location.href = base;
            },

            // ── low-level plan API call (all transition endpoints accept a JSON array of ulids) ──
            _planPost(endpoint, ulids) {
                return ControlApi(`/plans/${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ulids),
                });
            },
            _planDelete(endpoint, ulids) {
                return ControlApi(`/plans/${endpoint}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ulids),
                });
            },

            // Helpers to perform actions, then refresh
            async executePlan(ulid) {
                if (!confirm('Execute plan ' + ulid + '?')) return;
                try { await this._planPost('execute', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async approvePlan(ulid) {
                if (!confirm('Approve plan ' + ulid + '?')) return;
                try { await this._planPost('revive', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async revivePlan(ulid) {
                if (!confirm('Revive plan ' + ulid + '?')) return;
                try { await this._planPost('revive', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async postponePlan(ulid) {
                if (!confirm('Postpone plan ' + ulid + '?')) return;
                try { await this._planPost('postpone', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async cancelPlan(ulid) {
                if (!confirm('Cancel plan ' + ulid + '?')) return;
                try { await this._planPost('cancel', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async deletePlan(ulid) {
                if (!confirm('Delete plan ' + ulid + '? This cannot be undone.')) return;
                try { await this._planDelete('delete', [ulid]); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            // When an in-progress plan link is clicked: switch tab and open accordion
            selectPlan(ulid, tab) {
                try {
                    // activate tab via Bootstrap
                    const tabBtn = document.querySelector(`#tab-${tab}`);
                    if (tabBtn) {
                        // use Bootstrap's Tab API if available
                        if (window.bootstrap && bootstrap.Tab) {
                            const bsTab = new bootstrap.Tab(tabBtn);
                            bsTab.show();
                        } else {
                            tabBtn.click();
                        }
                    }
                    // after the tab is visible, try to expand accordion entry
                    requestAnimationFrame(() => {
                        // find any element in DOM with data-plan-ulid matching
                        const selector = `[data-plan-ulid="${ulid}"]`;
                        const item = document.querySelector(selector);
                        if (!item) {
                            // maybe the ULID has characters used in id - fallback search
                            const els = document.querySelectorAll('[data-plan-ulid]');
                            for (let e of els) {
                                if (e.getAttribute('data-plan-ulid') === ulid) { item = e; break; }
                            }
                        }
                        if (!item) return;
                        // find the collapse target inside the accordion-item
                        const collapse = item.querySelector('.accordion-collapse');
                        if (collapse && !collapse.classList.contains('show')) {
                            try {
                                if (window.bootstrap && bootstrap.Collapse) {
                                    new bootstrap.Collapse(collapse, { show: true });
                                } else {
                                    collapse.classList.add('show');
                                }
                            } catch (e) {
                                collapse.classList.add('show');
                            }
                        }
                        // scroll into view
                        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    });
                } catch (e) {
                    console.warn('selectPlan error', e);
                }
            },

            // Formatting helper for JSON display (kept for fallback/debug)
            formatJSON(obj) {
                try {
                    return JSON.stringify(obj, null, 2);
                } catch (e) {
                    return String(obj);
                }
            },

            // helper used when building in-progress links if tab unknown
            getTabForPlan(p) {
                return this.findTabForUlid(p.ulid);
            },

            // ── filtering ────────────────────────────────────────────────────

            filteredPlans(tab) {
                const list = this[tab] || [];
                const f = (this.filters[tab] || {}).criteria;
                if (!f) return list;
                return list.filter(p => this._matchesCriteria(p, f));
            },

            isFiltered(tab) {
                const f = (this.filters[tab] || {}).criteria;
                if (!f) return false;
                return Object.values(f).some(c => c.enabled);
            },

            clearFilter(tab) {
                this.filters[tab] = this._mkFilter();
                this.selected[tab] = [];
            },

            _matchesCriteria(p, f) {
                // Boolean: approved / autofocus / too
                for (const key of ['approved', 'autofocus', 'too']) {
                    const c = f[key];
                    if (!c.enabled) continue;
                    if (!!p[key] !== c.value) return false;
                }
                // Not valid
                if (f.notValid?.enabled) {
                    if (this.planValid(p)) return false;
                }
                // Owner
                if (f.owners.enabled && f.owners.values.length) {
                    if (!f.owners.values.includes(p.owner)) return false;
                }
                // Classification
                if (f.classifications.enabled && f.classifications.values.length) {
                    const cls = p.target?.science?.classification || null;
                    if (!f.classifications.values.includes(cls)) return false;
                }
                // Requested units (any match)
                if (f.units.enabled && f.units.values.length) {
                    const ru = p.requested_units || [];
                    if (!f.units.values.some(u => ru.includes(u))) return false;
                }
                // Merit
                if (f.merit.enabled) {
                    const m = p.merit ?? null;
                    if (m === null) return false;
                    const v = Number(f.merit.val);
                    if (f.merit.op === '>=' && !(m >= v)) return false;
                    if (f.merit.op === '<=' && !(m <= v)) return false;
                    if (f.merit.op === '='  && !(m === v)) return false;
                }
                // Time window overlap
                const tw = p.constraints?.time_window;
                if (f.timeFrom.enabled && f.timeFrom.value) {
                    const filterFrom = new Date(f.timeFrom.value);
                    const planEnd    = tw?.end   ? new Date(tw.end)   : null;
                    // plan ends before filter starts → no overlap
                    if (planEnd && planEnd < filterFrom) return false;
                    // plan has no end and no start (open-ended) → include
                }
                if (f.timeTo.enabled && f.timeTo.value) {
                    const filterTo   = new Date(f.timeTo.value);
                    const planStart  = tw?.start ? new Date(tw.start) : null;
                    // plan starts after filter ends → no overlap
                    if (planStart && planStart > filterTo) return false;
                }
                return true;
            },

            // ── selection ────────────────────────────────────────────────────

            isSelected(tab, ulid)    { return (this.selected[tab] || []).includes(ulid); },
            selectedCount(tab)       { return (this.selected[tab] || []).length; },
            anySelected(tab)         {
                return this.selectedCount(tab) > 0 ||
                       (this.isFiltered(tab) && this.filteredPlans(tab).length > 0);
            },
            // Returns ulids to act on: explicit selection, or all filtered plans as fallback
            _targetUlids(tab) {
                const manual = this.selected[tab] || [];
                if (manual.length > 0) return manual;
                if (this.isFiltered(tab)) return this.filteredPlans(tab).map(p => p.ulid);
                return [];
            },

            toggleSelect(tab, ulid) {
                const arr = this.selected[tab] || [];
                const idx = arr.indexOf(ulid);
                if (idx >= 0) arr.splice(idx, 1); else arr.push(ulid);
                this.selected[tab] = [...arr]; // new array reference triggers Alpine reactivity
            },

            // master checkbox: null=indeterminate, true=all, false=none
            masterCheckState(tab) {
                const filtered = this.filteredPlans(tab);
                const n = filtered.filter(p => this.isSelected(tab, p.ulid)).length;
                if (n === 0) return false;
                if (n === filtered.length) return true;
                return null; // indeterminate
            },

            toggleMaster(tab) {
                const filtered = this.filteredPlans(tab);
                const state    = this.masterCheckState(tab);
                const cur      = new Set(this.selected[tab] || []);
                if (state === true) {
                    filtered.forEach(p => cur.delete(p.ulid));
                } else {
                    filtered.forEach(p => cur.add(p.ulid));
                }
                this.selected[tab] = [...cur];
            },

            // ── bulk actions ─────────────────────────────────────────────────

            async bulkApprove(tab) {
                const ulids = this._targetUlids(tab);
                if (!ulids.length) return;
                if (!confirm(`Approve ${ulids.length} plan(s)?`)) return;
                try { await this._planPost('revive', ulids); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async bulkPostpone(tab) {
                const ulids = this._targetUlids(tab);
                if (!ulids.length) return;
                if (!confirm(`Postpone ${ulids.length} plan(s)?`)) return;
                try { await this._planPost('postpone', ulids); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async bulkRevive(tab) {
                const ulids = this._targetUlids(tab);
                if (!ulids.length) return;
                if (!confirm(`Revive ${ulids.length} plan(s)?`)) return;
                try { await this._planPost('revive', ulids); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async bulkDelete(tab) {
                const ulids = this._targetUlids(tab);
                if (!ulids.length) return;
                if (!confirm(`Delete ${ulids.length} plan(s)? This cannot be undone.`)) return;
                try { await this._planDelete('delete', ulids); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async bulkCancel(tab) {
                const ulids = this._targetUlids(tab);
                if (!ulids.length) return;
                if (!confirm(`Cancel ${ulids.length} plan(s)?`)) return;
                try { await this._planPost('cancel', ulids); } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },
        };
    };
    // If Alpine is not used, expose a global helper for manual calls
    window.plansPageSelect = function (ulid, tab) {
        try {
            const comp = document.querySelector('[x-data="plansPage()"]');
            if (!comp) return;
            const scope = comp.__x ? comp.__x.$data : (window._plansPageInstance || null);
            if (scope && typeof scope.selectPlan === 'function') scope.selectPlan(ulid, tab);
        } catch (e) { console.warn(e); }
    };
})();
