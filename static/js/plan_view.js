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

                // _details / constraints: show non-null, non-empty, non-false values
                const items = [];
                for (const sf of card.fields.filter(f => !f._isSectionHeader && !f.hidden)) {
                    const val = this.getFieldValue(key, sf.name, sf._groupKey);
                    if (val !== null && val !== undefined && val !== '' && val !== false) {
                        items.push({ label: sf.label, value: val, unit: sf.unit });
                    }
                }
                return items.length ? items : [{ message: '—' }];
            },
        };
    };
})();
