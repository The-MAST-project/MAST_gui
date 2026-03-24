/**
 * formValidationMixin()
 *
 * Reusable Alpine.js mixin for metadata-driven field validation.
 * Spread into any Alpine component that provides:
 *   - getFieldValue(cardKey, fieldName, groupKey)  → current value
 *   - _getOriginalValue(cardKey, fieldName, groupKey) → initial value
 *   - cards  → [{ key, fields: [...] }]
 *   - plan   → the live data object
 *
 * Validation rules are read directly from field metadata produced by
 * extract_field_metadata_recursive() — no extra configuration needed.
 * Supported: required, min, max, minLength, maxLength, pattern, options membership, int type.
 * Extend via json_schema_extra ui: { validate: "email"|"url"|... } for named validators.
 */
function formValidationMixin() {
    return {
        fieldErrors: {},   // { "cardKey.uniqueName": "error string" | null }

        // ── internal ────────────────────────────────────────────────────────

        _fieldKey(cardKey, field) {
            return cardKey + '.' + (field._uniqueName || field.name);
        },

        _findField(cardKey, fieldName, groupKey) {
            const card = (this.cards || []).find(c => c.key === cardKey);
            if (!card) return null;
            return card.fields.find(
                f => !f._isSectionHeader && f.name === fieldName && f._groupKey === groupKey
            ) || null;
        },

        // ── core validation ─────────────────────────────────────────────────

        validateField(cardKey, field, value) {
            const key = this._fieldKey(cardKey, field);

            const isEmpty = value === null || value === undefined || value === '' ||
                (typeof value === 'number' && isNaN(value));

            if (isEmpty) {
                this.fieldErrors[key] = field.required
                    ? (field.error_message || `${field.label} is required`)
                    : null;
                return;
            }

            if (field.min !== undefined && value < field.min) {
                this.fieldErrors[key] = field.error_message || `Must be ≥ ${field.min}`; return;
            }
            if (field.max !== undefined && value > field.max) {
                this.fieldErrors[key] = field.error_message || `Must be ≤ ${field.max}`; return;
            }
            if (field.minLength !== undefined && String(value).length < field.minLength) {
                this.fieldErrors[key] = field.error_message || `Must be at least ${field.minLength} characters`; return;
            }
            if (field.maxLength !== undefined && String(value).length > field.maxLength) {
                this.fieldErrors[key] = field.error_message || `Must be at most ${field.maxLength} characters`; return;
            }
            if (field.pattern && !new RegExp(field.pattern).test(String(value))) {
                this.fieldErrors[key] = field.error_message || `Invalid format`; return;
            }
            if (field.options && field.options.length) {
                const coerced = (typeof field.options[0] === 'number' && value !== '' && value !== null) ? Number(value) : value;
                if (!field.options.includes(coerced)) {
                    this.fieldErrors[key] = field.error_message || `Invalid option`; return;
                }
            }
            if (field.type === 'int' && !Number.isInteger(Number(value))) {
                this.fieldErrors[key] = field.error_message || `Must be a whole number`; return;
            }

            // Named validators (extensible via json_schema_extra ui: { validate: "..." })
            if (field.validate) {
                const msg = formNamedValidators[field.validate]?.(value);
                if (msg) { this.fieldErrors[key] = msg; return; }
            }

            this.fieldErrors[key] = null;
        },

        // Validate a field by name/groupKey — looks up field metadata from cards
        validateByName(cardKey, fieldName, groupKey, value) {
            const field = this._findField(cardKey, fieldName, groupKey);
            if (field) this.validateField(cardKey, field, value);
        },

        // ── query helpers ───────────────────────────────────────────────────

        isFieldChanged(cardKey, field) {
            const current = this.getFieldValue(cardKey, field.name, field._groupKey);
            const original = this._getOriginalValue(cardKey, field.name, field._groupKey);
            return JSON.stringify(current) !== JSON.stringify(original);
        },

        // Returns Bootstrap border class for a field input
        fieldBorderClass(cardKey, field) {
            if (!this.isFieldChanged(cardKey, field)) return '';
            const key = this._fieldKey(cardKey, field);
            return this.fieldErrors[key] ? 'border-danger' : 'border-success';
        },

        // Returns error string for display under the field, or null
        fieldError(cardKey, field) {
            return this.fieldErrors[this._fieldKey(cardKey, field)] || null;
        },

        // True when no field has an active error AND all required fields have values
        isFormValid() {
            if (!this.plan) return false;
            if (Object.values(this.fieldErrors).some(e => e)) return false;
            for (const card of (this.cards || [])) {
                for (const field of card.fields.filter(f => !f._isSectionHeader && f.required)) {
                    const v = this.getFieldValue(card.key, field.name, field._groupKey);
                    if (v === null || v === undefined || v === '') return false;
                }
            }
            return true;
        },
    };
}

/**
 * Named validators — extend here for semantic checks that can't be expressed
 * as simple Pydantic constraints.  Return an error string or null.
 */
const formNamedValidators = {
    email:  v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Invalid email address',
    url:    v => { try { new URL(v); return null; } catch { return 'Invalid URL'; } },
};
