@common/CLAUDE.md

# MAST_gui — Claude Guidance

Django web frontend. Runs on `mast-wis-control`. Submodules `MAST_common` as `./common/`.

## Running

```bash
python manage.py runserver
```

## Conventions

### HTML templates
Use 2-space indentation in all `.html` templates — never tabs.

### Modal forms
Use a Bootstrap horizontal layout: per field, a `row mb-2 align-items-center` with a `col-4` label (`fw-bold text-end`) and a `col-8` input/widget. Modal footer is Cancel (left) then the primary action (right). The modal title includes the entity name (e.g. `Edit User — username`).

### Sidebar submenus
Collapsible submenus (Safety, Manage) use Bootstrap Collapse (`data-bs-toggle="collapse"` + `data-bs-target="#…-submenu"`), **not** a custom `style.display` toggle (which flipped the arrow but never revealed the content). A small script listens to `show.bs.collapse` / `hide.bs.collapse` to swap the chevron icon and auto-opens any submenu containing the active item.
