# netiCRM Development Guide

## Essential Rules

### Code Style
- **Indentation**: 2 spaces (all files)
- **Comparisons**: Always use strict equality (`===`)
- **PHP**: CamelCase classes, camelCase methods
- **JS**: Single quotes, semicolons required

### Class-to-File Mapping
```
CRM_Core_Transaction → /CRM/Core/Transaction.php
CRM_Contribute_BAO_Contribution → /CRM/Contribute/BAO/Contribution.php
```

### Database Lookup
- Table `civicrm_contribution_product` → XML: `/xml/schema/**/ContributionProduct.xml`
- Search SQL files: Use `*.mysql` (not `*.sql`)

### Branch Strategy
- `develop` - new features and PRs
- `master` - stable release
- `hotfix` - urgent production fixes

### Multi-language String Translation

| Context | Syntax | Parameter Format |
|---------|--------|------------------|
| **PHP** | `ts('text', [...])` | `[1 => $val, 2 => $val]` |
| **Smarty** | `{ts 1=$var}text %1{/ts}` | `1=$var 2=$var` |
| **Drupal** | `t('text', [...])` / `$this->t(...)` | `['!1' => $val]` |

```php
// PHP: use ts() with numbered placeholders
ts('Hello %1', [1 => $name]);

// Smarty: use {ts} block with parameters
{ts 1=$name}Hello %1{/ts}
{ts escape='js'}Text in JS context{/ts}

// Drupal: use t() with ! prefix placeholders
t('Hello !1', ['!1' => $name]);
```

See agent docs for detailed patterns: **php-engineer**, **frontend-engineer**, **drupal-module-developer**

## Directory Quick Reference
| Path | Purpose |
|------|---------|
| `/CRM/` | PHP core classes (BAO, DAO, Form) |
| `/api/v3/` | API endpoints |
| `/templates/` | Smarty templates (.tpl) |
| `/xml/schema/` | Database schema definitions |
| `/neticrm/` | netiCRM extensions |
| `/drupal/` | civicrm drupal module base dir|
| `/js/`, `/css/`, `/packages/jquery` | Frontend assets |

## Specialized Agents
Use these agents for detailed guidance:
- **php-engineer** - PHP, BAO/DAO, API development
- **frontend-engineer** - JS, CSS, Smarty templates
- **database-agent** - Schema, migrations, update scripts
- **drupal-module-developer** - Drupal integration
- **structor-planner** - Architecture planning
