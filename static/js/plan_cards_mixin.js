/**
 * planCardsMixin()
 *
 * Shared card-building and field-reading logic used by both planNewPage (editable)
 * and planViewCards (readonly).  Spread this into an Alpine component object.
 *
 * The consuming component must supply:
 *   this.plan         — the plan data object
 *   this.openCards    — { cardKey: bool }  (can be pre-initialised to {})
 *
 * The consuming component may override:
 *   isEditable(field)               — default: true
 *   fieldBorderClass(cardKey, field)— default: ''
 *   fieldError(cardKey, field)      — default: null
 *   cardBorderClass(key)            — default: ''
 *   cardSummaryItems(card)          — default: generic summary
 *   setFieldValue(...)              — default: no-op
 *   openDatePicker(...)             — default: no-op
 *   setModeValue(...)               — default: no-op
 */
function planCardsMixin() {
    return {
        cards: [],
        openCards: {},

        _buildCards(meta) {
            const CARD_ORDER = ['target', '_details', 'spec_assignment', 'constraints'];
            const cardMap = {};

            for (const [key, entry] of Object.entries(meta)) {
                if (entry._is_group) {
                    const fields = this._flatFields(entry.fields)
                        .filter(f => !f.hidden)
                        .map(f => f.options_key ? { ...f, options: this[f.options_key] || f.options } : f);
                    cardMap[key] = {
                        key,
                        label: entry.label,
                        fields: this._insertSectionDividers(fields),
                        summaryFields: fields.filter(f => f.summary),
                    };
                }
            }
            // Collect top-level scalar fields into a Details card
            const detailsFields = [];
            for (const [key, entry] of Object.entries(meta)) {
                if (!entry._is_group && !entry.hidden) {
                    detailsFields.push({ ...entry, name: key });
                }
            }
            if (detailsFields.length) {
                cardMap['_details'] = {
                    key: '_details',
                    label: 'Details',
                    fields: this._insertSectionDividers(detailsFields),
                    summaryFields: detailsFields.filter(f => f.summary),
                };
            }
            return CARD_ORDER.filter(k => cardMap[k]).map(k => cardMap[k]);
        },

        _flatFields(fieldsObj) {
            const result = [];
            for (const [name, meta] of Object.entries(fieldsObj)) {
                if (meta._is_group) {
                    for (const [subName, subMeta] of Object.entries(meta.fields || {})) {
                        result.push({
                            ...subMeta,
                            name: subName,
                            _groupKey: name,
                            _groupLabel: meta.label,
                            _uniqueName: name + '.' + subName,
                        });
                    }
                } else {
                    result.push({ ...meta, name, _uniqueName: name });
                }
            }
            return result;
        },

        _insertSectionDividers(fields) {
            const result = [];
            let currentSection = null;
            for (const field of fields) {
                const rawSection = field.section || null;
                const sectionKey = (rawSection && typeof rawSection === 'object' ? rawSection.label : rawSection) || field._groupKey || null;
                const sectionLabel = (rawSection && typeof rawSection === 'object' ? rawSection.label : rawSection) || field._groupLabel || sectionKey;
                const sectionTooltip = (rawSection && typeof rawSection === 'object') ? (rawSection.tooltip || null) : null;
                if (sectionKey && sectionKey !== currentSection) {
                    result.push({ _isSectionHeader: true, label: sectionLabel, tooltip: sectionTooltip, name: '__section__' + sectionKey, _uniqueName: '__section__' + sectionKey });
                }
                currentSection = sectionKey;
                result.push(field);
            }
            return result;
        },

        getFieldValue(cardKey, fieldName, groupKey) {
            if (!this.plan) return null;
            const card = this.plan[cardKey];
            if (card && typeof card === 'object') {
                if (groupKey) return (card[groupKey] ?? {})[fieldName] ?? null;
                return card[fieldName] ?? null;
            }
            return this.plan[fieldName] ?? null;
        },

        resolveOptions(field) {
            return field.options || [];
        },

        toggleCard(key) {
            this.openCards[key] = !this.openCards[key];
        },

        // Defaults — override in consuming component as needed
        isEditable(field)               { return true; },
        cardBorderClass(key)            { return ''; },
        fieldBorderClass(cardKey, field){ return ''; },
        fieldError(cardKey, field)      { return null; },
        setFieldValue()                 {},
        openDatePicker()                {},
        setModeValue()                  {},

        cardSummaryItems(card) {
            const key = card.key;

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

            return card.summaryFields.map(sf => ({
                label: sf.label,
                value: this.getFieldValue(key, sf.name, sf._groupKey),
                unit: sf.unit,
            }));
        },
    };
}
