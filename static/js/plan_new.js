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
            filter_options: (window.__PLAN_NEW_INIT || {}).filter_options || [],

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
                        this.filter_options = data.filter_options || this.filter_options;
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

                    const name = this.getFieldValue('target', 'name');
                    const duration = this.getFieldValue('target', 'requested_exposure_duration');
                    const nExp = this.getFieldValue('target', 'requested_number_of_exposures');

                    const items = [];
                    items.push({ message: name || `(${ra}, ${dec})`, bold: true });
                    if (duration != null)
                        items.push({ message: `${duration} seconds`, plain: true });
                    if (nExp != null && nExp > 1)
                        items.push({ message: `${nExp} exposures`, plain: true });
                    return items.map((item, i) =>
                        i < items.length - 1 && item.message ? { ...item, message: item.message + ',' } : item
                    );
                }

                if (key === 'spec_assignment') {
                    const instr = this.getFieldValue('spec_assignment', 'instrument');
                    if (!instr) return [{ message: 'Not selected' }];

                    const items = [];
                    items.push({ message: instr, bold: true });

                    const lampOn = this.getFieldValue('spec_assignment', 'lamp_on', 'calibration');
                    if (lampOn) {
                        const filter = this.getFieldValue('spec_assignment', 'filter', 'calibration');
                        items.push({ message: filter ? `ThAr ${filter}` : 'ThAr', plain: true });
                    }

                    return items.map((item, i) =>
                        i < items.length - 1 && item.message ? { ...item, message: item.message + ',' } : item
                    );
                }

                if (key === '_details') {
                    const items = [];

                    const ownerUid = this.getFieldValue('_details', 'owner');
                    const ownerName = this._resolveUser(ownerUid)?.name || ownerUid;
                    if (ownerName) items.push({ message: ownerName, bold: true });

                    const merit = this.getFieldValue('_details', 'merit');
                    if (merit != null) items.push({ message: `Merit: ${merit}`, plain: true });

                    const autofocus = this.getFieldValue('_details', 'autofocus');
                    if (autofocus) items.push({ message: 'Autofocus', plain: true });

                    const units = this.getFieldValue('_details', 'requested_units');
                    const unitsList = Array.isArray(units) ? units.join(', ') : units;
                    if (unitsList) items.push({ message: unitsList, plain: true });

                    return items.length
                        ? items.map((item, i) => i < items.length - 1 ? { ...item, message: item.message + ',' } : item)
                        : [{ message: 'Default' }];
                }

                if (key === 'constraints') {
                    return this._constraintsSummaryItems();
                }

                return card.summaryFields.map(sf => ({
                    label: sf.label,
                    value: this.getFieldValue(key, sf.name, sf._groupKey),
                    unit: sf.unit,
                }));
            },

            _constraintsSummaryItems() {
                const items = [];

                // Moon
                const moonPhase = this.getFieldValue('constraints', 'max_phase', 'moon');
                const moonDist  = this.getFieldValue('constraints', 'min_distance', 'moon');
                if (moonPhase != null || moonDist != null) {
                    const parts = [];
                    if (moonPhase != null) parts.push(`${moonPhase}%`);
                    if (moonDist  != null) parts.push(`distance ${moonDist}\u00b0`);
                    items.push({ message: 'Moon', bold: true });
                    items.push({ message: parts.join(', '), plain: true });
                }

                // Airmass
                const airmass = this.getFieldValue('constraints', 'max', 'airmass');
                if (airmass != null) {
                    items.push({ message: 'Airmass', bold: true });
                    items.push({ message: String(airmass), plain: true });
                }

                // Time window — Start
                const startMode = this.getFieldValue('constraints', 'start_mode', 'time_window');
                const start     = this.getFieldValue('constraints', 'start', 'time_window');
                if (startMode && startMode !== 'Anytime' && start) {
                    items.push({ message: 'Start', bold: true });
                    items.push({ message: startMode === 'Date' ? String(start).substring(0, 10) : String(start).replace('T', ' ').substring(0, 16), plain: true });
                }

                // Time window — End
                const endMode     = this.getFieldValue('constraints', 'end_mode', 'time_window');
                const end         = this.getFieldValue('constraints', 'end', 'time_window');
                const afterNights = this.getFieldValue('constraints', 'end_after_nights', 'time_window');
                if (endMode && endMode !== 'Anytime') {
                    items.push({ message: 'End', bold: true });
                    if (endMode === 'After' && afterNights != null)
                        items.push({ message: `After ${afterNights} nights`, plain: true });
                    else if (end)
                        items.push({ message: endMode === 'Date' ? String(end).substring(0, 10) : String(end).replace('T', ' ').substring(0, 16), plain: true });
                }

                // Comma after each plain item that is followed by a bold item
                for (let i = 0; i < items.length - 1; i++) {
                    if (items[i].plain && items[i + 1] && items[i + 1].bold)
                        items[i] = { ...items[i], message: items[i].message + ',' };
                }

                return items.length ? items : [{ message: 'Default' }];
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
