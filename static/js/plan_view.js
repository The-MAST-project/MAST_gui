(function () {
    /**
     * planViewCards(plan, fieldMeta)
     *
     * Readonly plan card view — same card structure as the new-plan form but
     * with all inputs disabled and no validation.  Used in the plans index page
     * to replace the JSON tree inside each accordion body.
     *
     * @param {Object} plan      — the plan data object from the API
     * @param {Object} fieldMeta — field metadata from extract_field_metadata_recursive(Plan)
     */
    window.planViewCards = function (plan, fieldMeta) {
        return {
            ...planCardsMixin(),

            plan: plan || {},
            cardErrors: {},

            init() {
                this.cards = this._buildCards(fieldMeta || {});

                // Events card — built from plan.events, not from field metadata
                const rawEvents = (this.plan.events || []).slice();
                rawEvents.sort((a, b) => (a.when || '') < (b.when || '') ? -1 : 1);
                this.cards.push({
                    key: 'events',
                    label: 'Events',
                    type: 'events',
                    events: rawEvents,
                    summaryEvent: rawEvents.find(e => e.what === 'created' || e.what === 'submitted') || null,
                });

                this.cards.forEach(c => this.openCards[c.key] = false);
            },

            // Readonly overrides
            isEditable(field)               { return false; },
            cardBorderClass(key)            { return ''; },
            fieldBorderClass(cardKey, field){ return ''; },
            fieldError(cardKey, field)      { return null; },
            setFieldValue()                 {},
            openDatePicker()                {},
            setModeValue()                  {},

            // In view mode show all non-null/non-false values for details/constraints
            // (no "changed from default" concept — we don't have a baseline)
            cardSummaryItems(card) {
                const key = card.key;

                if (key === 'events') {
                    if (!card.summaryEvent) return [{ message: '—' }];
                    return [{
                        label: card.summaryEvent.what,
                        value: this._fmtWhen(card.summaryEvent.when),
                    }];
                }

                if (key === 'target') {
                    const ra = this.getFieldValue('target', 'ra_hours');
                    const dec = this.getFieldValue('target', 'dec_degrees');
                    if (ra == null || dec == null) return [{ message: 'Not set' }];

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
                        ? items.map((item, i) => i < items.length - 1 && item.message ? { ...item, message: item.message + ',' } : item)
                        : [{ message: '—' }];
                }

                // constraints: show non-null, non-empty, non-false values
                const items = [];
                for (const sf of card.fields.filter(f => !f._isSectionHeader && !f.hidden)) {
                    const val = this.getFieldValue(key, sf.name, sf._groupKey);
                    if (val !== null && val !== undefined && val !== '' && val !== false) {
                        const display = sf.widget === 'user'
                            ? (this._resolveUser(val)?.name || val)
                            : val;
                        items.push({ label: sf.label, value: display, unit: sf.unit });
                    }
                }
                return items.length ? items : [{ message: '—' }];
            },
        };
    };
})();
