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

            canManagePlans: false,
            canSubmitPlans: false,
            currentUserUid: null,

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
                    this.canManagePlans = window.__PLANS_INIT && window.__PLANS_INIT.canManagePlans === true;
                    this.canSubmitPlans = window.__PLANS_INIT && window.__PLANS_INIT.canSubmitPlans === true;
                    this.currentUserUid = (window.__PLANS_INIT || {}).currentUserUid || null;
                } catch (e) {
                    this.canManagePlans = false;
                    this.canSubmitPlans = false;
                }
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
                    // attach a helper _tab for inProgress entries if needed
                    this.inProgress.forEach(p => p._tab = this.findTabForUlid(p.ulid));
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

            // Helpers to perform actions, then refresh
            async executePlan(ulid) {
                if (!confirm('Execute plan ' + ulid + '?')) return;
                try {
                    await ControlApi(`/plans/execute?ulid=${encodeURIComponent(ulid)}`, { method: 'POST' });
                } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async approvePlan(ulid) {
                if (!confirm('Approve plan ' + ulid + '?')) return;
                try {
                    await ControlApi(`/plans/revive?ulid=${encodeURIComponent(ulid)}`, { method: 'POST' });
                } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async revivePlan(ulid) {
                if (!confirm('Revive plan ' + ulid + '?')) return;
                try {
                    await ControlApi(`/plans/revive?ulid=${encodeURIComponent(ulid)}`, { method: 'POST' });
                } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async postponePlan(ulid) {
                if (!confirm('Postpone plan ' + ulid + '?')) return;
                try {
                    await ControlApi(`/plans/postpone?ulid=${encodeURIComponent(ulid)}`, { method: 'POST' });
                } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async cancelPlan(ulid) {
                if (!confirm('Cancel plan ' + ulid + '?')) return;
                try {
                    await ControlApi(`/plans/cancel?ulid=${encodeURIComponent(ulid)}`, { method: 'POST' });
                } catch (e) { console.warn(e); }
                await this.fetchPlans();
            },

            async deletePlan(ulid) {
                if (!confirm('Delete plan ' + ulid + '? This cannot be undone.')) return;
                try {
                    await ControlApi(`/plans/delete?ulid=${encodeURIComponent(ulid)}`, { method: 'DELETE' });
                } catch (e) { console.warn(e); }
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
            }
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
