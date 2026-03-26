(function () {
    window.planNewPage = function () {
        return {
            ...planCardsMixin(),
            ...formValidationMixin(),

            loading: true,
            error: null,

            // plan data (from get_new_plan)
            plan: null,
            initialPlan: null,
            specDefaults: {},
            filter_options: [],

            // UI state
            cardErrors: {},   // { cardKey: string|null }

            async init() {
                const init = window.__PLAN_NEW_INIT || {};
                const meta = init.fieldMeta || {};
                const editUlid = init.editUlid || '';
                try {
                    let data;
                    if (editUlid) {
                        const plans = await ControlApi('/plans/get');
                        const all = [
                            ...(plans.submitted || []), ...(plans.pending || []),
                            ...(plans.in_progress || []), ...(plans.completed || []),
                            ...(plans.postponed || []), ...(plans.failed || []),
                            ...(plans.expired || []),
                        ];
                        data = all.find(p => p.ulid === editUlid) || null;
                        if (!data) throw new Error(`Plan ${editUlid} not found`);
                    } else {
                        data = await ControlApi('/plans/new');
                        if (!data) throw new Error('Backend returned no data — check console for details');
                        this.specDefaults = data.spec_defaults || {};
                        this.filter_options = data.filter_options || [];
                        if (data.owner == null)
                            data.owner = init.currentUserUid || null;
                    }
                    this.plan = data;
                    this.initialPlan = JSON.parse(JSON.stringify(data));
                    this.cards = this._buildCards(meta);
                    this.cards.forEach(c => this.openCards[c.key] = false);
                } catch (e) {
                    this.error = 'Failed to load plan: ' + e;
                } finally {
                    this.loading = false;
                }
            },

            // Edit-mode overrides

            isEditable(field) {
                if (field.editable === false) return false;
                return true;
            },

            cardBorderClass(key) {
                if (this.cardErrors[key]) return 'border-danger';
                return '';
            },

            setFieldValue(cardKey, fieldName, value, groupKey) {
                if (!this.plan) return;
                // Coerce string values to number when field options are numeric
                const fieldMeta = this._findFieldMeta(cardKey, fieldName, groupKey);
                if (fieldMeta && fieldMeta.options && fieldMeta.options.length && typeof fieldMeta.options[0] === 'number' && value !== '' && value !== null) {
                    value = Number(value);
                }
                if (cardKey in this.plan && typeof this.plan[cardKey] === 'object') {
                    if (!this.plan[cardKey]) this.plan[cardKey] = {};
                    if (groupKey) {
                        if (!this.plan[cardKey][groupKey]) this.plan[cardKey][groupKey] = {};
                        this.plan[cardKey][groupKey][fieldName] = value;
                    } else {
                        this.plan[cardKey][fieldName] = value;
                    }

                } else {
                    this.plan[fieldName] = value;
                }

                this.validateByName(cardKey, fieldName, groupKey, value);
            },

            openDatePicker(cardKey, field, opt) {
                const current = this.getFieldValue(cardKey, field.name, field._groupKey);
                if (current !== opt) {
                    this.setModeValue(cardKey, field, opt);
                }
                this.$nextTick(() => {
                    const input = document.getElementById(`picker-${cardKey}-${field._uniqueName}-${opt}`);
                    if (input && input.showPicker) input.showPicker();
                });
            },

            setModeValue(cardKey, field, opt) {
                const groupKey = field._groupKey;
                const companionName = field.name.replace('_mode', '');
                this.setFieldValue(cardKey, field.name, opt, groupKey);
                this.setFieldValue(cardKey, companionName, null, groupKey);
                if (field.name === 'end_mode') {
                    this.setFieldValue(cardKey, 'end_after_nights', null, groupKey);
                }
            },

            _findFieldMeta(cardKey, fieldName, groupKey) {
                const card = this.cards.find(c => c.key === cardKey);
                if (!card) return null;
                return card.fields.find(f => f.name === fieldName && f._groupKey === groupKey) || null;
            },

            _getOriginalValue(cardKey, fieldName, groupKey) {
                if (!this.initialPlan) return null;
                const card = this.initialPlan[cardKey];
                if (card && typeof card === 'object') {
                    if (groupKey) return (card[groupKey] ?? {})[fieldName] ?? null;
                    return card[fieldName] ?? null;
                }
                return this.initialPlan[fieldName] ?? null;
            },

            // Edit-mode summary: show changed fields for details/constraints
            cardSummaryItems(card) {
                const key = card.key;

                if (key === 'target') {
                    const ra = this.getFieldValue('target', 'ra_hours');
                    const dec = this.getFieldValue('target', 'dec_degrees');
                    if (ra == null || dec == null)
                        return [{ message: 'Not set' }];
                    return card.summaryFields.map(sf => ({
                        label: sf.label,
                        value: this.getFieldValue(key, sf.name, sf._groupKey),
                        unit: sf.unit,
                    }));
                }

                if (key === 'spec_assignment') {
                    const instr = this.getFieldValue('spec_assignment', 'instrument');
                    if (!instr) return [{ message: 'Not selected' }];
                    return card.summaryFields.map(sf => ({
                        label: sf.label,
                        value: this.getFieldValue(key, sf.name, sf._groupKey),
                        unit: sf.unit,
                    }));
                }

                if (key === '_details' || key === 'constraints') {
                    const changed = [];
                    for (const sf of card.fields.filter(f => !f._isSectionHeader && !f.hidden)) {
                        const current = this.getFieldValue(key, sf.name, sf._groupKey);
                        const original = this._getOriginalValue(key, sf.name, sf._groupKey);
                        if (JSON.stringify(current) !== JSON.stringify(original)) {
                            const display = (sf.widget === 'user')
                                ? (this._resolveUser(current)?.name || current)
                                : current;
                            changed.push({ label: sf.label, value: display, unit: sf.unit });
                        }
                    }
                    return changed.length ? changed : [{ message: 'Default' }];
                }

                return card.summaryFields.map(sf => ({
                    label: sf.label,
                    value: this.getFieldValue(key, sf.name, sf._groupKey),
                    unit: sf.unit,
                }));
            },

            isValid() {
                return this.isFormValid();
            },

            async submitPlan() {
                if (!this.isValid()) return;
                try {
                    const { filter_options, ...payload } = this.plan;
                    const result = await ControlApi('/plans/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    if (result === null) {
                        this.error = 'Submission failed — check browser console for details.';
                        return;
                    }
                    window.location.href = (window.__PLAN_NEW_INIT || {}).plansUrl || '/plans/';
                } catch (e) {
                    this.error = 'Submission failed: ' + e;
                }
            },
        };
    };
})();
