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
                    summaryEvent: rawEvents.length > 0 ? rawEvents[rawEvents.length - 1] : null,
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
                    return [
                        { message: card.summaryEvent.what, bold: true },
                        { message: this._fmtWhen(card.summaryEvent.when), plain: true },
                    ];
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

                if (key === 'constraints') {
                    return this._constraintsSummaryItems();
                }

                return [{ message: '—' }];
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

                return items.length ? items : [{ message: '—' }];
            },
        };
    };
})();
