
/**
 * Render a collapsible JSON tree into element `el` for object `obj`.
 * Called from the template via x-init="renderJsonTree($el, p)".
 */
function renderJsonTree(el, obj) {
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
}

function _createTreeNode(key, value) {
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
}